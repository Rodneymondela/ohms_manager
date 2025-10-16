def test_index_payload(client):
    rv = client.get("/")
    data = rv.get_json()
    assert set(data) == {"app", "message", "version", "env"}
    assert data["app"] == "OHMS Manager"
    assert data["version"] == "0.1.0"
