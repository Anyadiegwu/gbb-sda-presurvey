import pytest

from app.integrations.kml_parser import (
    KmlParseError, classify_point, infer_node_type, parse_kml,
)
from tests.conftest import KML, make_kmz


def test_classifies_a_realistic_mixed_file():
    parsed = parse_kml(make_kmz(), "x.kmz")
    by_name = {n.name: n.node_type for n in parsed.nodes}
    assert by_name == {
        "Kaduna": "POP",         # in a "Sites" folder inside a backbone file
        "FDT-01": "FDT",         # from its own name
        "FAT-01": "FAT",
        "MH 07 Wuse": "MH",      # multi-line name collapsed to one line
        "Server Room": "MH",     # no MH in the name, but it is in a "Metro MH" folder
    }
    assert [r.name for r in parsed.routes] == ["S1 Abuja - Madalla"]
    # not imported, but counted so the admin can see what was left out
    assert parsed.skipped_points == {"SPLICE": 1, "POLE": 1, "UNCLASSIFIED": 1}
    assert parsed.skipped_survey_routes == 1


def test_node_remembers_its_folder_and_drops_the_boilerplate_site_leaf():
    n = next(n for n in parse_kml(make_kmz(), "x.kmz").nodes if n.name == "Server Room")
    assert n.folder == "Backbone Test > Metro MH > Kano.kml"


def test_default_node_type_imports_unrecognised_points():
    parsed = parse_kml(KML.encode(), "x.kml", default_node_type="POP")
    assert "Customer School" in {n.name for n in parsed.nodes}
    assert parsed.skipped_points.get("UNCLASSIFIED", 0) == 0


def test_invalid_default_node_type():
    with pytest.raises(KmlParseError):
        parse_kml(KML.encode(), "x.kml", default_node_type="BANANA")


@pytest.mark.parametrize("name,folders,expected", [
    # --- names seen in the real KMZs ---
    ("MH01", [], "MH"), ("EXMH65", [], "MH"), ("ExMH04", [], "MH"), ("NMH01", [], "MH"),
    ("S2_EXMH104", [], "MH"), ("S20NMH01", [], "MH"), ("S33 Ex.MH76", [], "MH"),
    ("Ext. MH 11", [], "MH"), ("RMH 01", [], "MH"), ("HH01", [], "MH"), ("Ext HH02", [], "MH"),
    ("M12 HH2B", [], "MH"), ("MHO1", [], "MH"),           # letter-O typo for 01
    ("R7 MH-006 SP1", [], "MH"),                          # a manhole that also has a splice
    ("FDT8 (Finance)", [], "FDT"), ("FDT 7 (Women Center)", [], "FDT"), ("FAT1 (NOC)", [], "FAT"),
    ("Pole 1 SP1 Old", [], "POLE"), ("SP11", [], "SPLICE"), ("Splicing Point", [], "SPLICE"),
    ("11km AS Spl", [], "SPLICE"),
    ("Site BB Madalla", [], "POP"), ("MINNA SITE", [], "POP"), ("Kano DC", [], "POP"),
    ("GBB-NOC", [], "POP"), ("Funtua ODF", [], "POP"),
    # --- folders decide when the name doesn't ---
    ("1A", ["Phase 1 MH", "R14", "Pole", "Checklist 1A"], "POLE"),
    ("SP8", ["Phase 1 MH", "Existing SP"], "SPLICE"),
    ("Anything", ["Metro MH", "Kano.kml", "Site"], "MH"),
    ("Kaduna", ["Backbone Phase 2", "Site-Surveyed", "cities"], "POP"),
    ("Bajoga", ["Backbone Phase 2", "New Site"], "POP"),
    # --- things that must NOT become connection points ---
    ("Fatima", [], "UNCLASSIFIED"), ("Mhairi", [], "UNCLASSIFIED"),
    ("Gbagada General Hospital", ["Lagos", "Lagos.kml", "Site"], "UNCLASSIFIED"),  # "Site" outside a backbone file
    ("Central Primary School", ["Kaduna", "New sites"], "UNCLASSIFIED"),
    ("NIMC", ["Abuja", "SDH-Ring2", "FDT6", "GPONl5"], "UNCLASSIFIED"),  # customer served FROM FDT6, not an FDT
])
def test_classify_point(name, folders, expected):
    assert classify_point(name, folders) == expected


def test_infer_node_type_returns_none_for_non_nodes():
    assert infer_node_type("Pole 1", []) is None and infer_node_type("School", []) is None
    assert infer_node_type("MH01", []) == "MH"


def test_survey_routes_are_recognised():
    def routes(kml):
        p = parse_kml(kml.encode(), kml_name)
        return len(p.routes), p.skipped_survey_routes

    wrap = ('<kml xmlns="http://www.opengis.net/kml/2.2"><Document>%s</Document></kml>')
    line = '<LineString><coordinates>7,9 7.1,9</coordinates></LineString>'
    global kml_name
    kml_name = "x.kml"
    # named by its measured length -> a hand-measured pre-survey route
    assert routes(wrap % f'<Placemark><name>Route - 6998m</name>{line}</Placemark>') == (0, 1)
    assert routes(wrap % f'<Placemark><name>4671</name>{line}</Placemark>') == (0, 1)
    # backbone names use KM and are real cable
    assert routes(wrap % f'<Placemark><name>S1 Abuja - Madalla -44.186KM</name>{line}</Placemark>') == (1, 0)
    # a customer point sitting next to its drawn route
    assert routes(wrap % ('<Folder><name>Gbagada Hospital</name>'
        '<Placemark><name>Gbagada Hospital</name><Point><coordinates>7,9</coordinates></Point></Placemark>'
        f'<Placemark><name>Untitled Path</name>{line}</Placemark></Folder>')) == (0, 1)
    # a metro link with several sites is real fibre
    assert routes(wrap % ('<Folder><name>Link 3</name>' + "".join(
        f'<Placemark><name>S{i}</name><Point><coordinates>7,9</coordinates></Point></Placemark>' for i in range(4))
        + f'<Placemark><name>Untitled Path</name>{line}</Placemark></Folder>')) == (1, 0)
    # a whole file/folder called SURVEY holds pre-survey drawings
    kml_name = "GOMBE_SURVEY.kml"
    assert routes(wrap % f'<Placemark><name>Youth</name>{line}</Placemark>') == (0, 1)


def test_site_surveyed_folder_is_not_mistaken_for_a_survey_folder():
    kml = ('<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Folder><name>Site-Surveyed</name>'
           '<Placemark><name>Kaduna</name><Point><coordinates>7,9</coordinates></Point></Placemark>'
           '<Placemark><name>Route A</name><LineString><coordinates>7,9 7.1,9</coordinates></LineString>'
           '</Placemark></Folder></Document></kml>')
    p = parse_kml(kml.encode(), "Backbone.kml")
    assert [n.node_type for n in p.nodes] == ["POP"] and len(p.routes) == 1


def test_bad_coordinates_are_skipped_not_fatal():
    kml = """<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
      <Placemark><name>bad</name><Point><coordinates>999,999,0</coordinates></Point></Placemark>
      <Placemark><name>short</name><LineString><coordinates>7,9,0</coordinates></LineString></Placemark>
      <Placemark><name>MH1</name><Point><coordinates>7,9,0</coordinates></Point></Placemark>
    </Document></kml>"""
    parsed = parse_kml(kml.encode(), "x.kml")
    assert [n.name for n in parsed.nodes] == ["MH1"]
    assert len(parsed.skipped) == 2


def test_multigeometry_yields_multiple_routes():
    kml = """<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark><name>R</name>
      <MultiGeometry>
        <LineString><coordinates>7,9 7.1,9</coordinates></LineString>
        <LineString><coordinates>7,9.5 7.1,9.5</coordinates></LineString>
      </MultiGeometry></Placemark></Document></kml>"""
    assert [r.name for r in parse_kml(kml.encode(), "x.kml").routes] == ["R (part 1)", "R (part 2)"]


def test_chinese_names_survive():
    kml = """<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark><name>未命名路径</name>
      <LineString><coordinates>7,9 7.1,9</coordinates></LineString></Placemark></Document></kml>"""
    assert parse_kml(kml.encode(), "x.kml").routes[0].name == "未命名路径"


def test_rejects_garbage():
    with pytest.raises(KmlParseError):
        parse_kml(b"not xml", "x.kml")
    with pytest.raises(KmlParseError):
        parse_kml(b"not a zip", "x.kmz")
        