import app as application


def test_dashboard_sin_configuracion():
    client = application.app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"Control de accesos" in response.data


def test_health_sin_configuracion():
    if application.client is None:
        response = application.app.test_client().get("/health")
        assert response.status_code == 503
