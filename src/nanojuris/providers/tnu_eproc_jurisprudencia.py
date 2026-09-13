"""TNU EPROC jurisprudence provider compatibility module.

The implementation lives in :mod:`eproc_jurisprudencia_federal` so the
shared family contract remains the single parser boundary.  This module gives
the registered provider a stable, discoverable import path without duplicating
the implementation.
"""

from nanojuris.providers.eproc_jurisprudencia_federal import TnuEprocJurisprudenciaProvider

__all__ = ["TnuEprocJurisprudenciaProvider"]
