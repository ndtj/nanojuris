# SDD 0104 — TJMMG jurisprudência bounded binding

Status: `verified`  
Owner: Provider Engineering  
Data: `2026-09-10`

## Objetivo

Disponibilizar um binding opt-in para a aplicação oficial de jurisprudência do
TJMMG, com busca bounded por número exato ou janela fechada e inteiro teor
oficial sob demanda, sem transformar a limitação de paginação da fonte em
promessa de busca ampla.

## Requisitos

- **REQ-001** — consultar metadados públicos sem persistir o corpo decisório;
- **REQ-002** — enviar apenas payload bounded à rota indicada pelo frontend;
- **REQ-003** — parsear `collection` em resultados canônicos com grau, ramo,
  coleção, datas, texto e `SourceTrace`;
- **REQ-004** — obter PDF oficial por `NomeArquivo`, validar `%PDF`, MIME,
  tamanho e extração canônica;
- **REQ-005** — classificar resposta excedente, bloqueio, timeout e schema como
  estados explícitos;
- **REQ-006** — nunca tratar resposta excedente ou contrato desconhecido como
  `authoritative_empty`;
- **REQ-007** — manter o provider opt-in e fora da federação padrão enquanto a
  fonte não oferecer paginação server-side para consultas amplas.

## Critérios de aceite

- **AC-001** — fixture de metadados é lida e seus campos são redigidos;
- **AC-002** — número exato e intervalo fechado geram coleção bounded;
- **AC-003** — `collection: []` é vazio autoritativo somente em consulta bounded;
- **AC-004** — `response_too_large` gera `SourceUnavailableError`;
- **AC-005** — JSON sem envelope conhecido gera `ParserContractChangedError`;
- **AC-006** — PDF válido gera `CanonicalDocument` e arquivo inválido falha;
- **AC-007** — capabilities declaram `supports_unified_search=false` e
  `opt_in_unified_search=true`.

## Fora de escopo

Resolver CAPTCHA, repetir resposta sem limite, persistir corpus, usar credenciais
ou declarar cobertura do acervo militar.
