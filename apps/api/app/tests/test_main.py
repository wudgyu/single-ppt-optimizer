from app.main import app, health


def test_health_endpoint_returns_ok() -> None:
    assert health() == {"status": "ok"}


def test_application_has_health_route() -> None:
    assert app.title == "PPT Single-Slide Optimizer API"
