# Rastreabilidade

| Requisito | Design | Código | Teste | Artefato |
| --- | --- | --- | --- | --- |
| RF-001 | coleta HTTP | `discovery/http.py` | `test_http_*` | `research.md` |
| RF-002 | candidatos | `discovery/extract.py` | `test_extract_*` | `spec.md` |
| RF-003 | browser | `discovery/browser.py` | `test_browser_*` | `design.md` |
| RF-004 | política | `discovery/policy.py` | `test_policy_*` | `threat-model.md` |
| RF-005 | classificação | `discovery/models.py` | `test_status_*` | `verification.md` |
| RF-006 | seletores | `discovery/extract.py` | `test_selector_*` | `spec.md` |
| RF-007 | drafts | `discovery/draft.py` | `test_draft_*` | `tasks.md` |
| RF-008 | replay | `discovery/replay.py` | `test_replay_*` | `verification.md` |
| RF-010 | AC-012 | T10 | `test_mcp_*`, CLI smoke | `docs/provider-discovery.md` |
