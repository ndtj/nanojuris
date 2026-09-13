# 0091 — handoff de cobertura nacional ouro

Status: `proposed`  
Owner: Provider Engineering, Data Quality, Search, Security and Release  
Escopo: planejamento e execução local segura; sem commit, push, publicação,
deploy ou alteração de produção.

## Objetivo

Fornecer a outro modelo um plano único, verificável e retomável para elevar os
providers NanoJuris à melhor cobertura pública comprovável de jurisprudência
brasileira. A cobertura deve separar primeiro grau, segundo grau, precedentes,
informativos, SJUR, eproc, portais e datasets; nunca contar consulta
processual, DataJud, metadados ou contexto como jurisprudência textual.

## Requisitos funcionais

- **REQ-001:** manter uma superfície canônica por `authority`, `branch`,
  `degree`, `instance`, `collection` e `document_scope`.
- **REQ-002:** separar `implemented`, `contract_valid`, `live_validated`,
  `quality_passed`, `federation_enabled` e `legal_pending`.
- **REQ-003:** inventariar filtros, enumerações, ordenação, paginação, campos,
  detalhe e documentos de cada fonte oficial.
- **REQ-004:** classificar cada capacidade como `native`, `translated`,
  `local_postfilter`, `validated_scope`, `unsupported_by_source`,
  `access_blocked` ou `source_unavailable`; `unverified` impede ouro.
- **REQ-005:** preservar `raw`, `SourceTrace`, fingerprint, versão do parser,
  schema e instante da consulta.
- **REQ-006:** distinguir `authoritative_empty`, `unconfirmed_empty`,
  `access_blocked`, `challenge_enforced`, `rate_limited`, `timeout`,
  `schema_invalid`, `partial` e `success_with_results`.
- **REQ-007:** validar inteiro teor por host permitido, redirect, MIME, magic
  bytes, tamanho, hash, extração e vínculo com a decisão.
- **REQ-008:** usar fixtures sanitizadas de sucesso, vazio autoritativo, erro,
  bloqueio, schema drift e segunda página quando aplicável.
- **REQ-009:** promover automaticamente somente providers que passem os oito
  gates técnicos e tenham acesso público; revisão humana continua separada.
- **REQ-010:** permitir que a busca web escolha 8–12 fontes, sem índice próprio,
  LLM, embeddings ou reranking pago, consumindo estados federados auditáveis.
- **REQ-011:** atualizar o ranking independentemente da ordem das ondas e
  congelá-lo após interação do usuário.
- **REQ-012:** registrar bloqueios externos sem repetir tentativas contra a
  mesma proteção e sem convertê-los em vazio.
- **REQ-013:** usar Juscraper apenas como referência de rotas, parâmetros,
  seletores e estratégias; implementação e fixtures NanoJuris são independentes.
- **REQ-014:** manter tarefas humanas e externas abertas até existir evidência
  ou decisão assinada; o executor não fabrica aprovação.
- **REQ-015:** produzir um handoff autossuficiente com comandos, ordem, critérios
  de parada e relatório de cada lote.

## Fora de escopo

- contornar ou enfraquecer CAPTCHA, Turnstile, WAF, login, TLS, rate limit ou
  segredo de justiça;
- solver, OCR ou automação de desafios, stealth/fingerprint spoofing, rotação de
  IP/proxy, replay de cookies/tokens ou fuzzing de endpoints privados;
- coleta massiva, pesquisa de corpus fora das janelas oferecidas pela fonte;
- migração de produção, OCI, Terraform, secrets, release ou publicação;
- declarar cobertura nacional por contagem de adapters.

## Critérios de aceite

- **AC-001:** outro modelo consegue iniciar pelo `GOAT_EXECUTOR_PROMPT.md` sem
  consultar a conversa.
- **AC-002:** manifesto e registro de superfícies apontam para os mesmos
  artefatos gerados e declaram sua data de observação.
- **AC-003:** cada provider tem um workpack com contrato, evidência, fixtures,
  documentos, qualidade, federação e próxima ação.
- **AC-004:** cada bloqueio tem URL, método, data, estado, evidência redigida e
  alternativa oficial avaliada.
- **AC-005:** nenhum erro externo é serializado como lista vazia.
- **AC-006:** cada provider promovido informa filtros aplicados, locais,
  ignorados, estado do total, páginas, latência e trace.
- **AC-007:** os artefatos passam `validate_sdd.py`, auditoria de tarefas e
  verificações de consistência antes de qualquer implementação.
- **AC-008:** o handoff declara explicitamente o que continua dependente de
  fonte externa ou decisão humana.
