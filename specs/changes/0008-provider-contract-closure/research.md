# Research — fechamento de contratos provider a provider

Data: `2026-08-20`

## Estado de partida

- Discovery profundo: 44/44 providers runtime e 9/9 candidates documentais observados.
- Evidência agregada: 3.275 rotas candidatas e 299 campos de filtro observados.
- Backlog automático: 90 itens em 40 providers runtime e 18 itens nos 9 candidates.
- O backlog mistura lacunas reais com tarefas de promoção que não podem ser resolvidas por GET bounded: payloads POST, fixtures de sucesso/vazio/erro, detalhe, texto integral e estados de acesso.

## Causas raiz

1. O discovery não envia POST sem payload contratado; portanto a observação live não substitui fixture local.
2. Alguns providers têm contrato e testes locais, mas o sweep ainda os marca como “confirmar POST”.
3. Controle de acesso, robots, TLS e indisponibilidade são impedimentos externos e precisam virar estados documentados, não falsos sucessos.
4. Candidates não possuem adapter runtime e não devem ser promovidos só porque a página institucional respondeu.

## Regra de fechamento

Um TODO só pode ser encerrado por evidência equivalente: contrato de rota/payload, fixture versionada, parser/canonicalização, teste de sucesso e estados de vazio/erro. Quando a fonte não permite confirmação pública, o item será convertido em bloqueio operacional explícito com próxima ação autorizada.
