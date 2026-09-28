"""
Parses KML/KMZ files (as exported from Google Earth) into a flat list of
named LineString routes, ignoring styling, folders, and any Point
placemarks (cities/sites are a separate concern from route geometry).

A KMZ is just a zip file containing a doc.kml plus assets; we only need
the KML.
"""

import zipfile
from dataclasses import dataclass
from io import BytesIO
from typing import List
from xml.etree import ElementTree as ET

KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}


@dataclass
class ParsedRoute:
    name: str
    coordinates: List[tuple]  # list of (lon, lat) — matches KML's lon,lat[,alt] order


class KmlParseError(Exception):
    pass


def _extract_kml_bytes(file_bytes: bytes, filename: str) -> bytes:
    if filename.lower().endswith(".kmz"):
        with zipfile.ZipFile(BytesIO(file_bytes)) as z:
            kml_names = [n for n in z.namelist() if n.lower().endswith(".kml")]
            if not kml_names:
                raise KmlParseError("No .kml file found inside the .kmz archive")
            # doc.kml is the conventional main file; fall back to the first match
            preferred = next((n for n in kml_names if n.lower() == "doc.kml"), kml_names[0])
            return z.read(preferred)
    return file_bytes


def _all_placemarks(element) -> List[ET.Element]:
    result = list(element.findall("kml:Placemark", KML_NS))
    for folder in element.findall("kml:Folder", KML_NS):
        result.extend(_all_placemarks(folder))
    return result


def parse_routes(file_bytes: bytes, filename: str) -> List[ParsedRoute]:
    """Returns every LineString placemark in the file as a ParsedRoute.
    Point placemarks (cities/sites) are skipped — this is route geometry only."""
    kml_bytes = _extract_kml_bytes(file_bytes, filename)

    try:
        root = ET.fromstring(kml_bytes)
    except ET.ParseError as exc:
        raise KmlParseError(f"Could not parse KML: {exc}") from exc

    document = root.find("kml:Document", KML_NS)
    if document is None:
        raise KmlParseError("No <Document> element found in KML")

    routes: List[ParsedRoute] = []
    for placemark in _all_placemarks(document):
        line_string = placemark.find("kml:LineString", KML_NS)
        if line_string is None:
            continue  # not a route (likely a Point/site placemark) — skip

        name_el = placemark.find("kml:name", KML_NS)
        name = (name_el.text or "").strip() if name_el is not None else "(unnamed route)"

        coords_el = line_string.find("kml:coordinates", KML_NS)
        if coords_el is None or not coords_el.text:
            continue

        coordinates = []
        for raw in coords_el.text.split():
            parts = raw.split(",")
            if len(parts) < 2:
                continue
            lon, lat = float(parts[0]), float(parts[1])
            coordinates.append((lon, lat))

        if len(coordinates) < 2:
            continue  # not a valid line

        routes.append(ParsedRoute(name=name, coordinates=coordinates))

    return routes