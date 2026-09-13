"""TJMS CJPG (first-instance) public jurisprudence provider.

TJMS publishes a public e-SAJ ``/cjpg/`` search form with inline decision
text.  The binding reuses the hardened e-SAJ parser used by TJSP while keeping
the authority, source identity and configurable host distinct.
"""

from __future__ import annotations

from dataclasses import replace
from urllib.parse import urlsplit

import requests

from nanojuris.config import NanoJurisConfig
from nanojuris.models import ProviderCapabilities
from nanojuris.providers.tjsp_cjpg import TjspCjpgProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy


class TjmsCjpgProvider(TjspCjpgProvider):
    """Provider for TJMS public first-instance (CJPG) decisions."""

    name = "tjms_cjpg"
    authority = "TJMS"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        # The shared e-SAJ parser is safe to reuse, but the transport allowlist
        # must be rebound to TJMS.  Calling the parent constructor alone would
        # leave the TJSP host in the policy and reject the official TJMS URL
        # before the request was sent.
        super().__init__(config=config, session=session)
        host = urlsplit(self.config.tjms_cjpg_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=8_000_000,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )

    @property
    def base_url(self) -> str:
        return self.config.tjms_cjpg_url.rstrip("/")

    def get_capabilities(self) -> ProviderCapabilities:
        """Return the shared e-SAJ contract with TJMS-specific identity."""

        return replace(
            super().get_capabilities(),
            source=self.name,
            display_name="TJMS CJPG Jurisprudencia (1o grau)",
            source_url=self.base_url,
        )


__all__ = ["TjmsCjpgProvider"]
