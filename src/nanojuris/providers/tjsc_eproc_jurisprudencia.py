"""TJSC public eproc jurisprudence provider."""

from __future__ import annotations

import re

from nanojuris.errors import ParserContractChangedError
from nanojuris.providers.eproc_jurisprudencia_federal import (
    FederalEprocJurisprudenciaProvider,
)


class TjscEprocJurisprudenciaProvider(FederalEprocJurisprudenciaProvider):
    """Provider for the public TJSC eproc jurisprudence surface."""

    name = "tjsc_eproc_jurisprudencia"
    court = "TJSC"
    display_name = "TJSC eproc Jurisprudencia"
    config_url_attr = "tjsc_eproc_jurisprudencia_url"
    id_prefix = "tjsc-eproc-jurisprudencia"
    source_label = "TJSC/eproc jurisprudence"
    origins = ("TJSC", "Primeiro Grau", "Segundo Grau")

    def _extract_document_id(self, precedent_id: str) -> str:
        """Accept TJSC's shorter numeric ``id_jurisprudencia`` values."""

        match = re.search(r"(\d{6,})$", precedent_id.strip())
        if not match:
            raise ParserContractChangedError(
                "TJSC/eproc jurisprudence id must end with numeric id_jurisprudencia"
            )
        return match.group(1)
