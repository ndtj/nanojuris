"""TLS compatibility adapter for the public TJCE e-SAJ endpoint."""

from __future__ import annotations

from typing import Any

from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context


class TjceTlsAdapter(HTTPAdapter):
    """Enable TJCE's legacy cipher level without disabling TLS verification."""

    def init_poolmanager(
        self,
        connections: int,
        maxsize: int,
        block: bool = False,
        **pool_kwargs: Any,
    ) -> None:
        context = create_urllib3_context()
        context.set_ciphers("DEFAULT:@SECLEVEL=1")
        pool_kwargs["ssl_context"] = context
        super().init_poolmanager(connections, maxsize, block, **pool_kwargs)
