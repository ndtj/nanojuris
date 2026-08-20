# 0001 — Implantação inicial do NanoJuris na OCI

Status: `proposed`
Owner: `TBD`

## Intenção

Publicar o NanoJuris Studio em uma arquitetura OCI segura, reproduzível e
operável por agentes, sem expor credenciais, sem tornar o SQLite compartilhado
e sem expor o MCP local diretamente à internet.

## Objetivos

- criar ambientes dev, staging e production separados;
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
