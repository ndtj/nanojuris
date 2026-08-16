# Auditoria profissional de uso real

**Data:** 2026-08-16
**Escopo:** Studio, CLI, MCP, SDK, exportações, armazenamento e documentação de fontes
**Objetivo:** simular a primeira utilização do NanoJuris por profissionais que não conhecem o sistema e transformar os achados em um plano incremental verificável.

## Conclusão executiva

O NanoJuris apresenta uma base funcional sólida para uma primeira versão profissional:

- a consulta real ao TJDFT retornou resultados jurisprudenciais estruturados;
- a busca unificada via MCP preservou a distinção entre resultados parciais e coleção completa;
- a saída pode ser canonicalizada, exportada e persistida em SQLite;
- a suíte de browser do Studio passou integralmente;
- bloqueios e timeouts observados na validação live não foram convertidos em resultado vazio.

Não foi identificado um defeito P0 de integridade nesta rodada. Foram identificados, porém, riscos P1 que impedem chamar a experiência de pronta para pesquisa jurídica ou jurimetria sem ressalvas: a camada Studio perde parte dos metadados de completude disponíveis no núcleo/MCP, a proveniência HTTP de alguns resultados live permanece incompleta e a interface mistura catálogo, providers runtime e fontes selecionadas.

**Avaliação desta rodada:**

| Dimensão | Resultado | Leitura |
| --- | ---: | --- |
| Funcionalidade básica | 8/10 | Consulta, normalização, exportação e armazenamento funcionam no fluxo validado |
| Transparência da coleta | 6/10 | MCP é claro; Studio e alguns traces ainda omitem contexto importante |
| UX para advogado | 7/10 | Busca simples e resultado legível, mas faltam sinais mais fortes de completude e inteiro teor |
| UX para jurimetrista | 7/10 | Exportação e SQLite existem; evidência por rodada ainda não é uma jornada única |
| UX para analista de dados | 7/10 | Modelo canônico é útil; qualidade e semântica dos campos precisam aparecer na saída |
| Prontidão para agentes | 8/10 | MCP expõe estados de completude, contratos e fontes; Studio ainda não tem paridade |
| QA automatizado | 8/10 | E2E determinístico e suíte ampla; falta uma camada live opt-in persistida |

## Personas e jornadas testadas

### Advogado: localizar precedente utilizável

**Jornada:** instalar/importar o cliente, pesquisar `responsabilidade civil`, ler ementa, identificar tribunal, número, relator e acessar o documento.

**Resultado:** aprovada no TJDFT. Foram retornados dois resultados reais, com número de processo, tribunal, relator, situação, resumo/ementa e URL de documento. A busca não retornou `full_text`; o dado bruto indicou uma opção de download do inteiro teor no PJe.

**Risco:** a UI precisa dizer claramente “ementa disponível” e “inteiro teor não carregado/verificado”, em vez de deixar o usuário inferir isso a partir de um campo vazio.

### Jurimetrista: construir uma amostra reproduzível

**Jornada:** executar busca, verificar total remoto, canonicalizar, exportar CSV/JSONL e persistir registros em SQLite.

**Resultado:** aprovada no fluxo real TJDFT:

- 2 resultados coletados;
- 131.875 resultados informados pela fonte;
- 2 registros canonicalizados;
- 2 linhas JSONL canonical;
- 3 linhas CSV incluindo cabeçalho;
- 2 registros persistidos no SQLite;
- estatísticas por tipo e fonte disponíveis.

**Risco:** o fluxo ainda exige conhecimento de várias APIs. A jornada deveria produzir um artefato de pesquisa com consulta, parâmetros, fonte, horário, completude, falhas e hashes sem exigir composição manual pelo pesquisador.

### Analista de dados: comparar fontes

**Jornada:** executar uma busca em mais de um tribunal, comparar totais, quantidade coletada e qualidade dos dados.

**Resultado:** aprovada via MCP com TJDFT e TST. A resposta informou `total_available=4`, `total_returned=2`, `deduplicated_total=4`, ambas as fontes como `sources_partial`, `collection_complete=false` e nenhum erro.

**Risco:** a mesma riqueza semântica não está completa no retorno do Studio. A API web deve carregar os mesmos campos federados para evitar que uma interface apresente uma coleta parcial como se fosse uma pesquisa nacional completa.

### Desenvolvedor: descobrir o contrato de uma fonte

**Jornada:** listar fontes, consultar o contrato de `tjdf_juris`, descobrir maturidade, risco e prontidão para agentes.

**Resultado:** aprovada. O MCP reportou 37 fontes runtime e o contrato do TJDFT como nível 5, baixo risco, sem lacunas abertas e pronto para agentes.

**Risco:** a nomenclatura do catálogo precisa distinguir explicitamente “fonte catalogada”, “provider runtime”, “fonte recomendada” e “fonte selecionada”.

### Agente de IA: pesquisar sem inventar completude

**Jornada:** consultar fontes, interpretar estado da coleta, decidir se pode responder ou deve informar limitação.

**Resultado:** aprovada no MCP. A resposta inclui fontes pesquisadas, fontes parciais, `collection_complete`, motivo de completude e erros.

**Risco:** o Studio e a CLI ainda não oferecem a mesma superfície de evidência de forma igualmente visível. Um agente que consuma a API web pode receber menos contexto que um agente que use MCP.

## Matriz de evidências executadas

| Área | Cenário | Evidência | Resultado |
| --- | --- | --- | --- |
| Browser/Studio | Carregamento e busca | `pytest tests/e2e` | 9 passed |
| Browser/Studio | Falhas parciais, filtros, validação, vazio, detalhe, mobile e teclado | Suíte E2E | 9/9 cenários passaram |
| SDK live | Busca TJDFT por `responsabilidade civil` | `tjdf_juris` | 2 resultados; total remoto 131.875 |
| CLI live | Busca JSON | `nanojuris buscar ... --formato json` | 2 resultados estruturados |
| Saúde live | TJDFT, TST e TCU | `nanojuris saude` | TJDFT/TST healthy; TCU timeout classificado como error |
| Validação live | TJDFT | `source_validation_tool` | valid; coleta parcial explicitada |
| MCP | Catálogo e contrato | `list_sources_tool`, `source_contracts_tool` | 37 fontes runtime; contrato TJDFT nível 5 |
| MCP | Pesquisa federada | `search_unified_tool` | parcial explícita; sem erro mascarado |
| Exportação | CSV e JSONL canonical | SDK | contagens coerentes com a busca |
| Armazenamento | SQLite | `SQLiteStore` | 2 registros e estatísticas por fonte/tipo |
| Suíte Python | Regressão completa | `pytest -q` | 567 passed, 5 skipped |
| Qualidade estática | Ruff | `ruff check`, `ruff format --check` | aprovado |

Os cinco skips são validações live opt-in de fontes externas, não falhas da suíte offline. A disponibilidade de tribunais deve continuar sendo tratada como evidência temporal, e não como propriedade permanente do código.

## Evidência visual do Studio

As imagens abaixo foram geradas pela auditoria E2E existente:

- [Studio desktop inicial](../../artifacts/studio/qa-real-final-initial-desktop.png)
- [Studio mobile inicial](../../artifacts/studio/qa-real-final-initial-mobile.png)
- [Studio desktop de validação](../../artifacts/studio/qa-real-final-validation-desktop.png)

### Pontos positivos

- composição “terminal/aurora” coerente com um produto técnico;
- contraste suficiente para leitura;
- catálogo de fontes e resultados organizados em áreas previsíveis;
- layout mobile sem overflow horizontal no viewport testado;
- busca, validação, expansão, cópia, payload bruto e documento acessíveis por teclado nos cenários cobertos.

### Pontos a melhorar

- o cabeçalho comunica `7 estáveis`, `34 recomendadas` e `40 catalogadas`, enquanto a API de produção reporta 37 providers runtime; a diferença é defensável, mas não está explicada no momento da decisão;
- a seleção `7/40` pode ser interpretada como sete providers realmente disponíveis, embora o catálogo também contenha candidatos e fontes de contexto;
- a área de validação é informativa, porém densa para um advogado: estado, completude, fonte e ação recomendada deveriam ter hierarquia visual mais forte;
- identificadores técnicos são úteis para desenvolvedores, mas precisam coexistir com nome institucional, tipo de conteúdo e recomendação de uso;
- o estado “ementa disponível / inteiro teor não verificado / documento disponível” deve ser visualmente distinto de “resultado sem texto”.

## Achados priorizados

### P1-01 — Studio perde metadados de completude federada

O núcleo de busca unificada e o MCP expõem `source_totals`, `source_completeness`, `sources_complete`, `sources_partial`, `sources_unknown`, `collection_complete`, `completeness_reason` e `deduplicated_total`. A resposta atual do Studio reduz esse contrato a campos como `total`, `sources`, `source_status` e `errors`.

**Impacto:** uma pesquisa parcial pode ser visualmente entendida como completa, especialmente por um usuário que não conhece a diferença entre janela coletada e total remoto.

**Critério de aceite:** o endpoint web e a UI devem mostrar a mesma informação de completude do MCP, incluindo total remoto por fonte, quantidade coletada, motivo de parcialidade e deduplicação.

### P1-02 — Taxonomia de catálogo não é suficientemente explícita

A API de produção reporta 37 providers runtime, 7 fontes padrão e 34 recomendadas. O Studio exibe 40 entradas catalogadas. O catálogo reúne providers, candidatos e fontes de contexto em uma mesma experiência.

**Impacto:** o usuário pode confundir cobertura documental com cobertura efetivamente pesquisável.

**Critério de aceite:** cada entrada deve exibir, no mínimo, `runtime`, `catalogada`, `recomendada`, `candidata`, `fora do escopo` e `selecionável`; contadores devem ter rótulos sem ambiguidade.

### P1-03 — Proveniência HTTP incompleta no resultado live

Na validação TJDFT, a execução reportou resultado válido e tempo de resposta, mas `http_status`, `retrieval_status`, `content_type`, `content_sha256` e `response_bytes` permaneceram nulos no trace observado.

**Impacto:** o usuário consegue saber que houve resultado, mas não consegue auditar completamente a resposta HTTP que o originou.

**Critério de aceite:** o transporte compartilhado ou os providers devem propagar os metadados disponíveis sem inventar valores; quando a camada não observar um campo, deve registrar `not_observed` ou ausência documentada, não silêncio semântico.

### P1-04 — Inteiro teor e ementa não são diferenciados com força suficiente

A consulta TJDFT retornou resumo/ementa e uma referência de download, mas `full_text` não foi carregado na busca.

**Impacto:** em produção de peças, o usuário pode considerar que já possui o inteiro teor quando possui apenas o espelho da decisão e uma URL para documento.

**Critério de aceite:** cada resultado deve distinguir `summary_status`, `full_text_status`, `document_url_status` e `document_access_status`, com valores explícitos como `available`, `not_loaded`, `not_verified`, `unavailable` ou `blocked`.

### P1-05 — Latência de fonte indisponível é longa para uma jornada profissional

Na execução de saúde, o TCU terminou como `error` por timeout de leitura após aproximadamente 44,7 segundos, sem ser convertido em vazio.

**Impacto:** a classificação está correta, mas uma federação com várias fontes pode ficar lenta demais para uso interativo.

**Critério de aceite:** existir deadline global, timeout por fonte visível, concorrência limitada e estado de circuito/indisponibilidade documentado, preservando a distinção entre erro e vazio.

### P2-01 — Evidência live ainda não é uma jornada única para o pesquisador

A CLI e o MCP conseguem validar fontes, mas o usuário precisa conhecer interfaces distintas para obter consulta, artefato, exportação e persistência.

**Critério de aceite:** uma operação de pesquisa reproduzível deve gerar um manifesto com consulta, fontes, parâmetros, horários, resultados, falhas, completude e hashes, reutilizável por humanos e agentes.

### P2-02 — E2E é determinístico, mas não há uma camada live de browser equivalente

Os 9 cenários Playwright usam fixtures controladas, o que é correto para regressão. Ainda falta uma execução live opt-in que valide a integração do navegador com o backend real e produza artefatos sem tornar o CI dependente de tribunais.

**Critério de aceite:** workflow manual ou local separado, com fontes estáveis selecionadas, timeout controlado, artefato JSON/Markdown e screenshots, sem bloquear o CI offline.

### P2-03 — Comando `saude` exige descoberta documental

O CLI usa `saude`; um usuário que tente o termo comum `health` recebe erro de comando desconhecido.

**Critério de aceite:** o quickstart deve apresentar um mapa de comandos por objetivo, ou o CLI deve oferecer uma mensagem de descoberta clara. Qualquer alias deve ser uma decisão explícita de compatibilidade.

### P3-01 — Falta um painel de qualidade por campo para jurimetria

O catálogo informa capacidades, mas a experiência ainda não resume sistematicamente completude de resumo, datas, relator, identidade, inteiro teor e duplicidade por fonte.

**Critério de aceite:** cada provider deve possuir um perfil de qualidade observável, separado de disponibilidade live.

## Plano incremental recomendado

### Onda QA-0 — Transparência do contrato federado

**Objetivo:** levar para Studio e CLI a mesma semântica já disponível no núcleo/MCP.

1. ampliar o payload de `studio_search` com os campos federados;
2. exibir total remoto, coletado, deduplicado e motivo de parcialidade;
3. separar estado por fonte: `success`, `empty`, `partial`, `blocked`, `rate_limited`, `timeout`, `unavailable`, `contract_changed`;
4. criar testes API e Playwright para cada estado;
5. revisar textos para advogado e agente.

**Saída:** nenhum consumidor precisa inferir completude olhando apenas o número de resultados.

### Onda QA-1 — Proveniência e qualidade observável

1. mapear quais providers populam trace HTTP;
2. centralizar aquisição quando compatível com os contratos existentes;
3. propagar status de acesso e extração até CLI, Studio, canonical e MCP;
4. diferenciar `summary`, `full_text`, `document_url` e documento validado;
5. adicionar testes de ausência honesta e não de valores inventados.

**Saída:** cada campo relevante informa origem, estado e grau de observação.

### Onda QA-2 — Jornada de pesquisa reproduzível

1. criar comando ou fluxo de “executar pesquisa” com manifesto;
2. persistir consulta, filtros, fontes, versões, horários, latência, falhas e hashes;
3. permitir exportação canonical JSONL/CSV e relatório humano no mesmo run;
4. integrar o manifesto ao SQLite, Studio e MCP;
5. documentar a jornada para advogado, jurimetrista e analista.

**Saída:** uma pesquisa pode ser reaberta, auditada e comparada sem reconstrução manual.

### Onda QA-3 — Validação live controlada

1. manter CI offline determinístico;
2. criar workflow manual para smoke live;
3. executar apenas fontes públicas selecionadas e respeitar seus limites;
4. armazenar artefatos por timestamp;
5. atualizar catálogo somente a partir de evidência estruturada;
6. separar falha de origem, rede local, TLS e parser.

**Saída:** disponibilidade é histórica e observável, sem contaminar a suíte de regressão.

### Onda QA-4 — UX profissional por objetivo

Adicionar presets e linguagem orientada à tarefa, sem esconder o modo avançado:

| Perfil | Entrada principal | Saída prioritária |
| --- | --- | --- |
| Advogado | tema, tribunal, período, tipo de decisão | ementa, inteiro teor, citação, fonte |
| Jurimetrista | termo, fontes, período, paginação | dataset, completude, deduplicação, manifesto |
| Analista | filtros e campos | CSV/JSONL, esquema, qualidade, estatísticas |
| Desenvolvedor | provider e contrato | payload, trace, erro, fixture |
| Agente de IA | intenção estruturada | resultados, limitações, proveniência, ações seguintes |

**Saída:** a mesma infraestrutura atende públicos diferentes sem criar produtos divergentes.

## Critérios de saída da auditoria

O próximo ciclo poderá ser considerado concluído quando:

- Studio, CLI e MCP expuserem a mesma semântica de completude;
- catálogo e runtime tiverem contadores explicados;
- nenhum bloqueio, timeout ou falha aparecer como vazio;
- traces registrarem os metadados HTTP observados;
- ementa, inteiro teor e documento forem estados distintos;
- existir manifesto de pesquisa reproduzível;
- houver testes offline para todos os estados novos;
- houver uma validação live opt-in com artefato versionável;
- a documentação de cada provider refletir os estados reais;
- a suíte offline continuar verde.

## Estado do repositório

### Implementação desta rodada

As primeiras ondas do plano foram aplicadas incrementalmente:

- **QA-0:** o Studio agora preserva total remoto, total coletado,
  deduplicação, completude por fonte, motivo da parcialidade e estados de vazio,
  falha e fonte pulada;
- **QA-1:** os providers TJDFT e TST propagam no `SourceTrace` os fatos HTTP
  observados, incluindo status, URL final, hash, bytes, latência e estado de
  recuperação;
- **QA-2:** o SDK oferece `search_many_and_store_run`, o MCP oferece
  `search_unified_store` e o CLI oferece `buscar-unificada`, todos preservando
  os metadados federados no `ResearchRun`;
- **QA-4 inicial:** o Studio diferencia resultados da coleta de uma afirmação de
  completude, e cada resultado informa o estado de ementa, documento/inteiro
  teor, acesso e extração quando observados.

As ondas de validação live ampla, perfil de qualidade por provider e refinamento
visual por público continuam como próximos ciclos. As alterações anteriores do
worktree foram preservadas e não foram commitadas nem publicadas. Este relatório
deve ser revisado junto com o conjunto atual de mudanças antes de qualquer
commit.
