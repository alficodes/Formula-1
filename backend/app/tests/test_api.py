from fastapi.testclient import TestClient
from app.main import app


def test_health_and_version():
    # Arrange
    client = TestClient(app)
    # Act
    health = client.get('/health'); version = client.get('/version')
    # Assert
    assert health.status_code == 200 and health.json()['status'] == 'ok'
    assert version.status_code == 200 and version.json()['version'] == '1.0.0'


def test_core_monaco_endpoints():
    # Arrange
    client = TestClient(app)
    paths = ['/api/v1/monaco/state','/api/v1/monaco/drivers','/api/v1/monaco/drivers/NOR','/api/v1/monaco/laps/31','/api/v1/monaco/positions','/api/v1/monaco/track-status','/api/v1/monaco/weather','/api/v1/monaco/pit-window','/api/v1/monaco/strategies','/api/v1/monaco/recommendation']
    # Act / Assert
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200, (path, response.text)


def test_simulate_endpoint_has_minimum_iterations():
    client = TestClient(app)
    response = client.post('/api/v1/monaco/simulate', json={'iterations':500,'rain_probability':0.8,'rain_eta_laps':2,'safety_car_active':True})
    assert response.status_code == 200
    assert response.json()['iterations'] == 500
    assert len(response.json()['strategies']) == 12


def test_websocket_envelope():
    client = TestClient(app)
    with client.websocket_connect('/ws/monaco/replay/monaco-2024') as websocket:
        event = websocket.receive_json()
        assert event['type'] == 'race_state'
        assert event['race_id'] == 'monaco-2024'
        assert event['lap'] == 31
        assert {'timestamp','payload'} <= event.keys()
