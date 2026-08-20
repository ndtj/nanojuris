# Especificação de produto — NanoJuris

Status: `accepted`
Versão: `1.0`

## Propósito

NanoJuris pesquisa jurisprudência pública brasileira, precedentes, decisões,
informativos, textos públicos quando disponíveis, registros canônicos,
proveniência e jurimetria.

## Limites do produto

Não incluir consulta processual, comunicações de tribunais, DJEN, DataJud,
movimentações, partes ou linhas do tempo processuais. Esses escopos pertencem
ao NanoJud.

## Capacidades

- busca por provider e busca unificada;
- normalização para modelos canônicos;
- consulta de documentos públicos quando disponíveis;
- diagnósticos de fonte e validação live limitada;
- exposição via CLI, MCP e Studio quando declarada;
- store local auditável para pesquisas e sincronizações;
- exportação com provenance e rastreabilidade.

## Requisitos de qualidade

- resultados devem distinguir sucesso, vazio, erro e controle de acesso;
- cada registro deve preservar identidade e origem;
- filtros, paginação e ordenação devem respeitar o contrato da fonte;
- toda pesquisa live deve ter timeout e limites configuráveis;
- providers bloqueados não devem ser tratados como ausência de jurisprudência;
- mudanças de parser devem possuir fixture offline e teste de contrato.

## Critérios de produto premium

- cobertura declarada por maturidade, não apenas por quantidade;
- documentação sincronizada com runtime;
- evidência histórica e live reproduzível;
- APIs e exports versionados;
- erro operacional explicável ao usuário;
- operação segura sem bypass de controles externos.

## Especificações complementares

- [Blueprint de extração premium](extraction-blueprint.md);
- [Contrato de provider](../contracts/provider-contract.md);
- [Arquitetura de runtime](../architecture/runtime.md);
- [Mudança de implantação OCI](../changes/0001-oci-initial-deployment/spec.md).
