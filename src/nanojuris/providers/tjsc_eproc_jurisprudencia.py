"""TJSC public eproc jurisprudence provider."""

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
