# Design — Implantação inicial OCI

## Solução escolhida

Repositório privado `nanojuris-infra` com Terraform modular, ambientes
separados e OCI Resource Manager como executor de infraestrutura. A aplicação
será construída no repositório `nanojuris`, publicada como artefato/imagem e
implantada somente após gates de CI e aprovação.

## Componentes

```text
GitHub nanojuris
  ├─ testes/build ──→ imagem/artefato
  └─ contrato de versão

GitHub nanojuris-infra
  └─ Terraform ──→ Resource Manager ──→ OCI
                                      ├─ VCN/subnets
                                      ├─ Load Balancer
                                      ├─ Compute ou Container Instance
                                      ├─ Block Volume
                                      ├─ Object Storage
                                      ├─ Vault/Secrets
                                      └─ Logging/Monitoring
```

## Decisões

- uma instância inicial evita concorrência indevida no SQLite;
- exposição pública somente no Load Balancer;
- acesso administrativo por Bastion ou canal privado;
- state Terraform fica no Resource Manager, não no Git;
- segredos ficam no OCI Secret Management;
- produção usa plan + aprovação + apply;
- o primeiro deploy deve ser reversível antes de ser considerado aceito.

## Riscos

- limites e indisponibilidade dos tribunais externos;
- crescimento do SQLite;
- custos de tráfego e execução live;
- fixtures e logs com dados pessoais;
- divergência entre imagem publicada e infraestrutura configurada.
