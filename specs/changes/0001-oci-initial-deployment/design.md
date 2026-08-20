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

## Decomposicao e limites da decisao

O change e um envelope de programa, nao uma tarefa unica de implementacao.
`spec-of-specs.md` divide a entrega em pacotes menores. A escolha final entre
Compute e Container Instance permanece uma decisao de implementacao apos a
clarificacao de custo, observabilidade, persistencia e operacao.

O modelo arquitetural deve manter, no minimo, uma visao de contexto, containers
e implantacao; os nomes e fluxos precisam ser consistentes com
`specs/architecture/runtime.md`.

## Riscos

- limites e indisponibilidade dos tribunais externos;
- crescimento do SQLite;
- custos de tráfego e execução live;
- fixtures e logs com dados pessoais;
- divergência entre imagem publicada e infraestrutura configurada.
