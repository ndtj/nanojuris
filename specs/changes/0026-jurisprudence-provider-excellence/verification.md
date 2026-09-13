# Verificação — programa de excelência

Status: verified_with_limitations

## Ambiente

- repositório: nanojuris;
- branch observada: `release/0.4.0`;
- snapshot Juscraper: `604c1dd70d6f313011cc1079790febe6c71807e2`;
- origem: `https://github.com/jtrecenti/juscraper.git`;
- HEAD remoto verificado em 2026-09-01: mesmo commit;
- produção, publicação e deploy: não realizados; chamadas live bounded foram
  executadas sem persistir corpos sensíveis.

## Comandos e resultados

Nota de atualização: esta página registra o checkpoint de planejamento. A
validação live bounded posterior está registrada em 0035 e em
`docs/provider-discovery/all-provider-sweep-20260901.json`; produção e
publicação continuam sem alteração.

| Gate | Resultado | Evidência |
| --- | --- | --- |
| baseline do catálogo | pass | snapshot: 56 fontes, 46 runtime, 42 unificadas; não usado como denominador nacional |
| inventário Juscraper | pass estático | 25 CJSG, 3 CJPG, 1 detalhe TJTO e collection adicional de turma recursal TJES |
| licença Juscraper | pass para planejamento | MIT observada; cópia substancial ainda exige atribuição/revisão |
| decomposição SDD | pass | 1 programa + 14 pacotes filhos; 190 artefatos incluindo work packs gerados |
| validação SDD | pass | `python tools/validate_sdd.py` |
| auditoria semântica de rastreabilidade | pass | todos os REQ/AC explícitos de 0026–0040 representados em `traceability.md` |
| testes focados | pass | 4 passed |
| suíte completa final | pass | `python -m pytest -q`; 872 passed, 9 skipped |
| CI com cobertura | pass | execução anterior à inclusão do teste de migração: 871 passed, 9 skipped; 85,63%; código `src` inalterado depois |
| Ruff | pass | `python -m ruff check .` |
| formatação | pass | `python -m ruff format --check .`; 848 arquivos |
| tipos do runtime | pass | `python -m mypy src`; 92 arquivos sem erros |
| tipos ampliados | debt registrada | `python -m mypy src tools tests`; 160 erros em 47 arquivos |
| runtime de providers novos | pass | manifesto técnico com 11 fontes prontas |
| chamadas live | pass | suíte bounded pública e rechecagens TJBA/TJES/TJRN |

## Revisões executadas

- topologia nacional substitui contagem de source IDs como denominador;
- identidade jurídica separa processo, decisão, versão, publicação e documento;
- federação declara semântica, ranking, filtros, cursor e incompletude;
- bloqueio externo não encerra provider enquanto houver trabalho offline seguro;
- fingerprint invalida disposição terminal obsoleta;
- coverage epochs tornam a execução finita mesmo com expansão contínua;
- TJES foi separado em segundo grau, primeiro grau e turma recursal;
- Juscraper ganhou manifesto por unidade, hardening diferencial e delta upstream;
- retries de 403, exceções engolidas, tokens de configuração e CAPTCHA foram
  convertidos em gates explícitos de segurança/qualidade;
- coleta reprodutível foi separada de busca federada e de promessa de espelho.

## Rastreabilidade

REQ-001 a REQ-020 estão ligados a pacotes, tarefas e gates em
`traceability.md`. Os novos pacotes 0036–0040 e o manifesto 0039 fecham as
lacunas encontradas na revisão. O pacote 0034 registra a dívida de tipos fora
do escopo atualmente bloqueante da CI.

## Resultados

O programa foi executado no escopo técnico local/federado. O catálogo continua
sem declarar cobertura nacional: lacunas, bloqueios e fontes não promovidas
permanecem visíveis nos artefatos gerados.

## Pendências e limites

- obter decisão de licença/reuso antes de fixtures live ou código substancial;
- definir budgets por host antes de qualquer validação live;
- reduzir a dívida de tipagem em tools/tests sem enfraquecer `mypy src`;
- implementar o schema machine-readable da topologia e integrar a fila 0035;
- resolver Q-006 a Q-008 do programa antes do respectivo gate de alto impacto;
- reconciliar trabalhos abertos 0006/0007 durante a fundação;
- nenhuma disponibilidade atual de rota externa foi inferida da análise estática.
