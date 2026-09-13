from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/build_state_appellate_program.py"
SPEC = importlib.util.spec_from_file_location("build_state_appellate_program", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_program_contains_exactly_27_unique_state_cjsg_workpacks() -> None:
    registry = MODULE._load(MODULE.DEFAULT_REGISTRY)
    program = MODULE.build_program(registry, "2026-09-05")

    authorities = [item["authority"] for item in program["workpacks"]]
    assert len(authorities) == 27
    assert len(set(authorities)) == 27
    assert all(len(item["tasks"]) == 8 for item in program["workpacks"])
    assert all(item["total_gates"] == 8 for item in program["workpacks"])


def test_program_preserves_blocked_and_missing_provider_states() -> None:
    registry = MODULE._load(MODULE.DEFAULT_REGISTRY)
    program = MODULE.build_program(registry, "2026-09-05")
    by_authority = {item["authority"]: item for item in program["workpacks"]}

    # TJSP/CJSG was revalidated by bounded live evidence and is now maintained
    # as a technically enabled surface.  Access challenges remain explicit in
    # the provider diagnostics, but are no longer the current surface state.
    assert by_authority["TJSP"]["action"] == "maintenance"
    assert by_authority["TJAP"]["action"] == "blocked_recheck"
    assert by_authority["TJMA"]["action"] == "blocked_recheck"
    assert by_authority["TJMA"]["live_status"] == "access_controlled"
    assert by_authority["TJSE"]["action"] == "maintenance"


def test_only_eight_completed_gates_counts_as_complete() -> None:
    registry = MODULE._load(MODULE.DEFAULT_REGISTRY)
    program = MODULE.build_program(registry, "2026-09-05")

    complete = [item for item in program["workpacks"] if item["completed_gates"] == 8]
    assert program["summary"]["complete_8_of_8"] == len(complete)
    assert all(item["action"] == "maintenance" for item in complete)
    assert all(all(task["status"] == "completed" for task in item["tasks"]) for item in complete)
