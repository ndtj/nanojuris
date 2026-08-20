# 0001 — Implantação inicial do NanoJuris na OCI

Status: `proposed`
Owner: `TBD`

## Intenção

Publicar o NanoJuris Studio em uma arquitetura OCI segura, reproduzível e
operável por agentes, sem expor credenciais, sem tornar o SQLite compartilhado
e sem expor o MCP local diretamente à internet.

## Objetivos

- criar ambientes dev, staging e production separados;
- `REQ-001` - ambientes dev, staging e production devem ser isolados e
  reproduziveis por infraestrutura declarativa;
- `REQ-002` - o trafego publico deve terminar em HTTPS e a aplicacao deve
  expor health/readiness sem mascarar falhas de provider;
- `REQ-003` - segredos, identidade de runtime, logs e artefatos devem impedir
  exposicao acidental de credenciais ou dados pessoais;
- `REQ-004` - deploy, rollback, backup e restauracao devem possuir evidencia
  reproduzivel antes do aceite de producao;
- `REQ-005` - cada falha de provider deve manter diagnostico, provenance e
  completeness, sem ser convertida silenciosamente em resultado vazio;
- `REQ-006` - a operacao deve ter SLIs/SLOs, alertas, auditoria e runbooks
  suficientes para responder a incidentes.

## Acceptance criteria IDs

- `AC-001` - ambiente criado por Terraform/Resource Manager sem configuracao manual oculta;
- `AC-002` - somente HTTPS e publico e portas internas nao sao expostas;
- `AC-003` - `/api/health` responde com versao e estado sem ocultar falhas;
- `AC-004` - segredos nao aparecem em Git, logs, imagem ou saidas de CI;
- `AC-005` - deploy volta a ultima versao aprovada e a operacao e registrada;
- `AC-006` - backup e restauracao do store foram demonstrados;
- `AC-007` - busca offline e live bounded distinguem vazio, bloqueio, timeout e mudanca de fonte;
- `AC-008` - SLOs, alertas, auditoria e runbooks estao publicados;
- `AC-009` - producao exige aprovacao humana registrada;
- `AC-010` - escala horizontal possui plano de migracao antes de abandonar o SQLite inicial.

## Entregas principais
- provisionar infraestrutura por Terraform/OCI Resource Manager;
- executar build e deploy por pipeline;
- disponibilizar HTTPS, health check, logs, métricas e rollback;
- preservar backups do store e permitir restauração testada;
- registrar todas as decisões e aprovações.

## Fora de escopo inicial

- múltiplas réplicas usando SQLite compartilhado;
- migração imediata para banco relacional;
- MCP público sem contrato de segurança próprio;
- execução automática de operações destrutivas;
- ingestão ilimitada ou bypass de controles dos tribunais.

## Critérios de aceite

- [ ] ambiente pode ser criado a partir do Terraform sem configuração manual oculta;
- [ ] somente HTTPS é público;
- [ ] `/api/health` responde com versão e estado da aplicação;
- [ ] falha de provider é observável e não vira resultado vazio;
- [ ] segredos não aparecem em Git, logs ou imagem;
- [ ] deploy pode voltar à última versão aprovada;
- [ ] backup e restauração do store foram demonstrados;
- [ ] plano de migração antes de qualquer escala horizontal;
- [ ] produção exige aprovação humana registrada.
