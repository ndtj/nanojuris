# Threat model — inteiro teor

Status: pending

| ID | Ameaça | Impacto | Controle |
| --- | --- | --- | --- |
| TH-001 | arquivo malicioso | alto | nunca executar; parser isolado |
| TH-002 | zip/decompression bomb | alto | limites antes e durante parse |
| TH-003 | redirect para host hostil | alto | allowlist |
| TH-004 | path traversal | alto | nomes internos e diretório controlado |
| TH-005 | OCR/tempfile vazando dados | alto | arquivo imprevisível e limpeza |
| TH-006 | cache sem limite | médio | quota, TTL e content addressing |
| TH-007 | redistribuição indevida | alto | decisão por fonte |

Riscos residuais exigem revisão Security/Privacy por provider documental.
