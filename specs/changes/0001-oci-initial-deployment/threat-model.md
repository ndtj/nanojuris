# Threat model - Implantacao inicial OCI

Mudanca: `0001-oci-initial-deployment`
Status: `pending`

## Ativos e limites de confianca

| Ativo | Classificacao | Limite | Protecao |
| --- | --- | --- | --- |
| credenciais e secrets | confidencial | GitHub/OCI | Secret Management, nunca em imagem ou log |
| store SQLite e backups | interno | runtime/Object Storage | volume privado, bucket privado e restore testado |
| resultados e provenance | publico controlado | provider/app/usuario | canonicalidade, minimizacao e auditoria |
| imagem de aplicacao | integridade | CI/Registry/runtime | scan, digest e promocao por versao |

## Ameacas e controles

| ID | Ameaca | Controle preventivo | Deteccao/evidencia | Estado |
| --- | --- | --- | --- | --- |
| TH-001 | credencial vazada no Git, imagem ou log | Secret Management e secret scan | CI, revisao e Audit | pending |
| TH-002 | endpoint administrativo exposto | LB publico minimo, rede privada e IAM | inventario de portas e smoke externo | pending |
| TH-003 | provider bloqueado virar `zero_results` | classes de falha e provenance obrigatorios | fixture/teste e log estruturado | pending |
| TH-004 | artefato nao promovido ser executado | digest, registry privado e aprovacao | evidencia de pipeline | pending |
| TH-005 | perda ou corrupcao do store | backup privado, checksum e restore periodico | relatorio de restauracao | pending |
| TH-006 | agente executar operacao irreversivel | allowlist e gate humano | log de aprovacao | pending |

## Decisao de seguranca

O primeiro release mantem o MCP local, usa menor privilegio e separa CI,
runtime e operacao. Qualquer mudanca desses limites exige novo change package.
