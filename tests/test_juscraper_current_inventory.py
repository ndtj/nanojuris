from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
INVENTORY = ROOT / "docs" / "provider-discovery" / "juscraper-court-inventory-current.json"
SEMANTIC_DIFF = ROOT / "docs" / "provider-discovery" / "juscraper-semantic-diff-current.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_current_juscraper_tjrj_maps_to_the_ejuris_surface() -> None:
    records = {item["source_id"]: item for item in _load(INVENTORY)["records"]}
    tjrj = records["tjrj"]

    assert tjrj["surface_equivalents"]["cjsg"] == "tjrj_ejuris"
    assert tjrj["nanojuris_equivalent"] == "tjrj_ejuris"
    assert tjrj["equivalent_registered"] is True
    assert "tjrj_eproc_jurisprudencia" not in tjrj["nanojuris_equivalents"]


def test_current_inventory_separates_federable_and_diagnostic_runtime_counts() -> None:
    payload = _load(INVENTORY)
    nanojuris = payload["nanojuris"]
    assert nanojuris["runtime_provider_count"] == (
        nanojuris["federated_runtime_provider_count"]
        + nanojuris["diagnostic_runtime_provider_count"]
    )
    # The TRE first-degree family is now a normal, explicit-authority runtime
    # binding.  It remains opt-in at capability level (and outside the
    # default unified federation), but the inventory's federable count tracks
    # the normal client runtime, not the capability rollout decision.
    assert nanojuris["federated_runtime_provider_count"] == 78
    assert nanojuris["diagnostic_runtime_provider_count"] == 60
    assert len(nanojuris["diagnostic_runtime_providers"]) == 60


def test_current_juscraper_semantic_diff_keeps_tjrj_cjsg_on_ejuris() -> None:
    rows = _load(SEMANTIC_DIFF)["records"]
    tjrj = [row for row in rows if row["source_id"] == "tjrj" and row["surface"] == "cjsg"]

    assert len(tjrj) == 1
    assert tjrj[0]["nanojuris"]["provider"] == "tjrj_ejuris"
    assert tjrj[0]["status"] == "covered_requires_differential_fixture"


def test_tjrj_crosswalk_routes_match_the_independent_adapter_contract() -> None:
    upstream = (
        ROOT
        / ".tmp"
        / "juscraper-audit-20260901-correct"
        / "src"
        / "juscraper"
        / "courts"
        / "tjrj"
        / "client.py"
    ).read_text(encoding="utf-8")
    local = (ROOT / "src" / "nanojuris" / "providers" / "tjrj_ejuris.py").read_text(
        encoding="utf-8"
    )

    assert "https://www3.tjrj.jus.br/ejuris/ConsultarJurisprudencia.aspx" in upstream
    assert 'FORM_PATH = "/ejuris/ConsultarJurisprudencia.aspx"' in local
    assert (
        'RESULT_PATH = "/EJURIS/ProcessarConsJurisES.aspx/ExecutarConsultarJurisprudencia"' in local
    )
