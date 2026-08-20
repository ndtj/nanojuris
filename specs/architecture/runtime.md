# Arquitetura de runtime

Status: `accepted`

## Estado atual

O NanoJuris é um pacote Python com providers, CLI, store SQLite opcional, MCP
local e Studio FastAPI com frontend estático empacotado.

## Implantação inicial OCI

```text
HTTPS
  ↓
OCI Load Balancer
  ↓ subnet privada
NanoJuris Studio / FastAPI
  ↓
SQLite em armazenamento persistente
  ↓ backup
OCI Object Storage
```

O MCP atual é local/stdin-stdout. Não expor o processo MCP diretamente na
internet. MCP remoto exige transporte, autenticação, autorização, rate limit e
auditoria próprios.

## Evolução planejada

1. VM ou Container Instance única para o primeiro ambiente produtivo;
2. backup e restauração verificados;
3. observabilidade e deploy automatizado;
4. workers e filas quando sincronizações justificarem;
5. migração do SQLite para banco servidor antes de múltiplas réplicas;
6. alta disponibilidade atrás de Load Balancer.

## Invariantes

- acesso de entrada somente por HTTPS;
- portas internas não são públicas;
- providers fazem tráfego de saída limitado e observável;
- secrets vêm de mecanismo de secrets;
- health e readiness não devem mascarar falhas de provider;
- rollback deve existir antes de produção.
