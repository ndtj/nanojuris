# Pesquisa e evidências de planejamento

## Estado local observado

O baseline de 2026-09-08 está em
`specs/changes/0091-national-coverage-gold-handoff/baseline-20260908.json`.
Ele registra 73 fontes documentadas, 68 em runtime, 50 unificadas, 56 com
algum suporte documental, 25/27 superfícies estaduais de segundo grau completas,
8/27 CJPG, 25/27 CJSG e 60 tarefas abertas.

O catálogo atual diferencia maturidade, lifecycle, live status e cobertura. Essa
separação deve ser preservada: “funciona no Juscraper” não prova que a rota
oficial está disponível hoje nem que o contrato NanoJuris está fechado.

## Evidência a reutilizar

- `docs/coverage/source-of-truth.md`: precedência dos artefatos.
- `docs/registry/provider-catalog.full.json`: inventário gerado.
- `docs/coverage/surface-state-registry-20260902.json`: superfícies e gaps.
- `docs/coverage/state-appellate-program-20260905.json`: 27 TJs e workpacks.
- `docs/provider-discovery/juscraper-parity-assessment-20260906.md`: paridade
  semântica, não cópia de código.
- `docs/coverage/public-access-boundary-playbook-20260908.md`: limite de acesso
  público já aprovado tecnicamente.
- SDD 0091, 0092, 0097: handoff, blueprint e provider TJMG/EJEF.
- `national-source-task-matrix.json`: inventário executável de 251 linhas,
  incluindo as 59 superfícies Juscraper sem semântica NanoJuris confirmada.
- `docs/provider-discovery/national-directory-live-20260908.json`: GET bounded
  das cinco âncoras institucionais do CNJ; HTTP 200 comprova apenas o diretório.

Os diretórios institucionais usados como âncoras de descoberta são o catálogo
de Tribunais de Justiça Estaduais, Justiça do Trabalho, Justiça Eleitoral,
Tribunais de Justiça Militar e Relatório por Tribunal do CNJ. Eles servem para
enumerar autoridades; cada rota de jurisprudência ainda exige contrato e
evidência live própria.

## Hipóteses que devem ser provadas

1. Uma rota de jurisprudência pode expor apenas ementas, não inteiro teor.
2. Uma coleção chamada “sentenças” pode ser curada e não representar todo o
   primeiro grau.
3. API pública pode exigir filtros que distinguem primeiro e segundo grau.
4. Exportação oficial pode ser mais estável e econômica do que scraping HTML.
5. Um desafio interativo pode ser passivo ou obrigatório; os dois estados são
   diferentes e devem ser registrados.

## Princípios de investigação

- Priorizar documentação e exportação da própria fonte.
- Fazer uma chamada bounded por hipótese antes de escrever adapter.
- Sanitizar fixtures e descartar corpos que contenham PII desnecessária.
- Encerrar repetição ao primeiro bloqueio determinístico.
- Registrar limitações em vez de preencher campos por inferência forte.
