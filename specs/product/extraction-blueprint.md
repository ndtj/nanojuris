# Especificação de extração premium

Status: `accepted`
Origem migrada: `SPECS.md` e `docs/elite-extraction-blueprint.md`

## Intenção

O NanoJuris deve ser uma biblioteca open source premium para extração,
normalização e unificação de fontes públicas brasileiras de jurisprudência.
Não interpreta mérito jurídico, recomenda teses nem substitui revisão humana.

## Valor entregue

O usuário deve conseguir:

- buscar jurisprudência em fontes nacionais relevantes;
- obter dados estruturados, objetivos e auditáveis;
- reutilizar os dados em planilhas, bases, pipelines e agentes de IA.

Toda funcionalidade deve preservar fonte, URL/endpoint, query quando aplicável,
data/hora de coleta, status de acesso, limitações e versão do parser.

## Arquitetura normativa

```text
source → fetcher → parser → extractor → normalized record
                                      ↓
                              canonical model + traces
                                      ↓
                         SDK · CLI · MCP · Studio · exports
                                      ↓
                                  store/analytics
```

As camadas devem permanecer separadas:

- `providers`: contrato específico de cada fonte;
- `extraction`: bytes, HTTP, status de acesso e hash;
- `models`: contratos tipados e estáveis;
- `canonical`: equivalências sem apagar campos brutos;
- `store`: persistência auditável;
- `exports`: JSON, JSONL, CSV e Markdown;
- `mcp` e `web`: adaptadores opcionais.

## Modelos canônicos mínimos

### CanonicalDecision

Deve suportar identidade, fonte, tribunal, número, tipo, classe, assunto,
relator, órgão julgador, datas, resumo, texto integral, URL, `raw`,
`SourceTrace` e `ExtractionTrace`.

### CanonicalPrecedent

Deve suportar fonte, tribunal, tipo e número do precedente, status, questão,
tese, casos afetados/paradigma, data de atualização, `raw` e traces.

### CanonicalDocument

Deve suportar tipo, content type, título, texto, URL, SHA-256, tamanho,
`retrieved_at`, status de acesso, metadados brutos e traces.

## Status obrigatórios

`AccessStatus` deve diferenciar `public`, `partial`,
`access_control_required`, `login_required`, `secret_or_restricted`,
`not_found` e `source_unavailable`.

`ExtractionStatus` deve diferenciar `complete`, `partial`, `empty`,
`parser_contract_changed`, `unsupported_format` e `failed`.

Esses estados nunca podem ser convertidos silenciosamente em `zero_results`.

## Critérios técnicos de excelência

- modelos tipados e estáveis;
- `SourceTrace` e `ExtractionTrace` quando houver coleta ou parsing;
- fixtures públicas minimizadas e testes offline;
- testes live opt-in e bounded;
- detecção explícita de CAPTCHA, WAF, login e controle de acesso;
- documentação honesta de implementado, parcial e planejado;
- limites de timeout, retry, rate limit e concorrência;
- exportação objetiva, sem interpretação jurídica;
- cobertura e maturidade declaradas por fonte.

## Definição de provider suportado

Uma fonte só é considerada suportada quando entrega:

- dossiê técnico;
- contrato público observado;
- fixture offline representativa e minimizada;
- teste de parser e contrato canônico;
- validação live opcional quando aplicável;
- status de acesso explícito;
- traces completos;
- exemplo de uso quando a interface estiver exposta;
- classificação no catálogo de cobertura.

## Evolução

SQLite permanece como backend local inicial. Um backend servidor para uso
multiusuário exige uma mudança SDD própria, com contrato de migração,
concorrência, backup, restauração e compatibilidade.

As prioridades de providers são mantidas nos dossiês, contratos e catálogos
canônicos em `docs/providers/`, `docs/source-contracts/` e `docs/registry/`.
