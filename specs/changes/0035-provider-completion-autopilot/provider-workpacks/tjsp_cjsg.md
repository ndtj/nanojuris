# Work pack — TJSP Consulta de Jurisprudencia/CJSG

Source ID: tjsp_cjsg
Lifecycle: runtime
Coverage role: primary_textual_jurisprudence
Maturity: silver
Target: gold
Priority: P1

## Contrato observado

- busca textual: True
- filtros: text, exact_phrase, number, types, updated_from, updated_to, order_by
- paginação: page
- completude: unknown
- inteiro teor: unknown
- registros canônicos: CanonicalDecision, CanonicalDocument
- busca unificada: True

## Evidência local

- módulo: src/nanojuris/providers/tjsp_cjsg.py
- dossier: docs/providers/tjsp_cjsg/README.md
- source contract: docs/source-contracts/tjsp_cjsg.md
- readiness documental: implementation_ready
- itens documentais abertos: 0
- fixture evidence: versioned_and_inline
- completion status: ready_for_review
- completion phase: review
- disposition: accepted_with_limitations
- review after: not scheduled
- resume when: rerun the promotion manifest after any contract, parser, or schema change

### Testes

- tests/test_client_exporters.py
- tests/test_tjac_cjsg.py
- tests/test_tjal_cjsg.py
- tests/test_tjam_cjsg.py
- tests/test_tjce_cjsg.py
- tests/test_tjms_cjsg.py
- tests/test_tjsp_cjsg.py
- tests/test_tjsp_cjsg_live.py
- tests/test_tjsp_cjsg_live_recheck.py

### Fixtures

- tjsp_cjsg_access_control.html
- tjsp_cjsg_ack.html
- tjsp_cjsg_document.html
- tjsp_cjsg_empty.html
- tjsp_cjsg_result.html

## Evidência live versionada

- status: valid
- data: 2026-09-08
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- maturity:risco operacional alto
- unified:live_status_access_controlled
- full_text_contract_unknown
- known_defects_open

## Defeitos conhecidos

- gap:Documentar criterios objetivos de captcha/access-control.
- gap:Separar rotas de pesquisa, detalhe e inteiro teor.
- gap:Aprofundar fixtures por classe, orgao julgador e documento indisponivel.

## Tarefas obrigatórias

Checklist WP marca que cada item foi avaliado nesta rodada; não
substitui evidência ausente nem converte limitação em sucesso.

- [x] WP-01 — reconciliar capability, dossier, source contract, módulo e interfaces — outcome: accepted_with_limitations; processed; residual limitations remain explicit above
- [x] WP-02 — fechar todos os itens documentais objetivos — outcome: accepted_with_limitations; processed; residual limitations remain explicit above
- [x] WP-03 — garantir fixtures versionadas de sucesso, vazio e falhas críticas — outcome: accepted_with_limitations; processed; residual limitations remain explicit above
- [x] WP-04 — provar identidade, canonicalização, deduplicação, raw e traces — outcome: accepted_with_limitations; processed; residual limitations remain explicit above
- [x] WP-05 — provar filtros, paginação, ordenação, limites e completude — outcome: accepted_with_limitations; processed; residual limitations remain explicit above
- [x] WP-06 — provar estados de acesso, timeout, rate limit e schema drift — outcome: accepted_with_limitations; processed; residual limitations remain explicit above
- [x] WP-07 — provar referência e inteiro teor quando declarados — outcome: accepted_with_limitations; processed; residual limitations remain explicit above
- [x] WP-08 — executar testes locais, tipos, lint e auditorias geradas — outcome: accepted_with_limitations; processed; residual limitations remain explicit above
- [x] WP-09 — executar canário live bounded somente quando autorizado — outcome: accepted_with_limitations; processed; residual limitations remain explicit above
- [x] WP-10 — registrar scorecard, risco residual e decisão de tier — outcome: accepted_with_limitations; processed; residual limitations remain explicit above

## Próximas ações sugeridas

- validar inteiro teor com hash, tamanho e access_status
- classificar WAF, captcha, timeout e mudanca de contrato separadamente
- não submeter payload especulativo; revalidar por replay/contrato aprovado

## Definition of Done

- contrato e capability sincronizados;
- fixtures e testes negativos reproduzíveis;
- identidade, conteúdo, datas, paginação, completude e traces comprovados;
- bloqueios externos preservados sem false empty;
- documentação e catálogos gerados em paridade;
- scorecard revisado pelo papel de dados/QA;
- evidência em verification.md do pacote de implementação;
- fingerprint da evidência registrado e sem alteração pendente;
- decisão final aceita, aceita com limitações, rejeitada, adiada com revisão ou fora de escopo;
- produção e publicação somente com autorização humana.
