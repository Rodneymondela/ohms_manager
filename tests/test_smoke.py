def test_health(client):
    rv = client.get('/health')
    assert rv.status_code == 200
    assert rv.get_json().get('status') == 'ok'

def test_root_index(client):
    rv = client.get('/')
    assert rv.status_code == 200
