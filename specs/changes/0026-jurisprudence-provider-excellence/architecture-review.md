# Revisão crítica do programa de excelência

Status: reviewed
Data: 2026-09-01
Escopo: pacotes 0026 a 0035, catálogo atual e snapshot Juscraper

## Conclusão

O programa original possuía uma base correta de segurança, provenance e
isolamento por fonte, mas ainda não era suficiente para sustentar a afirmação
"jurisprudência brasileira unificada". Ele tratava o catálogo atual como
denominador nacional, concentrava a expansão nos tribunais estaduais e não
formalizava identidade jurídica, equivalência de busca, collections de
primeiro grau, versionamento do corpus nem invalidação de evidência antiga.

Esta revisão não declara os providers prontos. Ela corrige o plano para que a
execução futura possa produzir uma biblioteca extensível e verificável sem
confundir quantidade, disponibilidade e cobertura.

## Achados críticos e correções

| ID | Severidade | Achado | Consequência | Correção adotada |
| --- | --- | --- | --- | --- |
| AR-001 | crítica | as 56 fontes do catálogo eram tratadas como universo total | “100%” poderia significar apenas 100% do backlog conhecido | criar topologia nacional e denominadores por ramo, instituição, coleção e período |
| AR-002 | crítica | `blocked` encerrava todo o work pack | melhorias offline podiam ser abandonadas por uma falha live | separar estado de trabalho, saúde operacional e disposição final |
| AR-003 | crítica | conclusão não tinha fingerprint da evidência | provider alterado poderia continuar marcado como completo | invalidar aceite quando contrato, fixture, parser ou catálogo mudar |
| AR-004 | crítica | identidade e deduplicação estavam apenas como requisito genérico | decisões distintas do mesmo processo poderiam colidir; cópias iguais poderiam duplicar | criar pacote específico de identidade, taxonomia, versão e deduplicação |
| AR-005 | crítica | busca federada não definia equivalência de consulta ou ranking | resultados de fontes heterogêneas poderiam parecer comparáveis sem serem | criar pacote de semântica, ranking, paginação global e explicabilidade |
| AR-006 | crítica | OCR opcional estava próximo de fontes com CAPTCHA | OCR poderia ser interpretado como solução de desafio de acesso | proibir OCR para CAPTCHA; OCR somente para documentos públicos já obtidos legitimamente |
| AR-007 | alta | intake contava classes/tribunais, não superfícies jurídicas | `cjsg`, `cjpg`, detalhe e consulta processual eram misturados | inventariar método, coleção, grau, rota e decisão de escopo separadamente |
| AR-008 | alta | Juscraper tinha apenas três candidatos explícitos | rotas de primeiro grau e enriquecimento TJTO ficavam invisíveis | adicionar ledger de 25 CJSG, 3 CJPG e 1 detalhe de ementa |
| AR-009 | alta | plano estadual não cobria Justiça do Trabalho, Eleitoral e Militar em profundidade | “nacional” permanecia nominal | criar topologia de todos os ramos e backlog de lacunas por coleção |
| AR-010 | alta | o objetivo não distinguia federação live de corpus persistido | completude de uma busca podia ser confundida com acervo nacional | separar busca federada, coleta reprodutível e eventual dataset |
| AR-011 | alta | estado `deferred` não exigia prazo nem gatilho de revisão | candidatos poderiam desaparecer da fila | exigir rationale, owner, `review_after` e `resume_when` |
| AR-012 | alta | tarefas genéricas não provavam DoD por provider | checklists podiam ser marcados sem evidência verificável | exigir evidence manifest, comandos, hashes e revisão independente |
| AR-013 | média | score “gold” era usado como alvo mesmo para fonte externamente bloqueada | maturidade de implementação e saúde live eram confundidas | separar tier de engenharia, qualidade de dados e saúde operacional |
| AR-014 | média | testes fixavam exatamente 56/46/9 | crescimento legítimo quebraria o autopilot | validar consistência contra o catálogo atual e publicar tendências históricas separadamente, não cardinalidade eterna |
| AR-015 | média | README informava 44 runtime e catálogo gerado informava 46 | documentação pública já estava divergente | alinhar README e adicionar gate de claim derivado |
| AR-016 | média | atualização upstream não possuía política de delta | novas rotas do Juscraper poderiam passar despercebidas | registrar commit, delta, decisão e nova auditoria periódica, sempre manualmente promovida |
| AR-017 | média | consulta live de termo único era evidência frágil | vazio legítimo e regressão poderiam ser confundidos | usar corpus pequeno com caso positivo conhecido, negativo e schema probe |
| AR-018 | média | `raw mínimo` e reprodução integral não tinham fronteira | risco de perder auditoria ou acumular PII desnecessária | definir raw redigido no registro e manifesto/hash para payload bruto opcional |
| AR-019 | alta | API TJES reunia primeiro grau, segundo grau e turma recursal no mesmo plano | cobertura, identidade e métricas de collections distintas seriam misturadas | restringir 0025 ao segundo grau e abrir bindings próprios para primeiro grau e turma recursal |
| AR-020 | média | a execução longa não possuía conceito de época | um programa crescente nunca teria snapshot fechável nem comparação histórica | executar épocas finitas ligadas a uma versão da topologia e abrir nova época quando o universo mudar |
| AR-021 | alta | o handoff dizia “mypy verde”, mas a CI verifica apenas `src` | 160 erros em tools/tests ficavam fora da afirmação e poderiam ocultar doubles incompatíveis com contratos | declarar escopo do gate, manter `mypy src` bloqueante e reduzir baseline de tools/tests sem permitir regressão |

## Invariantes resultantes

1. Cobertura nunca é um único percentual sem denominador e data.
2. Uma instituição pode possuir várias coleções e vários providers.
3. Um provider implementado pode estar operacionalmente bloqueado sem perder
   sua evidência offline.
4. Uma rota externa só vira provider após fonte oficial, contrato, fixture e
   teste de equivalência.
5. Ranking de fontes distintas não é comparável por padrão.
6. O mesmo número de processo não identifica uma única decisão.
7. Primeiro grau, segundo grau, precedentes e informativos são coleções
   distintas, ainda que pertençam ao mesmo tribunal.
8. CAPTCHA, Turnstile, login e WAF não são problemas a serem “resolvidos” pelo
   scraper.
9. Evidência expira e toda conclusão é revalidada quando seu fingerprint muda.
10. “Toda a jurisprudência brasileira” é uma direção de cobertura mensurável,
    não uma promessa de disponibilidade integral dos sistemas externos.

## Decisão de prontidão

O planejamento só fica apto para implementação após os novos pacotes 0036 a
0040 estarem validados e as perguntas de fundação com impacto público terem
decisão explícita. A execução deve começar por topologia, identidade, contrato
e qualidade; não por copiar adapters externos.
