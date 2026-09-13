"""Public module for the opt-in SJUR/TRE provider family.

The implementation lives with the TSE adapter because both surfaces share the
same official API contract.  This module gives the catalogued
``tre_sjur_jurisprudencia`` provider a stable, discoverable import path without
duplicating transport or parser code.
"""

from nanojuris.providers.tse_sjur_jurisprudencia import (
    TRE_AUTHORITIES,
    TRE_STATES,
    TreSjurFirstDegreeFamilyProvider,
    TreSjurFirstDegreeProvider,
    TreSjurJurisprudenciaFamilyProvider,
    TreSjurJurisprudenciaProvider,
)

__all__ = [
    "TRE_AUTHORITIES",
    "TRE_STATES",
    "TreSjurFirstDegreeFamilyProvider",
    "TreSjurFirstDegreeProvider",
    "TreSjurJurisprudenciaFamilyProvider",
    "TreSjurJurisprudenciaProvider",
]
