"""TJRJ public eproc jurisprudence provider."""

from nanojuris.providers.eproc_jurisprudencia_federal import (
    FederalEprocJurisprudenciaProvider,
)


class TjrjEprocJurisprudenciaProvider(FederalEprocJurisprudenciaProvider):
    """Provider for the public TJRJ eproc jurisprudence surface."""

    name = "tjrj_eproc_jurisprudencia"
    court = "TJRJ"
    display_name = "TJRJ eproc Jurisprudencia"
    config_url_attr = "tjrj_eproc_jurisprudencia_url"
    id_prefix = "tjrj-eproc-jurisprudencia"
    source_label = "TJRJ/eproc jurisprudence"
    origins = ("TJRJ", "Primeiro Grau", "Segundo Grau")
