from __future__ import annotations

from tools.build_first_degree_workpacks import build


def test_first_degree_workpacks_cover_all_state_authorities() -> None:
    payload = build()
    assert payload["summary"]["authorities"] == 27
    assert payload["summary"]["route_candidates"] >= 0
    assert all(row["promotion_decision"] == "discovery_only" for row in payload["workpacks"])
    for row in payload["workpacks"]:
        assert not any(
            row["gates"][name]
            for name in ("degree_contract", "adapter", "fixtures", "live", "quality", "federation")
        )


def test_process_surfaces_are_not_promoted_as_jurisprudence() -> None:
    payload = build()
    for workpack in payload["workpacks"]:
        for route in workpack["routes"]:
            if route["scope"] == "process_surface":
                assert route["priority_reason"] == "process_surface_excluded"
