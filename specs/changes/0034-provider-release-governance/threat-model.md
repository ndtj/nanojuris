# Threat model — release de providers

Status: pending

| ID | Ameaça | Impacto | Controle |
| --- | --- | --- | --- |
| TH-001 | artefato adulterado | alto | hash, provenance e assinatura |
| TH-002 | dependência vulnerável | alto | SBOM e audit |
| TH-003 | provider instável vira default | alto | opt-in/shadow |
| TH-004 | rollback incompleto | alto | rehearsal e versão anterior |
| TH-005 | secret em pacote | alto | secret scan |
| TH-006 | release sem aprovação | alto | environment gate humano |
| TH-007 | docs exageram cobertura | alto | claims derivados e datados |

Publicação permanece ação release e exige autorização explícita.
