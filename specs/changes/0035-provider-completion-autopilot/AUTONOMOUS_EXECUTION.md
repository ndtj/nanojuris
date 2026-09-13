# Protocolo central de execução autônoma

Este é o artefato de entrada para qualquer agente que continue o programa. Ele
autoriza somente trabalho dentro do repositório e dos limites já aprovados.

## Objetivo finito

Processar unidades de cobertura e providers até que cada item possua disposição
comprovada: `accepted`, `accepted_with_limitations`, `rejected`,
`deferred_with_review` ou `out_of_scope`. Não usar loop cego, espera ilimitada
ou repetição sem nova evidência.

## Inicialização obrigatória

1. Ler `AGENTS.md`, `specs/constitution.md` e `specs/README.md`.
2. Ler 0026 e os pacotes 0027–0040.
3. Executar:

       python tools/build_provider_sdd_workpacks.py
       python tools/validate_sdd.py

4. Ler a topologia 0036, `execution-state.json`, o resumo da fila e o ledger de
   superfícies Juscraper 0029.
5. Verificar working tree, dependências, autorização e conflito com mudanças do
   usuário.

Para encerrar o processamento local de uma rodada sem rede, executar após a
regeneração do catálogo e do manifesto:

    python tools/complete_provider_workpacks.py --write

O comando é bounded e idempotente: fontes tecnicamente prontas recebem uma
disposição positiva com limitações, enquanto fontes incompletas ou bloqueadas
recebem `deferred_with_review` com condição objetiva de retomada. Ele não faz
deploy, push, publicação, bypass ou mutação da federação.

## Ordem obrigatória

1. Topologia nacional por coleção (0036).
2. Identidade canônica e deduplicação (0037).
3. Contrato/runtime/qualidade compartilhados (0027, 0028 e 0031).
4. Semântica federada e completude (0038).
5. Intake e adapters Juscraper por ondas (0029 e 0039).
6. Cobertura por ramo/grau e pipeline documental (0030 e 0032).
7. Coleta reprodutível/freshness (0040).
8. Observabilidade e release (0033 e 0034).

## Loop de trabalho

1. Selecionar a primeira unidade elegível por prioridade e dependências.
2. Marcar owner, fase, checkpoint e fingerprint.
3. Ler topologia, work pack, dossier, catálogo, contrato, módulo, fixtures e testes.
4. Auditar entrada, saída, identidade, conteúdo, datas, paginação, completude,
   acesso, falhas, documentos e interfaces.
5. Abrir/atualizar SDD próprio antes de código não trivial.
6. Implementar a menor tarefa reversível.
7. Executar testes focados, lint/tipos e registrar evidência.
8. Atualizar estado e `verification.md`.
9. Fazer revisão cruzada proporcional ao risco.
10. Aceitar somente após todo o DoD e fingerprint atual.
11. Se houver bloqueio externo, continuar tarefas offline seguras; se esgotadas,
    registrar deferimento revisável e seguir.
12. Repetir enquanto houver trabalho seguro autorizado.

## Gates por provider/coleção

- fonte oficial, autoridade, coleção, grau, período e tipo documental confirmados;
- capability, dossier e contrato em paridade;
- fixtures de sucesso, vazio legítimo e falhas críticas;
- identidade, canonicalização, versões e deduplicação estáveis;
- filtros, paginação, ordenação, limites e completude honestos;
- `SourceTrace` e `ExtractionTrace` reproduzíveis;
- estados de acesso, timeout, rate limit, WAF e schema drift distintos;
- documento/inteiro teor conforme capability;
- impacto em SDK, CLI, MCP, Studio, exports e store avaliado;
- scorecard, saúde operacional e disposição revisados separadamente;
- verification reproduzível e fingerprint atual.

## Três ocorrências e retomada

Três ocorrências iguais sem nova evidência encerram apenas a tentativa atual,
não o provider. Registrar `waiting_evidence`; usar `deferred_with_review` apenas
quando não houver trabalho seguro restante e preencher owner, `review_after`,
`resume_when`, evidência e impacto.

## Limites invioláveis

- não contornar CAPTCHA, WAF, login ou rate limit;
- não armazenar credenciais;
- não usar DataJud/processos como jurisprudência textual;
- não tratar falha como zero resultados;
- não fazer deploy, push, publicação ou operação destrutiva sem autorização;
- não gerar tráfego contínuo para tribunais.

## Condição de parada

Parar quando todos os itens elegíveis tiverem disposição comprovada, quando a
próxima ação exigir nova autoridade/credencial ou quando não restar trabalho
seguro. Registrar resumo, testes, fingerprints, limitações, revisões agendadas e
comando exato de retomada.
