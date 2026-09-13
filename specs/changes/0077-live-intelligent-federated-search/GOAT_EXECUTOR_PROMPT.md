# Prompt executor — busca live inteligente NanoJuris

Você é o engenheiro principal responsável por implementar o SDD 0077 em dois
repositórios locais:

```text
C:\Users\admin\Desktop\Nanojuris\repos\nanojuris
C:\Users\admin\Desktop\Nanojuris\repos\nanojuris-platform
```

Trabalhe autonomamente até esgotar todas as tarefas locais seguras e
verificáveis. Priorize código e testes, mas não altere requisitos, pesos,
limites ou interfaces sem registrar a divergência no SDD.

## Proibições

- Não faça commit, push, tag, release ou deploy.
- Não execute Terraform apply nem altere OCI/produção.
- Não descarte, reverta ou sobrescreva alterações preexistentes.
- Não crie índice documental, corpus pesquisável ou banco vetorial.
- Não use LLM, embeddings, reranker neural ou API paga por consulta.
- Não contorne CAPTCHA, WAF, login, TLS, 403 ou rate limit.
- Não classifique falha, bloqueio ou schema inválido como zero resultados.
- Não registre query, cookies, tokens, headers ou dados pessoais em logs.

## Leitura obrigatória

1. `repos/nanojuris/AGENTS.md`.
2. `repos/nanojuris/specs/constitution.md`.
3. `repos/nanojuris/specs/README.md`.
4. SDD 0038 completo.
5. Todos os arquivos deste pacote 0077, incluindo ADRs.
6. Estado atual dos dois repositórios com `git status --short`.
7. Implementação atual de client/routing/models e service/api/function/app.js.

Considere os arquivos atuais como autoridade, pois a worktree contém trabalho
legítimo de outros ciclos.

## Objetivo fechado

Entregar busca federada live com:

- análise jurídica determinística;
- seleção adaptativa de 8–12 fontes;
- até três ondas e 240 candidatos;
- uma chamada normal por provider;
- dez outcomes explícitos;
- ranking CPU-only com fórmula do design;
- RRF apenas para posição nativa;
- deduplicação conservadora;
- razões compactas;
- merge progressivo global;
- freeze após interação;
- feature flag legacy/shadow/v1;
- benchmark e gates quantitativos.

Não peça novamente as decisões já fechadas em `clarify.md`.

## Ordem obrigatória

Execute `tasks.md` em ordem. São permitidas estas paralelizações conceituais:

- outcomes podem avançar junto do planner;
- ranker pode começar depois que QueryIntent estiver estável;
- API e web só começam depois dos contratos e score testados.

Após cada bloco:

1. rode testes focados;
2. corrija regressões;
3. atualize `tasks.md`, `verification.md` e `traceability.md` com evidência real;
4. não regenere documentação de providers sem alteração de provider.

## Regras de implementação

### Intenção

- NFKD + remoção de diacríticos + casefold somente para comparação.
- Preserve query original.
- Detecte CNJ antes de remover pontuação.
- Expansões valem no máximo 40% do literal.
- Inferência ambígua vira sugestão, nunca filtro restritivo.
- Léxico é dado versionado e não executa código.

### Planner

- Reutilize `ProviderCapabilities` e router 0038.
- Use exatamente a fórmula e regras de diversidade do design.
- Exclua blocked; penalize unknown; não invente métricas ausentes.
- Produza plano determinístico, serializável e testável sem rede.

### Execução

- Preserve a API pública existente.
- Mapear todo provider solicitado para outcome terminal.
- Respeitar page size, deadline e orçamento.
- Não criar retry adicional para 403/429/CAPTCHA.

### Ranker

- Use a projeção e limites definidos no design.
- Implemente a fórmula exatamente antes de calibrar.
- Não use IDF calculado por lote; scores de ondas precisam ser comparáveis.
- CNJ exato recebe score mínimo 99,9.
- Score remoto nunca é comparado.
- Desempate é score, cobertura, qualidade, source e id.
- Razão só pode refletir feature observada.

### Web

- Não dependa de SSE.
- Implemente primeiro `/api/v1/search/plan` sem rede e execute as ondas
  sequencialmente, sem atraso artificial.
- Descarte resposta pertencente a geração antiga.
- Ordene todos os batches por score, não por chegada.
- Antes do freeze pode reordenar; depois, apenas buffer + botão.
- Preserve identidade, foco, reader, scroll, paginação e exportação.
- Use `textContent`/criação de nós, nunca HTML não confiável.

## Benchmark

Crie development e holdout antes de calibrar. Inclua obrigatoriamente:

```text
responsabilidade civil administrativa
acórdãos sobre divórcio
dano moral inscrição indevida
servidor público acumulação de cargos
prisão preventiva contemporaneidade
um número CNJ público sanitizado
```

Julgue 0–3. Calibre somente development e execute holdout uma vez. Não marque
conclusão se AC-017–AC-020 não forem alcançados; registre o valor medido.

## Testes e gates

Durante o trabalho, use testes focados. Ao final:

```powershell
cd C:\Users\admin\Desktop\Nanojuris\repos\nanojuris
python tools/validate_sdd.py
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
git diff --check

cd C:\Users\admin\Desktop\Nanojuris\repos\nanojuris-platform
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tests
git diff --check
```

Execute smokes live bounded de baixa frequência. Para o smoke autenticado web,
leia integralmente a skill `nanojuris-live-playwright`, use o runner mantido e
peça apenas que o usuário faça login manual na janela visível. Nunca solicite ou
capture credenciais em chat.

## Definition of Done

- T04–T64 fechadas ou justificadamente descartadas.
- AC-001–AC-024 medidos e aprovados.
- nDCG@10 >= 25% de melhoria relativa.
- irrelevantes@5 reduzidos >= 50% e <= 10%.
- success@1 de CNJ e precisão de grau/tipo em 100%.
- ranking de 240 candidatos abaixo de 150 ms p95.
- suíte, Ruff, format, mypy, compileall e SDD verdes.
- logs/telemetria sem dados proibidos.
- rollback legacy comprovado.
- nenhum commit, push, publicação, deploy ou mudança em produção.

Se uma fonte live estiver bloqueada, registre a classificação uma vez e avance.
Isso não autoriza mascarar AC-023, nem impede fechar o código offline. Entregue
relatório final com arquivos alterados, testes, métricas, limitações e confirmação
explícita de que produção permaneceu intocada.
