"""
Parses KML/KMZ files (as exported from Google Earth) into:

- routes: LineString placemarks that are real fibre cable paths,
- nodes:  Point placemarks that are network connection points
          (MH manholes/handholes, FDT, FAT, POP/site).

Real-world KMZs mix several kinds of content in one file, so every placemark
is classified instead of imported blindly:

  points  -> MH | FDT | FAT | POP            imported as network nodes
             POLE | SPLICE | UNCLASSIFIED    NOT imported (poles, splice points,
                                             and customer sites from earlier
                                             pre-surveys)
  lines   -> route                           imported as fibre routes
             survey                          NOT imported (a hand-drawn
                                             customer-to-MH pre-survey route)

How a point is classified: its own name wins, then the folders it sits in
(deepest folder first; folders can only say MH, pole or splice, never FDT/FAT). Tag matching ignores XML namespaces, so KML 2.0/2.1/2.2
all parse the same way. Everything skipped is reported back per folder so the
admin can see exactly what was and wasn't taken.
"""

import math
import re
import zipfile
from collections import Counter, OrderedDict
from dataclasses import dataclass, field
from io import BytesIO
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

# Node types that get imported as connection points.
NODE_TYPES = ("MH", "FDT", "FAT", "POP")
# Point categories that are recognised but deliberately not imported.
SKIPPED_POINT_CATEGORIES = ("POLE", "SPLICE", "UNCLASSIFIED")

_I = re.I
# (?<![A-Za-z]) = token must not be glued to a preceding letter ("Fatima" is not FAT).
_FDT = re.compile(r"(?<![A-Za-z])FDTs?(?![A-Za-z])", _I)
_FAT = re.compile(r"(?<![A-Za-z])FATs?(?![A-Za-z])", _I)
_POLE = re.compile(r"(?<![A-Za-z])poles?(?![A-Za-z])", _I)
# MH / HH (manhole / handhole), tolerating the prefixes seen in real files:
# EXMH65, ExMH04, NMH01, RMH 01, S2_EXMH104, S33 Ex.MH76, "MHO1" (letter-O typo for 01).
_MH = re.compile(
    r"(?<![A-Za-z])(?:EXT?|NEW|NW|N|R)?[ ._\-]*(?:MH|HH)(?![A-Za-z]{2})|manholes?|handholes?",
    _I,
)
_SPLICE = re.compile(r"(?<![A-Za-z])SP\d*(?![A-Za-z])|splic|(?<![A-Za-z])Spl(?![A-Za-z])", _I)
# Backbone sites / POPs named by what they are.
_POP_NAME = re.compile(
    r"(?<![A-Za-z])(?:site|POP|NOC|ODF|DC)(?![A-Za-z])|data ?cent(?:er|re)", _I
)
# Folders that hold POP/site pins (matched against the WHOLE folder name).
_POP_FOLDER = re.compile(r"^(?:cities|site-surveyed|pops?)$", _I)
# "Site" / "New site" folders are only POPs inside a *backbone* file. Elsewhere
# (Google Earth's default leaf folder "Site" under every per-project .kml) they
# hold customer sites -- schools, hospitals, roundabouts -- not connection points.
_POP_FOLDER_IN_BACKBONE = re.compile(r"^(?:sites?|new sites?)$", _I)
_BACKBONE = re.compile(r"backbone", _I)
# A file or folder called "...SURVEY" holds pre-survey drawings, not cable.
# (Whole word only: "Site-Surveyed" is a normal folder and must not match.)
_SURVEY_WORD = re.compile(r"(?<![A-Za-z])survey(?![A-Za-z])", _I)

# A line whose name is just a length ("6998m", "Route - 6998m", "4671") is a
# hand-measured pre-survey route, not backbone cable. (Backbone names use KM.)
_SURVEY_NAME = re.compile(r"^\d+$|(?<![\d.])\d+(?:\.\d+)?\s*m\b", _I)


@dataclass
class ParsedRoute:
    name: str
    coordinates: List[Tuple[float, float]]  # (lon, lat) -- matches KML's lon,lat[,alt] order
    folder: str = ""


@dataclass
class ParsedNode:
    name: str
    longitude: float
    latitude: float
    node_type: str  # one of NODE_TYPES
    folder: str = ""


@dataclass
class ParsedKml:
    routes: List[ParsedRoute] = field(default_factory=list)
    nodes: List[ParsedNode] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)  # invalid placemarks (bad coordinates)
    skipped_points: Dict[str, int] = field(default_factory=dict)  # POLE/SPLICE/UNCLASSIFIED -> count
    skipped_survey_routes: int = 0
    folders: List[dict] = field(default_factory=list)  # per-folder breakdown for the admin


class KmlParseError(Exception):
    pass


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(element, name: str) -> Optional[str]:
    for c in element:
        if _local(c.tag) == name:
            return c.text
    return None


def _clean(text: Optional[str], fallback: str) -> str:
    # Google Earth names often contain stray newlines/double spaces
    # ("S3 Minna - Bida\n- 93.602KM"); collapse them to single spaces.
    cleaned = " ".join((text or "").split())
    return cleaned or fallback


def _extract_kml_bytes(file_bytes: bytes, filename: str) -> bytes:
    if filename.lower().endswith(".kmz"):
        try:
            with zipfile.ZipFile(BytesIO(file_bytes)) as z:
                kml_names = [n for n in z.namelist() if n.lower().endswith(".kml")]
                if not kml_names:
                    raise KmlParseError("No .kml file found inside the .kmz archive")
                preferred = next((n for n in kml_names if n.lower().endswith("doc.kml")), kml_names[0])
                return z.read(preferred)
        except zipfile.BadZipFile as exc:
            raise KmlParseError("File is not a valid .kmz (zip) archive") from exc
    return file_bytes


def _parse_coordinates(raw: Optional[str]) -> List[Tuple[float, float]]:
    """Parses a KML <coordinates> string into [(lon, lat), ...], dropping
    malformed or out-of-range tuples."""
    result: List[Tuple[float, float]] = []
    for token in (raw or "").split():
        parts = token.split(",")
        if len(parts) < 2:
            continue
        try:
            lon, lat = float(parts[0]), float(parts[1])
        except ValueError:
            continue
        if not (math.isfinite(lon) and math.isfinite(lat)):
            continue
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            continue
        result.append((lon, lat))
    return result


def _token_category(text: str) -> Optional[str]:
    """Which kind of point does this piece of text (a name or a folder name)
    describe? Order matters: more specific / more decisive first, so e.g.
    'R7 MH-006 SP1' is an MH (with a splice) and 'Pole 1 SP1' is a pole."""
    if _FDT.search(text):
        return "FDT"
    if _FAT.search(text):
        return "FAT"
    if _POLE.search(text):
        return "POLE"
    if _MH.search(text):
        return "MH"
    if _SPLICE.search(text):
        return "SPLICE"
    return None


def classify_point(name: str, folders: List[str]) -> str:
    """Returns MH | FDT | FAT | POP | POLE | SPLICE | UNCLASSIFIED."""
    # 1) The point's own name.
    category = _token_category(name)
    if category:
        return category
    if _POP_NAME.search(name):
        return "POP"
    # 2) The folders it sits in, deepest first. Only MH / pole / splice are
    #    taken from folders (manhole lists use arbitrary point names). FDT and
    #    FAT never are: a folder called "FDT6" holds the customers served FROM
    #    that FDT, not FDTs.
    for folder in reversed(folders):
        category = _token_category(folder)
        if category in ("MH", "POLE", "SPLICE"):
            return category
    # 3) POP-style folders ("cities", "Site", "New sites"...) -- checked only
    #    after the above, because "Site" is also the boilerplate leaf folder
    #    Google Earth creates under every imported file ("Gombe.kml > Site"),
    #    which can hold manholes.
    if any(_POP_FOLDER.match(f) for f in folders):
        return "POP"
    if any(_BACKBONE.search(f) for f in folders) and any(
        _POP_FOLDER_IN_BACKBONE.match(f) for f in folders
    ):
        return "POP"
    return "UNCLASSIFIED"


def infer_node_type(name: str, folders: List[str]) -> Optional[str]:
    """Importable node type (MH/FDT/FAT/POP) for a point, or None if it's
    something that isn't imported (pole, splice, customer site...)."""
    category = classify_point(name, folders)
    return category if category in NODE_TYPES else None


def _folder_label(folders: List[str]) -> str:
    """Readable folder path for reports and for telling apart nodes that share
    a name (there are hundreds of "MH01"). Drops Google Earth's boilerplate
    leaf folder 'Site'."""
    parts = [f for f in folders if f]
    if parts and parts[-1].lower() == "site":
        parts = parts[:-1]
    return " > ".join(parts)


def _walk(element, folders: List[str], placemarks: list) -> None:
    for child in element:
        tag = _local(child.tag)
        if tag in ("Folder", "Document"):
            folder_name = _clean(_child_text(child, "name"), "")
            _walk(child, folders + ([folder_name] if folder_name else []), placemarks)
        elif tag == "Placemark":
            placemarks.append((folders, child))


def parse_kml(
    file_bytes: bytes, filename: str, default_node_type: Optional[str] = None
) -> ParsedKml:
    """Parses and classifies every placemark in a KML/KMZ file.

    default_node_type: if given (MH/FDT/FAT/POP), points that can't be
    classified are imported as that type instead of being skipped. Leave it
    None (recommended) so customer sites from earlier pre-surveys don't become
    connection points.
    """
    if default_node_type is not None and default_node_type not in NODE_TYPES:
        raise KmlParseError(f"default_node_type must be one of {', '.join(NODE_TYPES)}")

    kml_bytes = _extract_kml_bytes(file_bytes, filename)
    try:
        root = ET.fromstring(kml_bytes)
    except ET.ParseError as exc:
        raise KmlParseError(f"Could not parse KML: {exc}") from exc

    start = root if _local(root.tag) == "Document" else next(
        (c for c in root if _local(c.tag) == "Document"), root
    )

    placemarks: list = []
    _walk(start, [], placemarks)

    # Pass 1: classify every point (lines need to know what points share their folder).
    classified_points = []  # (folders, name, lon, lat, category)
    out = ParsedKml()
    points_in_folder: Dict[tuple, List[str]] = {}
    for folders, pm in placemarks:
        name = _clean(_child_text(pm, "name"), "(unnamed)")
        for point in (e for e in pm.iter() if _local(e.tag) == "Point"):
            coords_el = next((c for c in point if _local(c.tag) == "coordinates"), None)
            coords = _parse_coordinates(coords_el.text if coords_el is not None else None)
            if not coords:
                out.skipped.append(f"Point '{name}' has no valid coordinates")
                continue
            lon, lat = coords[0]
            category = classify_point(name, folders)
            if category == "UNCLASSIFIED" and default_node_type:
                category = default_node_type
            classified_points.append((folders, name, lon, lat, category))
            points_in_folder.setdefault(tuple(folders), []).append(category)

    # Pass 2: classify lines.
    folder_counts: "OrderedDict[str, Counter]" = OrderedDict()

    def bump(folders: List[str], key: str) -> None:
        folder_counts.setdefault(_folder_label(folders) or "(top level)", Counter())[key] += 1

    skipped_points: Counter = Counter()
    for folders, name, lon, lat, category in classified_points:
        bump(folders, category)
        if category in NODE_TYPES:
            out.nodes.append(
                ParsedNode(name=name, longitude=lon, latitude=lat, node_type=category,
                           folder=_folder_label(folders))
            )
        else:
            skipped_points[category] += 1

    for folders, pm in placemarks:
        name = _clean(_child_text(pm, "name"), "(unnamed)")
        lines = [e for e in pm.iter() if _local(e.tag) == "LineString"]
        for index, line in enumerate(lines, start=1):
            coords_el = next((c for c in line if _local(c.tag) == "coordinates"), None)
            coords = _parse_coordinates(coords_el.text if coords_el is not None else None)
            if len(coords) < 2:
                out.skipped.append(f"Route '{name}' has fewer than 2 valid coordinates")
                continue

            # A pre-survey route: its folder holds only a customer site
            # (1-2 unclassified points) next to the hand-drawn line, or the
            # name is just a measured length.
            sibling_points = points_in_folder.get(tuple(folders), [])
            customer_pair = 0 < len(sibling_points) <= 2 and all(
                c == "UNCLASSIFIED" for c in sibling_points
            )
            in_survey_file = _SURVEY_WORD.search(filename) or any(
                _SURVEY_WORD.search(f) for f in folders
            )
            if customer_pair or in_survey_file or _SURVEY_NAME.search(name):
                bump(folders, "survey route (skipped)")
                out.skipped_survey_routes += 1
                continue

            route_name = name if len(lines) == 1 else f"{name} (part {index})"
            out.routes.append(
                ParsedRoute(name=route_name, coordinates=coords, folder=_folder_label(folders))
            )
            bump(folders, "route")

    out.skipped_points = dict(skipped_points)
    out.folders = [{"folder": f, "counts": dict(c)} for f, c in folder_counts.items()]
    return out


def parse_routes(file_bytes: bytes, filename: str) -> List[ParsedRoute]:
    """Routes only (kept for backwards compatibility)."""
    return parse_kml(file_bytes, filename).routes
    