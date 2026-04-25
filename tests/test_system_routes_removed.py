from app.bootstrap import create_app


def test_health_route_is_not_registered() -> None:
    app = create_app()
    route_paths = {getattr(route, "path", None) for route in app.router.routes}

    assert "/health" not in route_paths


def test_secure_ping_route_is_not_registered() -> None:
    app = create_app()
    route_paths = {getattr(route, "path", None) for route in app.router.routes}

    assert "/secure/ping" not in route_paths
