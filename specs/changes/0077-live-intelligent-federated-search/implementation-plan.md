# Plano de implementação — busca live inteligente

## Estratégia

Implementar verticalmente, mantendo cada estágio testável e o comportamento
legado disponível. Não iniciar pela UI: o ranking comparável e seus contratos
devem estar estáveis antes do merge progressivo.

## Fase 0 — baseline e proteção da worktree

1. Ler `AGENTS.md`, constituição, SDD 0038 e este pacote.
2. Registrar `git status --short` dos dois repositórios; alterações existentes
   pertencem ao usuário.
3. Executar testes focados de cliente, routing, plataforma e navegador.
4. Capturar payloads offline das duas consultas de referência usando fixtures.
5. Não regenerar catálogos de providers, pois este SDD não altera cobertura.

## Fase 1 — intenção

1. Implementar tipos imutáveis e serialização estável.
2. Implementar normalização e parser de CNJ antes da tokenização.
3. Criar léxico v1 pequeno e conservador.
4. Implementar frases explícitas/implícitas, negação e classificação de comando.
5. Separar filtros detectados inequívocos de sugestões ambíguas.
6. Exportar API pública aditiva e documentar versões.
7. Fechar testes de português, acento, caixa, pontuação, CNJ e exemplos.

## Fase 2 — planner

1. Adaptar metadata existente sem duplicar catálogo.
2. Implementar score de roteamento puro e explicações.
3. Implementar diversidade e mínimo/máximo de fontes.
4. Produzir ondas estáveis.
5. Compilar filtro por `ProviderCapabilities.filter_status`.
6. Integrar com router 0038 para preservar skips e opt-in.
7. Testar blocked, contextual, filtro exato e ausência de histórico.

## Fase 3 — ranker

1. Criar projeção textual limitada e allowlisted.
2. Implementar cobertura ponderada, frases, proximidade e conceitos.
3. Implementar consistência de filtros e qualidade.
4. Incorporar rank nativo por RRF com constante 20.
5. Implementar penalidades e match CNJ dominante.
6. Produzir razões estruturadas.
7. Integrar deduplicação em estágios e diversidade de near-ties.
8. Substituir o contador legado atrás de flag.
9. Provar determinismo, invariância de permutação e limite de memória/tempo.

## Fase 4 — outcomes e API

1. Mapear resultados atuais para `source_outcomes_v2`.
2. Medir latência por fonte ao redor do future já existente.
3. Incluir query intent, plano e ranking no payload do cliente.
4. Atualizar projeções browser e research por allowlist.
5. Estender modelos Pydantic e validação comum da Function.
6. Preservar requisições legadas e limites de body.
7. Testar FastAPI e OCI Function com payloads equivalentes.

## Fase 5 — web progressiva

1. Tornar adaptive o default somente com feature flag.
2. Executar ondas limitadas, associadas a uma geração de busca.
3. Trocar concatenação por merge global baseado no score absoluto.
4. Preservar seleção por identidade após reordenação.
5. Implementar freeze por interação e buffer pendente.
6. Adicionar ação de aplicar ranking novo.
7. Renderizar chips, razões e status por fonte.
8. Adicionar `aria-live` moderado, foco estável e reduced motion.
9. Testar respostas fora de ordem, cancelamento e nova consulta concorrente.

## Fase 6 — benchmark e calibração

1. Criar schema JSON de queries/julgamentos e validador.
2. Montar conjunto development e holdout; não calibrar no holdout.
3. Capturar pools com o ranker legado e novo.
4. Julgar candidatos 0–3 com IDs cegos e guia objetivo.
5. Calcular nDCG@10, P@5, MRR@10, irrelevante@5 e success@1.
6. Calibrar pesos somente no development set.
7. Rodar holdout uma vez para decisão final.
8. Microbenchmarkar 240 candidatos e medir memória.
9. Registrar limitações sem inflar claims.

## Fase 7 — shadow e operação local

1. Implementar flag `legacy|shadow|legal-live-v1`.
2. Em shadow, calcular ambos sobre o mesmo pool e retornar legacy.
3. Implementar métricas agregadas sem textos.
4. Implementar chave de cache versionada e TTL.
5. Validar rollback sem migração.
6. Produzir instruções de rollout, sem executar publicação.

## Fechamento

1. Rodar testes completos nos dois repositórios.
2. Rodar Ruff, format-check, mypy, compileall e build frontend aplicável.
3. Rodar `python tools/validate_sdd.py`.
4. Executar smokes live bounded autorizados.
5. Executar Playwright autenticado somente com login manual do usuário em
   janela headed; nunca solicitar credenciais em chat.
6. Atualizar `verification.md`, `traceability.md` e status das tarefas.
7. Não fazer commit, push, release ou deploy.

## Critério de parada

Se fonte externa impedir smoke, registrar outcome real e continuar com testes
offline. Isso não bloqueia o algoritmo, mas AC-023 permanece pendente para a
fonte. O programa não pode ser declarado concluído sem métricas do benchmark e
sem fechar AC-001 a AC-024.
