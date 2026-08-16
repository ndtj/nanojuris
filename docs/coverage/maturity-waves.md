# Maturity Waves

Este plano organiza a evolucao do NanoJuris depois da auditoria de cobertura.
Ele deve ser lido junto com:

- [matrix.md](matrix.md);
- [maturity-score.md](maturity-score.md);
- [improvement-queue.md](improvement-queue.md);
- [../registry/provider-catalog.full.json](../registry/provider-catalog.full.json).

O objetivo nao e aumentar quantidade de rotas a qualquer custo. O objetivo e
construir uma biblioteca confiavel para jurisprudencia textual brasileira,
jurimetria, engenharia de dados, advogados e agentes de IA.

## Principio Diretor

Cada provider deve responder, de forma auditavel:

1. qual fonte oficial foi consultada;
2. qual rota, metodo, payload, filtros e pagina foram usados;
3. qual conteudo juridico foi retornado;
4. quais campos foram extraidos sem inferencia;
5. quais campos foram normalizados;
6. qual limite, bloqueio ou falha foi observado;
7. se a fonte e adequada para busca unificada, Studio, MCP e coleta
   estatistica.

## Equipe E Responsabilidades

| Papel | Responsabilidade nesta onda |
| --- | --- |
| Tech lead | ordenar fila, bloquear atalhos inseguros e garantir criterio de saida |
| Arquiteto de dados juridicos | separar jurisprudencia textual, precedentes, informativos e fontes contextuais |
| Engenheiro de providers | fechar contrato HTTP, parser, paginacao, documentos e erros |
| QA de fontes judiciais | criar fixtures, testes offline e validacao live opt-in |
| Especialista jurimetrico | garantir datas, identificadores, campos e deduplicacao uteis para estatistica |
| Especialista MCP/IA | garantir respostas com proveniencia, limites e roteamento seguro |
| DevOps/Release | manter CI, catalogo gerado, schema, drift tests e release checklist |
| Documentacao/Branding | transformar contrato tecnico em indice claro para humanos e IA |

## Onda 1 - Catalogo Operacional

Status: concluida como baseline; manter regeneracao e testes de drift.

Entregas:

- catalogo completo em JSON para humanos e IA;
- matriz de cobertura;
- entradas, saidas, campos canonicos e live status;
- score de maturidade 0-100;
- fila de melhoria priorizada;
- testes de drift para impedir documentacao divergente.

Criterio de saida:

- `tools/build_provider_coverage.py --write` reproduz todos os arquivos;
- schema valida `maturity_score`;
- testes de coverage e documentacao passam;
- README de coverage aponta para a fila correta.

## Onda 2A - Hardening Documental Dos P0

Status: concluida como baseline documental; 33 dossies ainda exigem
aprofundamento operacional segundo o catalogo atual.

Escopo inicial:

- `cjf_jurisprudencia`;
- `stf_juris`;
- `tjsp_cjsg`;
- `stj_scon`;
- `trf5_jurisprudencia`.

Trabalho:

1. completar secoes formais de dados e proximos passos;
2. transformar lacunas genericas em experimentos verificaveis;
3. registrar rotas, filtros, payloads, estados de erro e limites;
4. declarar explicitamente o que ainda nao pode ser prometido;
5. manter paridade entre `docs/providers/*` e `docs/source-contracts/*`.

Criterio de saida:

- nenhum dossie P0 deve falhar por secao estrutural ausente;
- pendencias restantes devem ter evidencia exigida e criterio de fechamento;
- score sobe por maturidade real, nao por omissao de riscos;
- `audit_provider_docs.py` e `build_provider_coverage.py` continuam
  reproduziveis.

## Onda 2B - Fixtures E Contratos Offline

Escopo:

- providers P0 com score C ou B baixo;
- familias reutilizaveis, especialmente CJSG/e-SAJ, eproc e APIs JSON.

Trabalho:

1. fixture de sucesso com resultado juridico real e reduzido;
2. fixture vazia;
3. fixture de acesso controlado, WAF, captcha, login ou sessao expirada;
4. fixture de documento/inteiro teor quando houver acesso publico limpo;
5. teste de ID estavel e datas canonicas;
6. teste de parser contra mudanca de contrato.

Criterio de saida:

- cada provider textual maduro tem teste offline cobrindo sucesso, vazio e
  falha esperada;
- nenhum timeout, 403 ou captcha e tratado como zero resultado;
- documentos preservam hash, tamanho, content type e access status.

Status: baseline implementado; a cobertura deve continuar provider por provider
sem promover uma fonte apenas por possuir um parser.

## Onda 2C - Evidencia E Qualidade Operacional

Status: proxima frente de maior ganho.

Escopo:

1. registrar cada rodada live em JSON e Markdown derivados;
2. separar `live_status` de score documental e de contrato offline;
3. transformar a fila generica em proxima acao verificavel por provider;
4. fechar fixtures e testes dos providers textuais de maior impacto;
5. refletir falhas de qualidade, paginacao, identidade e inteiro teor no
   catalogo, Studio e MCP.

Criterio de saida:

- toda afirmacao de disponibilidade live aponta para evidencia datada;
- resultado vazio, bloqueio, indisponibilidade e contrato alterado possuem
  estados diferentes;
- nenhum provider e promovido sem fixture, teste e criterio de aceite;
- o Studio e o MCP exibem a mesma leitura operacional do catalogo.

## Onda 3 - Busca Unificada Profissional

Escopo:

- camada federada usada por Python SDK, CLI, MCP e Studio.

Trabalho:

1. separar `federated_search` de busca paginada global;
2. criar semantica explicita para `searched_sources`, `skipped_sources` e
   `errors`;
3. deduplicar por identificador estavel;
4. ordenar por score de fonte, data, relevancia e completude;
5. aplicar concorrencia limitada e deadline global;
6. validar filtros desconhecidos e datas antes da chamada.

Criterio de saida:

- o usuario entende quais fontes foram chamadas e por que outras foram puladas;
- `page_size` da busca unificada significa limite global ou declara claramente
  que e limite por fonte;
- erros previsiveis ficam visiveis sem derrubar toda a consulta;
- bugs inesperados nao sao mascarados como indisponibilidade normal.

## Onda 4 - Studio E Experiencia De Pesquisa

Escopo:

- interface de pesquisa unificada para advogado, jurimetrista, dev e agente.

Trabalho:

1. exibir fonte, status, score, campos retornados e limites por resultado;
2. criar filtros guiados por capacidade real dos providers;
3. diferenciar jurisprudencia textual, precedente, informativo e contexto;
4. apresentar ementa, inteiro teor, trace e raw controlado;
5. mostrar erro por fonte de forma acionavel;
6. rodar Playwright para UX, acessibilidade, responsividade e regressao visual.

Criterio de saida:

- busca com termo juridico retorna tela compreensivel mesmo com falhas parciais;
- advogado consegue ler e exportar resultados;
- jurimetrista consegue avaliar completude antes de coletar;
- agente de IA consegue interpretar a resposta sem baixar PDF manualmente.

## Onda 5 - Expansao Nacional

Escopo:

- candidatos sem codigo e providers de alto valor ainda superficiais.

Trabalho:

1. priorizar fontes com API JSON, Solr, GraphQL ou HTML estavel;
2. documentar contrato completo antes do codigo;
3. promover candidato somente com rota reproduzida e fixture minima;
4. evitar duplicar fontes que pertencem ao NanoJud;
5. manter mapa Brasil por tribunal, orgao e tipo de conteudo.

Criterio de saida:

- cada novo provider nasce com dossie, fixture, teste e capabilities;
- nenhuma fonte entra na busca unificada sem papel textual claro;
- o catalogo mostra cobertura nacional real, lacunas e proxima acao.

## Ordem Recomendada

1. executar Onda 2C com evidencias e contratos dos providers de maior impacto;
2. corrigir qualidade de identidade, datas, paginacao e documento antes de
   ampliar a quantidade de fontes;
3. amadurecer `tjsp_eproc_jurisprudencia` e a familia CJSG/e-SAJ;
4. rever a busca unificada com base nos estados reais de cada fonte;
5. so entao expandir para novos candidatos com contrato completo.

## Definicao De Pronto

Uma fonte esta pronta para liderar pesquisa jurimetrica quando:

- possui provider runtime;
- participa da busca unificada de forma opt-in;
- aceita termo textual;
- retorna `CanonicalDecision` ou equivalente textual;
- preserva trace, URL e campos brutos relevantes;
- diferencia sucesso, vazio, bloqueio e indisponibilidade;
- possui fixtures de sucesso/vazio/falha;
- tem dossie sem lacunas estruturais;
- possui score A ou B alto;
- foi validada em live opt-in recente ou declara claramente o bloqueio externo.
