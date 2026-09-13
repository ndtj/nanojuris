"""Contract regressions for the TJPI/JusPI adapter."""

from nanojuris.config import NanoJurisConfig
from nanojuris.providers.tjpi_juspi import TjpiJuspiProvider


def test_tjpi_capability_classifies_available_and_unavailable_filters() -> None:
    capability = TjpiJuspiProvider(NanoJurisConfig(rate_limit_interval=0)).get_capabilities()

    assert capability.filter_status("text") == "native"
    assert capability.filter_status("number") == "native"
    assert capability.filter_status("types") == "native"
    assert capability.filter_status("degree") == "translated"
    assert capability.filter_status("published_from") == "unsupported"
    assert capability.filter_status("case_class") == "unsupported"
    assert capability.filter_status("fetch_details") == "unsupported"
