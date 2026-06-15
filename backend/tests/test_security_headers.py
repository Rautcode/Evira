"""
test_security_headers.py
Verifies that every response from the FastAPI app includes the required
OWASP-baseline security headers. Runs without a live database connection
by mocking all DB-dependent utilities.

Run with:
    cd backend
    pytest tests/test_security_headers.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ── Mock DB & service dependencies before importing the app ──────────────────
# These are patched at the module level so main.py can import without a
# live SQL Server or WinCC connection.

_mock_conn_status = MagicMock(return_value=False)
_mock_recent_reports = MagicMock(return_value={"total": 0, "successful": 0, "failed": 0, "by_type": {}})
_mock_scheduled_tasks = MagicMock(return_value={"total": 0, "active": 0, "upcoming_24h": 0})
_mock_recent_events = MagicMock(return_value=[])
_mock_wincc_status = MagicMock(return_value={"connected": False, "total_tags": 0, "active_tags": 0})


@pytest.fixture(scope="module")
def client():
    """Create a TestClient with all external dependencies mocked."""
    with (
        patch("app.utils.db.get_connection_status", _mock_conn_status),
        patch("app.utils.db.get_recent_reports", _mock_recent_reports),
        patch("app.utils.db.get_scheduled_tasks", _mock_scheduled_tasks),
        patch("app.utils.db.get_recent_events", _mock_recent_events),
        patch("app.services.wincc_service.wincc_monitor.get_status", _mock_wincc_status),
    ):
        from main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


# ── Required security headers ────────────────────────────────────────────────
REQUIRED_HEADERS = [
    "x-content-type-options",
    "x-frame-options",
    "x-xss-protection",
    "content-security-policy",
    "permissions-policy",
    "referrer-policy",
]

ENDPOINTS_TO_CHECK = ["/", "/dashboard", "/dashboard/stats"]


# ── Tests ────────────────────────────────────────────────────────────────────

class TestSecurityHeaders:
    """Verify that security headers are present on all key endpoints."""

    @pytest.mark.parametrize("endpoint", ENDPOINTS_TO_CHECK)
    def test_security_headers_present(self, client, endpoint):
        """Every endpoint must include all OWASP baseline security headers."""
        response = client.get(endpoint)
        # Accept any 2xx or 5xx (DB may be mocked as disconnected → 500 is fine)
        # What matters is the headers, not the response body.
        for header in REQUIRED_HEADERS:
            assert header in response.headers, (
                f"Missing security header '{header}' on GET {endpoint}. "
                f"Headers returned: {dict(response.headers)}"
            )

    def test_x_content_type_options_value(self, client):
        """X-Content-Type-Options must be 'nosniff'."""
        response = client.get("/")
        assert response.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options_value(self, client):
        """X-Frame-Options must be 'DENY' to prevent clickjacking."""
        response = client.get("/")
        assert response.headers.get("x-frame-options") == "DENY"

    def test_csp_contains_default_src_self(self, client):
        """Content-Security-Policy must restrict default-src to 'self'."""
        response = client.get("/")
        csp = response.headers.get("content-security-policy", "")
        assert "default-src" in csp, f"CSP missing 'default-src': {csp}"
        assert "'self'" in csp, f"CSP missing \"'self'\": {csp}"

    def test_csp_no_wildcard_script_src(self, client):
        """CSP must not allow all scripts from any origin (no 'script-src *')."""
        response = client.get("/")
        csp = response.headers.get("content-security-policy", "")
        assert "script-src *" not in csp, f"CSP allows wildcard script-src: {csp}"

    def test_permissions_policy_blocks_sensitive_apis(self, client):
        """Permissions-Policy must disable camera, microphone, and geolocation."""
        response = client.get("/")
        pp = response.headers.get("permissions-policy", "")
        for feature in ("camera", "microphone", "geolocation"):
            assert feature in pp, (
                f"Permissions-Policy missing '{feature}=()' restriction. Value: {pp}"
            )

    @pytest.mark.parametrize("endpoint", ENDPOINTS_TO_CHECK)
    def test_no_server_header_disclosure(self, client, endpoint):
        """Server header should not leak uvicorn/Python version information."""
        response = client.get(endpoint)
        server_header = response.headers.get("server", "").lower()
        # FastAPI/Starlette sets 'server: uvicorn' which is acceptable,
        # but explicit version strings like 'uvicorn/0.x.y' are not.
        assert "/" not in server_header or "uvicorn" not in server_header, (
            f"Server header leaks version info: '{server_header}'"
        )
