from __future__ import annotations

import pytest

from nanojuris.access import AccessPath
from nanojuris.public_access import PublicSession, extract_csrf_token


def _path() -> AccessPath:
    return AccessPath(
        provider="fixture",
        url="https://juris.example.test/search",
        allowed_hosts=("juris.example.test",),
    )


@pytest.mark.parametrize(
    "html",
    [
        '<meta name="csrf-token" content="token-meta">',
        '<input name="_token" value="token-input">',
        '<input name="authenticity_token" value="token-auth">',
    ],
)
def test_csrf_is_extracted_only_in_memory(html: str) -> None:
    assert extract_csrf_token(html).startswith("token-")
    assert extract_csrf_token("<html>no token</html>") is None


def test_public_session_requires_allowlisted_url() -> None:
    active = PublicSession.create(_path())
    try:
        with pytest.raises(ValueError):
            active.request("GET", "https://other.example.test/search")
    finally:
        active.close()


def test_public_session_has_bounded_transport_budget() -> None:
    active = PublicSession.create(_path(), max_retries=0, rate_limit_interval=0)
    try:
        assert active.transport.policy.max_retries == 0
        assert active.transport.policy.max_redirects == 3
        assert active.transport.policy.verify_ssl is True
        assert active.transport.policy.http_version == "1.1"
        assert active.transport.policy.allowed_hosts == ("juris.example.test",)
    finally:
        active.close()
