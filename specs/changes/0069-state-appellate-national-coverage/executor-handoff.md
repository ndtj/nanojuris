# Handoff para o modelo executor

Para uma execução integral e autocontida, prefira
[`GOAT_EXECUTOR_PROMPT.md`](GOAT_EXECUTOR_PROMPT.md). O prompt resumido abaixo
permanece útil para ciclos curtos.

## Prompt recomendado

Trabalhe no repositorio `repos/nanojuris` para concluir o SDD 0069. Leia
`AGENTS.md`, `specs/constitution.md`, `specs/README.md`, o SDD 0069 inteiro e o
workpack JSON antes de editar. Escolha a primeira superficie incompleta na ordem
de `implementation-plan.md` e conclua o maximo de gates comprovaveis. Execute
chamadas live somente de baixa frequencia, uma pagina pequena, fontes publicas e
sem credenciais. Nunca contorne CAPTCHA, WAF, login, TLS ou rate limit e nunca
converta falha em vazio. Preserve a worktree existente. Nao faca commit, push,
deploy ou mudanca de producao. Ao terminar cada tribunal, regenere todos os
artefatos listados, rode testes focados e a suite completa, atualize a
verificacao do pacote individual e volte ao proximo workpack. Pare somente ao
atingir 27/27 ou quando todas as linhas restantes tiverem bloqueio externo
comprovado e nenhuma acao local segura restante.

## Entrada autoritativa

1. `docs/coverage/state-appellate-program-20260905.json`;
2. `specs/changes/0069-state-appellate-national-coverage/implementation-plan.md`;
3. `docs/coverage/surface-state-registry-20260902.json`;
4. `docs/registry/provider-catalog.full.json`;
5. dossie, source contract, provider e testes da linha escolhida;
6. snapshot Juscraper apenas como referencia secundaria.

## Relatorio obrigatorio por ciclo

- tribunal e superficie trabalhados;
- gates antes/depois;
- arquivos alterados;
- comandos e resultados;
- evidencia live redigida;
- bloqueios semanticos/externos;
- nova contagem 8/8;
- confirmacao de que nao houve commit, push ou deploy.
