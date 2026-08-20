# Spec of specs - Implantacao inicial OCI

Status: `proposed`

Este change e amplo demais para ser implementado como uma unica tarefa. A
entrega deve ser decomposta em pacotes independentes, preservando a ordem e os
gates abaixo:

| Pacote futuro | Escopo | Saida de aceite |
| --- | --- | --- |
| `0002-oci-foundation` | regiao, compartments, IAM, state e tagging | plan sem privilegio excessivo |
| `0003-oci-network-edge` | VCN, subnets, NSGs, DNS, TLS e Load Balancer | smoke publico/privado |
| `0004-oci-runtime-storage` | runtime, volume, bucket, secrets e health | restore e health comprovados |
| `0005-oci-delivery-observability` | registry, CI/CD, logs, metricas e auditoria | promocao por digest e alerta |
| `0006-oci-release-recovery` | staging, rollback, backup, restore e runbooks | exercicio de recuperacao |

Nenhum pacote filho deve importar decisoes nao resolvidas de `clarify.md` como
se fossem fatos. Cada pacote tera seus proprios `spec.md`, `design.md`,
`tasks.md`, `verification.md` e, quando aplicavel, pesquisa e threat model.
