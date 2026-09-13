# NanoJuris — pacote de execução para continuidade

Snapshot: 2026-09-07
Escopo: cobertura nacional, paridade técnica com Juscraper, busca federada e
completude documental.
Política: trabalho local e verificável; não executar commit, push, release,
deploy, Terraform apply ou alteração em produção.

Este é um handoff operacional para outro modelo. Os SDDs, catálogos e
evidências referenciados permanecem como fonte primária; este resumo não
substitui o contrato de um provider.

## Medição adicional do ranker

Em 1.000 rodadas com 240 candidatos, o ranker CPU-only apresentou p95 de
78,125 ms de tempo de processo e zero chamadas de rede. O resultado está em
`docs/benchmarks/live-ranking-performance-20260907-cycle2.json`. O gate técnico
de desempenho passa; a calibração e o holdout de T62 ainda exigem rótulos
humanos independentes.

## 1. Estado verificado

| Dimensão | Estado | Fonte |
| --- | ---: | --- |
| Testes da biblioteca | 1531 passed, 26 skipped | python -m pytest -q |
| Testes da plataforma | 153 passed | repos/nanojuris-platform |
| SDD, Ruff, format, mypy, compileall, diff | verdes | gates locais |
| Authorities estaduais de segundo grau | 27 mapeadas | docs/coverage/state-appellate-program-20260905.json |
| Workpacks CJSG completos | 25/27 | TJAP/TJMA são blocked_recheck |
| CJPG / CJSG | 7/27 / 25/27 | docs/coverage/surface-state-registry-20260902.json |
| Superfícies | 150 mapeadas / 125 obrigatórias | registry |
| Providers | 67 catalogados / 62 runtime | certificação gerada |
| Promovíveis sem evidência nova | 0 | manifesto/certificação |
| Tarefas não marcadas | 47 no escopo deste pacote | docs/coverage/open-task-audit-20260907.json |
| Classificação das abertas | 35 externas, 12 humanas | auditoria acima |

Não declarar 27/27. HTTP 200, adapter existente, catálogo ou resposta
contextual não constituem prova de jurisprudência textual.

O provider `tjrj_banco_sentencas` foi adicionado como coleção oficial curada de
primeiro grau, opt-in. O PDF do índice respondeu HTTP 200 em 2.490.134 bytes e
259 páginas; o primeiro documento histórico observado respondeu HTTP 503 e
permanece `source_unavailable`. Evidência:
`docs/provider-discovery/tjrj-banco-sentencas-live-20260908.json`.

## 2. Leitura obrigatória

Leia, nesta ordem:

1. AGENTS.md, specs/constitution.md e specs/README.md;
2. docs/coverage/README.md;
3. SDDs 0069, 0077, 0078, 0081, 0082, 0083, 0084, 0088, 0089 e 0090 (spec, design, tasks
   e verification quando presentes);
4. docs/coverage/public-access-boundary-playbook-20260908.md e .json;
5. docs/coverage/state-appellate-program-20260905.json;
6. docs/coverage/surface-state-registry-20260902.json;
7. docs/registry/provider-catalog.full.json;
8. docs/provider-discovery/juscraper-parity-assessment-20260906.md,
   juscraper-court-inventory-20260906.json e juscraper-semantic-diff-20260906.json;
9. docs/coverage/open-task-audit-20260907.json;
10. docs/coverage/external-action-requests-20260907.md;
11. docs/operations/provider-certification-20260907.json e
    docs/operations/technical-promotion-manifest-20260905.json;
12. SDD, contrato, implementação, fixtures e testes do provider em execução.

O checkout de referência é repos/.tmp-juscraper, commit
604c1dd70d6f313011cc1079790febe6c71807e2. Use-o como referência técnica, sem
copiar código, cookies, cabeçalhos ou respostas.

O provider `trt2_ementario_jurisprudencia` foi adicionado como runtime opt-in
com contrato e fixtures de ementário oficial de segundo grau. A evidência live
`docs/provider-discovery/trt2-ementario-live-20260907.json` registra índice e
tópico válidos na primeira tentativa; respostas CloudFront 403 posteriores
permanecem `partial/access_controlled` e não foram contornadas.

## 3. Tarefas restantes

### 0069 — cobertura estadual de segundo grau

T07 (external_source): TJAP/TJMA precisam de rota oficial pública sem desafio
ou de um relatório de bloqueio terminal. As rechecagens estão em
docs/provider-discovery/legitimate-blocked-techniques-20260907.json,
tjap-official-alternatives-live-20260907.json,
tjma-official-alternatives-live-20260907.json e
tjma-public-route-inventory-live-20260907.json. Só marcar concluído com
contrato de grau, fixture, paginação/filtros e live comprovados.

### 0077 — busca federada inteligente

T62 (human_review): obter julgamentos independentes 0–3 no benchmark, separar
development e holdout, calibrar somente no development e medir nDCG@10,
precision@5, MRR@10, irrelevantes no top 5 e p95. Código não inventa
relevância jurídica; registrar julgadores, conflitos, versão do dataset e
decisão.

### 0078 — cobertura nacional e acesso lícito

| Tarefa | Definição de pronto |
| --- | --- |
| T012 | TJRJ/TJSC CJPG e lacunas CJSG com rota, grau, paginação, fixtures e documento |
| T013 | Falcao comprovado por autoridade trabalhista real |
| T014 | SJUR/TSE/TRE com decisão textual geral, não metadado |
| T015 | Todas as superfícies CJPG estaduais com contrato e live |
| T016 | TRF, STF, STJ, TNU, TJM e STM com detalhe/documento/temporalidade |
| T017 | filtros nativos, traduzidos, locais, ignorados e paginação por provider |
| T019 | detalhe, download ou inteiro teor live com MIME/tamanho/vínculo |
| T021 | fixtures de sucesso, vazio autoritativo, erro, bloqueio e schema drift |
| T022 | validação de autoridade, ramo, grau, identidade, datas e coleção |

### 0081, 0082, 0083 e 0084

- 0081 T003–T006: provar CJPG (grau, classe, filtros, paginação,
  documentos/temporalidade, fixtures e oito gates).
- 0082 T002/T004–T006: provar TRT/TST, criar fixtures diferenciais, separar
  catálogo/metadado de jurisprudência e federar só contratos aprovados.
- 0083 T004: validar live detalhe, documento e intervalo temporal.
- 0084 T002/T004/T005: provar filtros/paginação, detalhe/download/texto
  integral e matriz MIME/PDF/OCR/hash/linkagem.

## 4. Protocolo por provider

1. Ler SDD, contrato, implementação, testes e fixtures.
2. Confirmar a fonte oficial e comparar a estratégia do Juscraper sem copiar.
3. Fazer no máximo uma tentativa normal bounded por rota, em baixa frequência.
4. Preservar access_status, extraction_status, total_state, páginas, latência e
   SourceTrace redigido.
5. Usar o transporte compartilhado e modelos canônicos.
6. Adicionar fixtures de sucesso, vazio autoritativo, erro, bloqueio e drift;
   segunda página quando suportada.
7. Testar filtros nativos, traduzidos, pós-filtrados, não suportados e não
   verificados sem declarar aplicação inexistente.
8. Validar authority, branch, degree, instance, collection, classe, órgão,
   datas, identificador, URL, documento e deduplicação.
9. Executar smoke federado opt-in e só depois alterar rollout.
10. Regenerar inventários ao fim do lote e registrar evidências em
    verification.md.

Estados obrigatórios: success_with_results, authoritative_empty,
unconfirmed_empty, timeout, access_blocked, rate_limited, transport_error,
schema_invalid, partial e cancelled.

403, 429, CAPTCHA, WAF, Turnstile, TLS, timeout, página inesperada e parser
quebrado nunca são authoritative_empty.

## 5. Acesso lícito

Permitido: navegação pública normal, sessão efêmera, CSRF/ViewState/hidden
fields fornecidos pela própria página, cookies da mesma sessão,
redirecionamentos allowlisted, HTTP/1.1 quando exigido (com TLS verificado),
retry/backoff transitório, cache efêmero curto, paginação/documento exibidos
pela fonte e contato oficial.

Proibido: solver de CAPTCHA/OCR de desafio, bypass Turnstile/WAF, replay de
token/cookie, stealth/fingerprint spoofing, rotação de proxy/IP para evasão,
evasão de rate limit, relaxamento TLS, endpoint administrativo não público e
qualquer mascaramento de bloqueio.

## 6. Gates de promoção

    runtime == true
    official_source == proven
    degree_contract == valid
    fixtures == complete
    pagination_filters == validated
    live_status == valid
    quality_gate == passed
    access_status == public

Só então usar federation_status=enabled. Candidate, blocked, contextual,
legal_pending, unverified e source_unavailable ficam fora do rollout padrão,
mas aparecem no diagnóstico.

## 7. Comandos de reprodução

    cd C:/Users/admin/Desktop/Nanojuris/repos/nanojuris
    $env:PYTHONPATH = 'src'
    python tools/audit_open_tasks.py
    python tools/validate_executor_packet.py
    python tools/audit_provider_docs.py --write
    python tools/build_provider_coverage.py --write
    python tools/build_degree_coverage.py
    python tools/build_surface_state_registry.py
    python tools/build_state_appellate_program.py --write
    python tools/build_promotion_manifest.py --write
    python tools/build_provider_certification.py
    python tools/validate_sdd.py
    python tools/audit_search_no_ai.py --json
    python -m pytest -q
    python -m ruff check .
    python -m ruff format --check .
    python -m mypy src
    python -m compileall -q src tools tests
    git diff --check

Na plataforma, em repos/nanojuris-platform, repetir pytest, Ruff, format e
mypy. Testes focados durante o lote; suíte completa apenas no fechamento.

## 8. Encerramento

Só declarar sucesso quando open_tasks=0, o programa indicar
complete_8_of_8=27 e coverage_claim=27/27, cada superfície tiver
contrato/fixture/live/qualidade/smoke e todos os gates estiverem verdes.

Se restarem somente bloqueios externos ou julgamentos humanos, produzir
relatório de parada com provider, URL, data, método bounded, classificação,
evidência redigida e ação necessária. Não reduzir a contagem artificialmente.

Mudanças técnicas recentes estão resumidas em
docs/coverage/executor-handoff-20260907-current.md. Preserve a worktree e não
faça commit, push, tag, release, deploy, Terraform apply ou alteração de
produção.

Rechecagem adicional nesta continuidade: TJGO/Projudi foi confirmado live em
7 de setembro, páginas 1 e 2, com quatro IDs de segundo grau sem sobreposição.
A evidência redigida está em docs/provider-discovery/tjgo-projudi-live-20260907.json
e foi adicionada ao gerador de cobertura.

Também foram revalidados, em chamadas bounded de 7 de setembro, STM e TRF4:
duas páginas sem sobreposição e uma rota de detalhe com texto extraído em cada
caso. As evidências são
docs/provider-discovery/stm-live-20260907-cycle59.json e
docs/provider-discovery/trf4-live-20260907-cycle62.json. Elas cobrem apenas
essas duas superfícies; não encerram o T004 da família federal/superior/militar.

TRF5 também foi revalidado no mesmo ciclo, com duas páginas sem sobreposição
e detalhe HTML não vazio; ver
docs/provider-discovery/trf5-live-20260907-cycle45.json. O T004 continua
aberto para as demais autoridades sem evidência equivalente.

O TST teve nova chamada bounded com detalhe HTML e texto extraído em
docs/provider-discovery/tst-live-20260907-cycle60.json; isso melhora a
evidência da superfície TST, mas não encerra a validação da família inteira.

Uma alternativa oficial do TJAP também foi verificada: o PJe público de 2º
grau respondeu HTTP 200, mas é consulta processual, não jurisprudência textual.
O resultado redigido está em
docs/provider-discovery/tjap-pje-2g-alternative-live-20260907.json e não altera
o bloqueio CJSG.

O benchmark CPU do ranker foi reexecutado com 240 candidatos e 25 rodadas:
p95 de 56,444 ms, sem chamadas de rede, em
docs/benchmarks/live-ranking-performance-20260907.json. A calibração/holdout
continua corretamente pendente de rótulos humanos independentes.

Uma nova QA bounded de documentos validou TRF5, STM, TST e TJPR: quatro
resultados, quatro detalhes com texto e quatro URLs públicas HTTP 200, sem
falhas de probe. O relatório redigido está em
docs/provider-discovery/document-qa-cycle-20260907-batch06.json; ele não
encerra as tarefas de documento para os demais providers.

O pipeline documental compartilhado também recebeu um gate local: o fetch
explícito aplica o limite de bytes do transporte, a qualidade registra MIME,
estrutura PDF, tamanho e SHA-256, e referências que carregam `decision_id`
geram vínculo decisão-documento determinístico. A sonda de URL é HTTPS,
allowlisted por host, streamed e limitada a 4 MB, classificando documento
vazio, malformado ou excessivo sem convertê-lo em vazio autoritativo. A
verificação focada (34 testes, Ruff, formato e mypy) está em
`specs/changes/0084-fulltext-and-field-completeness/verification.md`; isto
fortalece a infraestrutura, mas não encerra a evidência externa de T019/T004/T005.
Uma sonda posterior do TRF5 usando o código endurecido carregou 9.941 bytes de
HTML oficial, extraiu o texto e validou MIME, hash e HTTP 200 sem falha; o
artefato está em
`docs/provider-discovery/document-qa-cycle-20260907-batch08.json`.
O lote seguinte validou TNU (HTML, 29.116 caracteres), TJMS (PDF válido de 14
páginas, 41.313 caracteres) e classificou STJ/SCON como controle de acesso,
sem converter o bloqueio em vazio; a evidência está em
`docs/provider-discovery/document-qa-cycle-20260907-batch09.json`.

A inspeção bounded do formulário oficial TJRJ EJURIS confirmou as opções de
origem de segundo grau e não revelou uma opção de primeiro grau; essa evidência
está em `docs/provider-discovery/tjrj-ejuris-origin-options-live-20260907.json`.
Ela reforça o contrato CJSG, mas não encerra a lacuna CJPG do TJRJ.

O lote de QA documental seguinte consultou as sete fontes com rota de detalhe
pendente. BNP retornou resultado contextual, mas sua URL de busca respondeu
405; CJF e os dois endpoints STF permaneceram explicitamente em erro de acesso
ou TLS; SJUR/TSE permaneceu catalog-only; TJCE Informativos teve URL oficial
HTTP 200; e TJSP NugepNAC confirmou vazio para esse termo. O artefato redigido
é `docs/provider-discovery/document-qa-cycle-20260907-batch10.json`. Nenhum
erro foi convertido em vazio e o lote não fecha as tarefas nacionais de
inteiro teor.

O Boletim Jurídico público do TJSE também foi revalidado com uma chamada
bounded para `responsabilidade`: HTTP 200, dez ementas textuais de seção
recursal, identidade explícita `degree=second`, `instance=second` e
`collection=CJSG`, além de links públicos. O total global continua desconhecido
por edição/seção. A evidência redigida está em
`docs/provider-discovery/tjse-boletim-jurisprudencia-live-20260907.json`.

A auditoria do contrato unificado também foi regenerada: 47 providers no
envelope federado, 44 com evidência live na fotografia auditada e 33 com dados
válidos nessa fotografia. A matriz estruturada está em
docs/provider-discovery/unified-contract-matrix.json; bloqueios e contratos
rejeitados permanecem explícitos.
