# Threat model — identidade e deduplicação

| Ameaça | Impacto | Controle |
| --- | --- | --- |
| fundir decisões distintas | crítico | regras conservadoras e corpus de colisão |
| duplicar a mesma publicação | alto | aliases e match explicável |
| hash instável entre versões | alto | normalização versionada |
| perder provenance no merge | crítico | merge não destrutivo |
| expor PII no fingerprint | médio | campos allowlisted e hash local |
