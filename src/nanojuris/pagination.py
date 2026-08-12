"""Shared pagination and source-completeness semantics."""

from __future__ import annotations


def page_completeness(
    *,
    reported_total: int | None,
    start: int,
    returned: int,
    total_is_authoritative: bool,
) -> tuple[bool | None, str]:
    """Evaluate whether a provider response covers its reported result set.

    ``start`` is one-based when the page contains results. A missing or
    synthetic total never becomes evidence of completeness. This distinction
    is important for federated legal research, where a short response can be
    either a complete empty result or a truncated page.
    """

    if not total_is_authoritative or reported_total is None or reported_total < 0:
        return None, "A fonte nao informou um total autoritativo para a consulta."
    if reported_total == 0:
        return True, "A fonte informou total zero para a consulta."
    if returned == 0:
        return False, "A fonte informou resultados, mas a janela retornada veio vazia."
    covered_end = max(start, 1) + returned - 1
    if covered_end >= reported_total:
        return True, "A janela retornada alcanca o total informado pela fonte."
    return False, "A resposta e uma janela parcial do total informado pela fonte."
