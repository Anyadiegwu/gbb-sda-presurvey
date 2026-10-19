from tests.conftest import make_kmz


# ---- admin: import ---------------------------------------------------------
def test_import_counts_and_types(imported):
    assert imported["importedCount"] == 1
    assert imported["nodesImported"] == 5
    assert imported["nodesByType"] == {"FDT": 1, "FAT": 1, "MH": 2, "POP": 1}


def test_import_reports_what_it_left_out(imported):
    assert imported["pointsSkipped"] == {"SPLICE": 1, "POLE": 1, "UNCLASSIFIED": 1}
    assert imported["surveyRoutesSkipped"] == 1
    assert imported["duplicatesSkipped"] == 0 and imported["dryRun"] is False
    # per-folder breakdown so the admin can see how each KMZ folder was treated
    counts = {f["folder"]: f["counts"] for f in imported["folders"]}
    assert counts["Backbone Test > Metro MH > Kano.kml"] == {"MH": 2, "SPLICE": 1}
    assert counts["Backbone Test > Customer School"] == {"UNCLASSIFIED": 1, "survey route (skipped)": 1}


def test_dry_run_previews_without_saving(client, admin_headers):
    r = client.post("/admin/fiber-routes/import?dry_run=true", headers=admin_headers,
                    files={"file": ("test.kmz", make_kmz(), "x")})
    assert r.status_code == 200 and r.json()["dryRun"] is True and r.json()["nodesImported"] == 5
    assert client.get("/admin/manholes/", headers=admin_headers).json() == []
    assert client.get("/admin/fiber-routes/", headers=admin_headers).json() == []


def test_same_nodes_in_another_file_are_not_duplicated(client, admin_headers, imported):
    r = client.post("/admin/fiber-routes/import", headers=admin_headers,
                    files={"file": ("other_copy.kmz", make_kmz(), "x")})
    body = r.json()
    assert body["nodesImported"] == 0 and body["duplicatesSkipped"] == 5
    assert len(client.get("/admin/manholes/", headers=admin_headers).json()) == 5


def test_a_file_with_only_surveys_explains_why_nothing_was_imported(client, admin_headers):
    kml = ('<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark><name>Youth</name>'
           '<LineString><coordinates>7,9 7.1,9</coordinates></LineString></Placemark></Document></kml>')
    r = client.post("/admin/fiber-routes/import", headers=admin_headers,
                    files={"file": ("GOMBE_SURVEY.kml", kml.encode(), "x")})
    assert r.status_code == 400 and "pre-survey" in r.json()["detail"]


def test_import_response_keeps_the_fields_the_old_frontend_reads(imported):
    assert {"importedCount", "sourceFile"} <= imported.keys()


def test_reimport_replaces_instead_of_duplicating(client, admin_headers, imported):
    r = client.post(
        "/admin/fiber-routes/import", headers=admin_headers,
        files={"file": ("test.kmz", make_kmz(), "application/octet-stream")},
    )
    assert r.json()["replacedNodes"] == 5 and r.json()["replacedRoutes"] == 1
    assert len(client.get("/admin/manholes/", headers=admin_headers).json()) == 5
    assert len(client.get("/admin/fiber-routes/", headers=admin_headers).json()) == 1


def test_import_requires_admin(client):
    r = client.post("/admin/fiber-routes/import", files={"file": ("a.kmz", make_kmz(), "x")})
    assert r.status_code in (401, 403)


def test_import_rejects_wrong_extension(client, admin_headers):
    r = client.post("/admin/fiber-routes/import", headers=admin_headers, files={"file": ("a.txt", b"x", "text/plain")})
    assert r.status_code == 400


def test_admin_can_fix_a_node_type(client, admin_headers, imported):
    nodes = client.get("/admin/manholes/", headers=admin_headers).json()
    kaduna = next(n for n in nodes if n["name"] == "Kaduna")
    r = client.patch(f"/admin/manholes/{kaduna['id']}", headers=admin_headers, json={"nodeType": "FDT"})
    assert r.status_code == 200 and r.json()["nodeType"] == "FDT"


def test_manual_node_creation_defaults_to_manhole(client, admin_headers):
    r = client.post("/admin/manholes/", headers=admin_headers,
                    json={"name": "M1", "latitude": 9.0, "longitude": 7.4})
    assert r.json()["nodeType"] == "MH"
    r = client.post("/admin/manholes/", headers=admin_headers,
                    json={"name": "bad", "latitude": 99, "longitude": 7.4})
    assert r.status_code == 422


# ---- map data --------------------------------------------------------------
def test_geojson_has_routes_and_nodes(client, admin_headers, imported):
    gj = client.get("/admin/fiber-routes/geojson", headers=admin_headers).json()
    kinds = [f["properties"]["kind"] for f in gj["features"]]
    assert kinds.count("route") == 1 and kinds.count("node") == 5
    route = next(f for f in gj["features"] if f["properties"]["kind"] == "route")
    assert route["geometry"]["type"] == "LineString"
    only_fdt = client.get("/admin/fiber-routes/geojson?node_type=FDT", headers=admin_headers).json()
    assert [f["properties"]["nodeType"] for f in only_fdt["features"] if f["properties"]["kind"] == "node"] == ["FDT"]


def test_geojson_is_admin_only(client, imported):
    assert client.get("/admin/fiber-routes/geojson").status_code in (401, 403)


# ---- customer: nearest node + road route ------------------------------------
def test_resolve_location_returns_road_route_and_fibre_point(client, imported):
    r = client.post("/quotes/resolve-location", json={"latitude": 9.0005, "longitude": 7.4005})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["manholeName"] == "FDT-01"  # the FDT ~70 m away
    assert body["nodeType"] == "FDT"
    assert body["formattedAddress"] == "Stubbed Street, Abuja"
    assert body["routePolyline"]
    # road distance (x1.3 in the stub) is longer than the straight line
    assert body["customerToManholeMeters"] > body["straightLineMeters"] > 0
    # FDT-01 sits on the S1 line (lat 9.0): tap distance is ~0 (a few metres at most --
    # PostGIS measures to the geodesic arc, which bows slightly off a constant-latitude line)
    assert body["fiberlinePointLatitude"] == 9.0 and body["manholeToFiberlineMeters"] < 5
    assert body["totalDistanceMeters"] == body["customerToManholeMeters"] + body["manholeToFiberlineMeters"]


def test_road_distance_beats_straight_line_when_they_disagree(client, imported, monkeypatch):
    """The closest node as the crow flies isn't always closest by road
    (river, motorway...). Make the straight-line winner a long drive and check
    the road-nearest candidate wins."""
    from app.integrations import geo_provider

    def fake(origin, destinations):
        # candidate 0 is the straight-line nearest: give it a huge road distance
        return [50000.0] + [1000.0 + i for i in range(1, len(destinations))]

    monkeypatch.setattr(geo_provider, "get_distances_to_candidates", fake)
    body = client.post("/quotes/resolve-location", json={"latitude": 9.0005, "longitude": 7.4005}).json()
    assert body["manholeName"] != "FDT-01"
    assert body["customerToManholeMeters"] == 1001.0


def test_node_type_filter(client, imported):
    body = client.post("/quotes/resolve-location",
                       json={"latitude": 9.0005, "longitude": 7.4005, "nodeTypes": ["MH"]}).json()
    assert body["nodeType"] == "MH" and body["manholeName"] == "MH 07 Wuse"
    assert body["manholeFolder"] == "Backbone Test > Metro MH > Kano.kml"  # tells apart the hundreds of "MH01"s


def test_resolve_address_flow(client, imported):
    r = client.post("/quotes/resolve-address", json={"address": "anywhere"})
    assert r.status_code == 200 and r.json()["formattedAddress"] == "Stubbed address, Abuja"


def test_nearest_nodes_one_per_type(client, imported):
    r = client.post("/quotes/nearest-nodes", json={"latitude": 9.0005, "longitude": 7.4005})
    assert r.status_code == 200, r.text
    body = r.json()
    types = [n["nodeType"] for n in body["nearestByType"]]
    assert sorted(types) == ["FAT", "FDT", "MH", "POP"] and len(set(types)) == 4
    assert body["nearestByType"][0]["nodeType"] == "FDT"  # sorted nearest-first
    assert body["nearestFiberLine"]["routeName"] == "S1 Abuja - Madalla"
    assert body["nearestFiberLine"]["distanceMeters"] < 100


def test_no_nodes_configured_is_a_clean_400(client):
    r = client.post("/quotes/resolve-location", json={"latitude": 9.0, "longitude": 7.4})
    assert r.status_code == 400 and "No network nodes" in r.json()["detail"]


def test_no_fibre_routes_imported_does_not_break_the_quote(client, admin_headers):
    client.post("/admin/manholes/", headers=admin_headers, json={"name": "M1", "latitude": 9.0, "longitude": 7.4})
    body = client.post("/quotes/resolve-location", json={"latitude": 9.001, "longitude": 7.401}).json()
    assert body["manholeToFiberlineMeters"] == 0 and body["fiberlinePointLatitude"] is None


def test_invalid_coordinates_rejected(client):
    assert client.post("/quotes/resolve-location", json={"latitude": 123, "longitude": 7}).status_code == 422


def test_unreachable_nodes_give_a_clean_400(client, imported, monkeypatch):
    from app.integrations import geo_provider
    monkeypatch.setattr(geo_provider, "get_distances_to_candidates", lambda o, d: [None] * len(d))
    r = client.post("/quotes/resolve-location", json={"latitude": 9.0005, "longitude": 7.4005})
    assert r.status_code == 400 and "routable" in r.json()["detail"]


def test_routing_outage_is_a_502(client, imported, monkeypatch):
    from app.integrations import geo_provider

    def boom(o, d):
        raise geo_provider.GeoProviderError("OSRM down")

    monkeypatch.setattr(geo_provider, "get_distances_to_candidates", boom)
    assert client.post("/quotes/resolve-location", json={"latitude": 9.0, "longitude": 7.4}).status_code == 502


def test_full_customer_journey_to_priced_quote(client, imported):
    loc = client.post("/quotes/resolve-location", json={"latitude": 9.0005, "longitude": 7.4005}).json()
    q = client.post("/quotes/calculate", json={
        "totalDistanceMeters": loc["totalDistanceMeters"], "manholeId": loc["manholeId"],
        "bandwidthMbps": 100,
    })
    assert q.status_code == 200, q.text
    assert q.json()["grandTotal"] > 0
    