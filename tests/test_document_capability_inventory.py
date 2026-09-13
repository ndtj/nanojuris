from __future__ import annotations

import json
from pathlib import Path

from tools.build_document_capability_inventory import build

ROOT = Path(__file__).parents[1]


def test_document_capability_inventory_is_current_and_offline() -> None:
    payload = build()
    artifact = json.loads(
        (ROOT / "docs" / "coverage" / "document-capability-inventory.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload == artifact
    assert payload["network_access"] == "not_used"
    assert payload["summary"]["runtime"] == 80
    tjto = next(row for row in payload["providers"] if row["source_id"] == "tjto_jurisprudencia")
    assert tjto["supports_full_text"] is True
    assert "GET /documento.php?uuid=<uuid>" in tjto["document_endpoints"]
    assert tjto["pipeline_policy"]["mime_policy"] == "declared_header_plus_magic_validation"
    assert tjto["pipeline_policy"]["hash"] == "sha256"
    tjrn = next(row for row in payload["providers"] if row["source_id"] == "tjrn_jurisprudencia")
    assert tjrn["lifecycle"] == "implemented"
    assert tjrn["runtime"] is True
    assert tjrn["opt_in_runtime"] is False
