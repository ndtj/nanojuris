# 0070 — convergência ouro de filtros, dados e inteiro teor

ID: `0070-provider-capability-gold-convergence`
Status: `proposed`
Owner: Provider Engineering, Data Engineering, Data Quality e Security
Data: `2026-09-06`

## Problema e intenção

O NanoJuris aceita um vocabulário canônico amplo, mas o suporte efetivo varia
por provider e ainda existem muitas combinações `provider + filtro` sem prova.
O catálogo, o scorecard, o discovery e a saúde live também utilizam fotografias
e critérios diferentes. Em documentos, uma declaração genérica de inteiro
teor não prova que o conteúdo possa ser localizado, obtido e extraído.

Esta mudança cria um programa executável para descobrir e implementar tudo que
cada fonte oficial pública oferece, preservar os dados que não pertencem ao
modelo comum e certificar qualidade ouro por evidência.

## Objetivos

- inventariar todos os filtros, valores, ordenações e modos de pesquisa;
- inventariar todos os campos de resultado, detalhe, catálogo e documento;
- implementar cada capacidade pública suportada no adapter correspondente;
- obter e vincular inteiro teor sempre que a fonte o disponibilizar
  legitimamente;
- tornar `unverified` temporário e eliminá-lo dos providers certificados;
- impedir filtros silenciosamente ignorados e falsos resultados vazios;
- unificar os critérios de ouro sem misturar maturidade e saúde live;
- gerar workpacks e métricas automaticamente para todas as fontes.

## Fora de escopo

- inventar filtros ou documentos ausentes na fonte;
- consulta processual, andamentos, partes e comunicações do NanoJud;
- bypass de CAPTCHA, WAF, login, TLS ou rate limit;
- coleta histórica massiva durante discovery;
- OCR de CAPTCHA ou desafio de acesso;
- commit, push, publicação, release, deploy ou alteração de produção.

## Requisitos

- **REQ-001:** deve existir um ledger canônico versionado por
  `source + surface + endpoint` com estado, evidência e data de cada capacidade.
- **REQ-002:** cada filtro oficial observado deve registrar nome canônico,
  parâmetro nativo, tipo, valores, validação, escopo pesquisado e semântica.
- **REQ-003:** cada filtro deve terminar como `native`, `translated`,
  `local_postfilter`, `validated_scope`, `unsupported_by_source`, `access_blocked` ou
  `source_unavailable`; capacidades fora da fronteira do produto terminam como
  `out_of_scope_nanojud`; `unverified` bloqueia ouro.
- **REQ-004:** `local_postfilter` só é válido se os dados necessários estiverem
  completos na janela coletada e a incompletude global for preservada.
- **REQ-005:** cada campo oficial observado deve ser classificado como
  canônico, `raw_preserved` ou `intentionally_ignored` com justificativa.
- **REQ-006:** o mapa de campos deve registrar tipo, nulabilidade, enumeração,
  transformação, origem, sensibilidade e provenance.
- **REQ-007:** resultado, detalhe, catálogo e documento são superfícies
  independentes e vinculadas por identificadores explícitos.
- **REQ-008:** inteiro teor deve ser classificado como `inline_text`,
  `detail_api`, `document_link`, `public_download`, `ocr_required`,
  `not_offered_by_source`, `access_blocked` ou `source_unavailable`.
- **REQ-009:** quando houver inteiro teor público, o provider deve produzir uma
  `DocumentReference` e passar pelo pipeline seguro do SDD 0032.
- **REQ-010:** documento válido deve preservar URL final, MIME, bytes, hash,
  data, número de páginas quando aplicável, método de extração e confiança OCR.
- **REQ-011:** toda capacidade implementada deve possuir fixture sanitizada e
  teste positivo, negativo e de schema drift compatíveis com a fonte.
- **REQ-012:** filtros devem ser provados por teste diferencial; presença de um
  input no HTML/JS não é prova suficiente.
- **REQ-013:** paginação, ordenação, total e escopo do campo textual pesquisado
  devem ser comprovados separadamente.
- **REQ-014:** a busca federada deve informar por fonte filtros aplicados,
  traduzidos, pós-filtrados, omitidos e não suportados.
- **REQ-015:** filtros identificadores não suportados devem impedir a chamada
  ou produzir erro explícito; refinamentos não podem desaparecer silenciosamente.
- **REQ-016:** SDK, CLI, MCP e Studio devem expor o mesmo conjunto canônico ou
  declarar explicitamente diferenças de interface.
- **REQ-017:** ouro será avaliado em cinco eixos independentes: contrato,
  dados, documentos, operação e federação.
- **REQ-018:** `engineering_gold` exige contrato, dados e estado documental
  terminal; o selo agregado `provider_gold` exige também operação saudável e
  federação ouro quando aplicável, zero `unverified`, zero lacuna crítica e
  evidência dentro do TTL.
- **REQ-019:** fonte que não oferece um recurso pode fechar o gate somente com
  evidência de `unsupported_by_source`/`not_offered_by_source`.
- **REQ-020:** alterações na fonte, fingerprint, rota ou schema invalidam apenas
  os gates afetados e geram workpack incremental.
- **REQ-021:** o programa deve cobrir os 60 itens catalogados atuais e crescer
  automaticamente com novos providers/superfícies.
- **REQ-022:** métricas não podem confundir adapter existente, capacidade
  declarada, capacidade testada, saúde live e federação habilitada.
- **REQ-023:** discovery live deve ser bounded, rate-aware, redigido e incapaz
  de transformar bloqueio ou erro em vazio.
- **REQ-024:** código de famílias pode ser compartilhado, mas contrato,
  evidência e certificação permanecem por provider/superfície.

## Comportamentos obrigatórios

### Filtro disponível

O adapter envia o parâmetro correto, preserva a transformação aplicada e um
teste diferencial comprova efeito coerente no request ou nos resultados.

### Filtro ausente

O contrato retorna `unsupported_by_source`; a UI e a federação não o anunciam
como disponível naquela fonte.

### Campo exclusivo

O campo permanece em `raw` tipado e com provenance. Ele só entra no contrato
canônico quando sua semântica é estável e reutilizável.

### Inteiro teor disponível

A busca devolve referência documental. O download explícito valida destino,
tamanho, MIME e conteúdo e gera documento canônico vinculado à decisão.

### Inteiro teor não oferecido

O provider registra `not_offered_by_source` com evidência; não substitui o
conteúdo por ementa nem inventa link.

### Falha externa

Bloqueio, timeout, TLS, rate limit e schema drift são resultados operacionais,
nunca listas vazias.

## Critérios de aceite

- **AC-001:** um gerador produz ledger e workpack para 100% das fontes atuais.
- **AC-002:** catálogo, runtime, scorecard, discovery e live referenciam IDs e
  timestamps reconciliáveis.
- **AC-003:** nenhum provider `provider_gold` possui filtro `unverified`.
- **AC-004:** 100% dos filtros oficiais comprovados estão implementados ou têm
  estado terminal justificado.
- **AC-005:** 100% dos campos oficiais estáveis estão mapeados para canônico,
  `raw_preserved` ou `intentionally_ignored`.
- **AC-006:** todo provider possui estado documental terminal e evidence ID.
- **AC-007:** todo inteiro teor público acessível possui referência, fetch,
  parser, vínculo, fixture e testes de segurança.
- **AC-008:** filtros sem suporte não são anunciados nem ignorados silenciosamente.
- **AC-009:** paginação, ordenação, vazio e total possuem testes por superfície.
- **AC-010:** resposta federada inclui matriz de aplicação de filtros por fonte.
- **AC-011:** cada provider `provider_gold` passa os cinco eixos ouro
  aplicáveis; providers bloqueados podem manter `engineering_gold`, mas não
  recebem ouro operacional.
- **AC-012:** candidates e famílias possuem workpack e disposição terminal sem
  serem apresentados como runtime funcional prematuramente.
- **AC-013:** novos providers entram automaticamente no denominador e falham o
  gate enquanto o inventário estiver incompleto.
- **AC-014:** suíte, Ruff, format, mypy, compileall, SDD e artefatos gerados
  passam no fechamento.
- **AC-015:** relatório final separa cobertura de filtros, campos, documentos,
  operação e federação, sem um único percentual enganoso.

## Riscos

- portais dinâmicos podem esconder contratos em bundles ou chamadas de UI;
- um filtro pode existir visualmente e ser ignorado pelo backend;
- detalhe/documento pode usar identificador efêmero;
- documentos podem conter malware, compressão abusiva ou dados pessoais;
- uma abstração de família pode apagar diferenças locais;
- evidência live envelhece e não prova disponibilidade permanente.
