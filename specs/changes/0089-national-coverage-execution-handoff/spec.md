# 0089 — pacote de execução da cobertura nacional

Status: `proposed`  
Owner: Provider Engineering, Data Quality, Search, Security and Release

## Objetivo

Levar cada superfície pública de jurisprudência ao maior nível comprovável,
sem prometer cobertura que a fonte não oferece. “Cobertura” significa uma
combinação independente de `authority + branch + degree + instance + collection
+ document_scope`, com identidade e proveniência preservadas.

## Escopo

- descoberta e revalidação de fontes oficiais públicas;
- equivalência técnica controlada com Juscraper, sem copiar implementação;
- adapters independentes usando o transporte compartilhado;
- filtros remotos, filtros locais, paginação, ordenação e cursores;
- ementa, resumo, inteiro teor, PDF/HTML e documentos referenciados;
- normalização canônica, deduplicação conservadora e `SourceTrace`;
- estados explícitos na busca federada e na plataforma web;
- execução contínua, fixtures, auditoria e handoff.

## Fora de escopo

- consulta processual, andamento, partes, DJEN, DataJud ou timeline;
- burlar CAPTCHA, WAF, Turnstile, login, rate limit ou sigilo;
- uso de credenciais pessoais, cookies importados, tokens de terceiros ou
  endpoints privados;
- índice documental próprio, embeddings, LLM ou reranking pago por consulta;
- commit, push, tag, release, OCI, Terraform apply, secrets, IAM ou deploy;
- declarar 27/27 por existência de adapter ou HTTP 200 isolado.

## Requisitos

- **REQ-001:** a fonte única registra lifecycle, contrato, live, documento,
  qualidade, federação, legalidade, TTL e evidências separadamente.
- **REQ-002:** cada campo e filtro possui estado `native`, `translated`,
  `local`, `unsupported`, `blocked` ou `unknown`; nada é ignorado em silêncio.
- **REQ-003:** `total_zero`, `total_unknown`, `access_blocked`, `timeout`,
  `schema_invalid` e `partial` são estados distintos.
- **REQ-004:** todo resultado aceito prova autoridade, ramo, grau, coleção e
  identidade, ou é rejeitado com motivo.
- **REQ-005:** todo provider tem fixtures de sucesso, vazio autoritativo,
  parâmetro inválido, bloqueio, drift e segunda página quando aplicável.
- **REQ-006:** todo documento é validado por host, redirect, MIME, magic bytes,
  tamanho, hash e extração antes de ser associado à decisão.
- **REQ-007:** dados brutos relevantes, trace, versão do parser e momento da
  consulta permanecem disponíveis para auditoria.
- **REQ-008:** falha externa nunca é convertida em lista vazia.
- **REQ-009:** promoções automáticas exigem todos os gates técnicos e acesso
  público; revisão legal/humana permanece uma dimensão separada.
- **REQ-010:** o executor trabalha em lotes de 1–3 providers e para cada fonte
  bloqueada registra uma única evidência terminal e avança.
- **REQ-011:** a busca web pode atualizar ondas e ranquear deterministicamente,
  mas congela a ordem após interação do usuário.
- **REQ-012:** nenhum ciclo altera produção ou publica artefatos.

## Critérios de aceite

- **AC-001:** `execution-manifest.json` e os geradores apontam para as mesmas
  fontes de verdade.
- **AC-002:** cada provider catalogado possui workpack, contrato e decisão de
  execução explícita.
- **AC-003:** nenhum provider promovido possui filtro, grau ou total não
  comprovado.
- **AC-004:** todos os bloqueios têm método, URL, data, classificação e ação
  externa necessária.
- **AC-005:** os oito gates de promoção são reproduzíveis em teste ou evidência
  live bounded.
- **AC-006:** o relatório final separa cobertura catalogada, executável, live e
  federada.
- **AC-007:** o próximo modelo consegue retomar pelo `GOAT_EXECUTOR_PROMPT.md`
  sem ler o histórico da conversa.
