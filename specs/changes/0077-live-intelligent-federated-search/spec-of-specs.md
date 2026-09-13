# Spec of specs — busca live inteligente e determinística

ID: `0077-live-intelligent-federated-search`
Status: `proposed`
Data: `2026-09-07`

## Resultado do programa

Entregar na biblioteca NanoJuris e na plataforma web uma busca federada live
que melhora de forma mensurável o top 10, sem índice documental próprio e sem
IA por consulta. A solução deve interpretar a consulta, selecionar de 8 a 12
fontes elegíveis, executar ondas limitadas, ranquear candidatos em escala
comparável, explicar o resultado e preservar os estados reais de cada fonte.

O programa estende o SDD 0038. Não altera seus invariantes: scores remotos não
são comparados diretamente, filtros não comprovados não são inventados e erro
externo nunca se transforma em resultado vazio.

## Decomposição executável

| Trilha | Entrega | Gate independente |
| --- | --- | --- |
| A — intenção | `LegalQueryAnalyzer`, `QueryIntent` e vocabulário jurídico versionado | consultas douradas produzem intenção determinística |
| B — planejamento | roteamento adaptativo, `SearchPlan`, ondas e orçamento | 8–12 fontes elegíveis, diversas e auditáveis |
| C — execução | compilação por provider, deadlines e estados normalizados | uma chamada normal por fonte e falhas explícitas |
| D — ranking | score jurídico absoluto, RRF de posição nativa, deduplicação e diversidade | top 10 determinístico e melhor que o baseline |
| E — API | contratos aditivos e projeção segura para navegador | compatibilidade com clientes existentes |
| F — UX | progresso por ondas, chips, razões, congelamento e atualização pendente | nenhuma perda de foco ou salto após interação |
| G — avaliação | benchmark, métricas, performance e live bounded | critérios quantitativos AC-017 a AC-024 |
| H — operação | feature flag, shadow, telemetria mínima e rollback | ativação reversível sem índice nem LLM |

## Ordem e dependências

```text
A -> B -> C
A -> D
B + C + D -> E -> F
D -> G
E + F + G -> H
```

Testes focados devem rodar por trilha. A suíte completa roda no fechamento. A
documentação pública somente será alterada quando o comportamento correspondente
existir; este pacote não autoriza produzir claims antecipados.

## Repositórios afetados

- `repos/nanojuris`: contratos, analisador, planner, ranker, federação e testes.
- `repos/nanojuris-platform`: API privada, função OCI, JavaScript/CSS e testes.
- `repos/nanojuris-infra`: somente em fase futura de rollout; nenhuma alteração
  é necessária para a implementação local do algoritmo.

## Condição de conclusão

O programa só pode mudar para `verified` quando todas as tarefas técnicas
T01–T64 estiverem concluídas ou justificadamente descartadas, a matriz de
rastreabilidade estiver fechada, os critérios quantitativos forem medidos e o
`verification.md` contiver comandos e resultados reais. Commit, push e deploy
continuam fora do escopo.
