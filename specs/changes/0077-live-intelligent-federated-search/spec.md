# 0077 — busca live inteligente e determinística

Status: `in_progress`
Owner: Search Architecture, Legal Data, Web Platform e QA
Data: `2026-09-07`

## Problema e intenção

A busca web atual consulta fontes públicas válidas, mas o ranking federado usa
contagem simples de palavras e a interface concatena lotes. Palavras genéricas,
ordem de chegada e concentração de uma fonte podem colocar resultados pouco
relacionados no topo. O produto precisa melhorar a relevância do top 10 sem
índice próprio, IA por consulta ou ocultação de falhas externas.

## Requisitos

- **REQ-001** — normalizar Unicode, acentos, caixa, pontuação e espaços,
  preservando a consulta original.
- **REQ-002** — distinguir comandos de pesquisa, termos jurídicos, frases,
  termos obrigatórios, opcionais e negativos.
- **REQ-003** — reconhecer com regras conservadoras número CNJ, tribunal,
  período, grau, ramo, tipo documental, classe, órgão, coleção e área jurídica.
- **REQ-004** — expandir conceitos apenas por vocabulário versionado,
  auditável e com peso inferior ao literal.
- **REQ-005** — inferência ambígua nunca deve restringir silenciosamente a
  consulta.
- **REQ-006** — selecionar por padrão entre 8 e 12 fontes públicas elegíveis,
  equilibrando capacidade, qualidade, saúde, latência, papel e diversidade.
- **REQ-007** — preservar modos `adaptive`, `selected` e `all`.
- **REQ-008** — representar o plano em até três ondas, orçamento global máximo
  de 240 candidatos e uma chamada normal por provider.
- **REQ-009** — compilar somente filtros comprovados no contrato do provider e
  registrar native, translated, local ou unsupported.
- **REQ-010** — classificar por fonte `success_with_results`,
  `authoritative_empty`, `unconfirmed_empty`, `timeout`, `access_blocked`,
  `rate_limited`, `transport_error`, `schema_invalid`, `partial` ou `cancelled`.
- **REQ-011** — erro, bloqueio ou resposta inválida nunca pode virar vazio
  autoritativo.
- **REQ-012** — calcular relevância absoluta e comparável com sinais lexicais,
  jurídicos, estruturais e de qualidade.
- **REQ-013** — identificador exato deve dominar qualquer correspondência
  temática.
- **REQ-014** — incorporar posição nativa somente como sinal por rank, sem
  comparar score remoto.
- **REQ-015** — penalizar termo genérico isolado, baixa cobertura, conflito de
  tipo/grau, texto precário e fonte contextual inadequada.
- **REQ-016** — deduplicar identificadores exatos e agrupar equivalências
  aproximadas de forma conservadora, preservando versões jurídicas distintas.
- **REQ-017** — diversificar apenas resultados de relevância próxima, sem quota
  rígida por tribunal.
- **REQ-018** — cada resultado deve expor score, versão, termos/conceitos
  encontrados, até três razões, rank nativo e grupo de duplicidade.
- **REQ-019** — a interface deve incorporar ondas concluídas e reranquear o
  conjunto enquanto não houver interação.
- **REQ-020** — após clique, foco intencional, seleção, abertura do leitor ou
  rolagem significativa, a ordem deve congelar e oferecer atualização manual.
- **REQ-021** — exibir chips removíveis de intenção, estados das fontes,
  progresso, parcialidade e filtros não suportados.
- **REQ-022** — cache permitido deve ser efêmero, não pesquisável, versionado e
  com TTL entre 5 e 15 minutos.
- **REQ-023** — telemetria, quando habilitada, deve ser agregada, sem consulta
  em claro, identidade, inteiro teor ou IP analítico, com retenção de 30 dias.
- **REQ-024** — a nova busca deve permanecer atrás de feature flag, com shadow
  mode e rollback por versão.
- **REQ-025** — contratos existentes de SDK, CLI, MCP, Studio e API devem
  permanecer compatíveis por extensão aditiva.
- **REQ-026** — nenhum código do fluxo pode chamar LLM, embedding, vector DB ou
  serviço de reranking.

## Comportamento esperado

### Cenário A — tema com comando documental

- Dado `acórdãos sobre divórcio`.
- Quando a consulta for analisada.
- Então `acórdãos` será intenção de tipo documental, `divórcio` será o tema e
  “sobre” não pontuará.
- E acórdãos de segundo grau com divórcio na ementa superarão itens que apenas
  mencionem palavra periférica.

### Cenário B — conceitos compostos

- Dado `responsabilidade civil administrativa`.
- Quando candidatos forem ranqueados.
- Então frase, bigramas e cobertura dos conceitos terão peso superior a uma
  ocorrência isolada de “civil”.

### Cenário C — número CNJ

- Dado um número CNJ válido.
- Quando fontes compatíveis responderem.
- Então a correspondência integral ficará em primeiro e não haverá expansão
  temática.

### Cenário D — fonte bloqueada

- Dado que uma fonte responda 403, CAPTCHA ou controle de acesso.
- Quando a onda for consolidada.
- Então a fonte aparecerá como `access_blocked`, sem resultados sintéticos e
  sem reduzir a busca inteira a erro.

### Cenário E — chegada progressiva

- Dado que a primeira onda já tenha resultados.
- Quando uma onda posterior concluir.
- Então todos os candidatos serão reranqueados em conjunto.
- E, se o usuário já interagiu, a lista permanecerá fixa até ele confirmar a
  atualização.

## Falhas e limites

| Situação | Resultado obrigatório | Evidência |
| --- | --- | --- |
| Timeout do provider | `timeout`, resultado parcial preservado | duração, provider e trace redigido |
| HTTP 403/CAPTCHA/login | `access_blocked` | status e classificação, sem token/cookie |
| HTTP 429 | `rate_limited`, sem retry agressivo | retry-after sanitizado |
| TLS/rede | `transport_error` | classe segura e endpoint lógico |
| Schema mudou | `schema_invalid` | versão do parser e fingerprint |
| Página vazia comprovada | `authoritative_empty` | total conhecido ou contrato explícito |
| Página vazia ambígua | `unconfirmed_empty` | razão de incompletude |
| Mais de 240 candidatos | truncar de forma determinística e declarar parcialidade | contagens antes/depois |
| Fonte lenta após freeze | incorporar em buffer e oferecer atualização | número de resultados pendentes |

## Critérios de aceite

- **AC-001** — exemplos dourados de normalização e intenção passam integralmente.
- **AC-002** — inferências ambíguas aparecem como sugestão, não filtro ativo.
- **AC-003** — adaptive seleciona 8–12 fontes e produz até três ondas estáveis.
- **AC-004** — nenhum provider recebe filtro `unsupported` ou `unverified`.
- **AC-005** — existe um outcome terminal para toda fonte solicitada.
- **AC-006** — falhas externas não são convertidas em vazio.
- **AC-007** — identificador exato obtém success@1 de 100%.
- **AC-008** — grau e tipo documental explícitos têm precisão de 100%.
- **AC-009** — ranking final independe da ordem de chegada dos candidatos.
- **AC-010** — uma única onda e várias ondas produzem a mesma ordem final.
- **AC-011** — deduplicação não funde retificação ou versão distinta sem prova.
- **AC-012** — razões correspondem a sinais realmente observados.
- **AC-013** — interface congela após interação e preserva foco, leitor e scroll.
- **AC-014** — busca all continua disponível e progressiva.
- **AC-015** — API antiga funciona sem informar `mode` ou `ranking_version`.
- **AC-016** — nenhum dado proibido cruza a projeção pública ou telemetria.
- **AC-017** — nDCG@10 melhora pelo menos 25% relativamente ao baseline.
- **AC-018** — irrelevantes no top 5 caem pelo menos 50% e ficam em até 10%.
- **AC-019** — rankear 240 candidatos consome menos de 150 ms no p95.
- **AC-020** — busca comum faz no máximo uma chamada por provider.
- **AC-021** — nenhum teste existente regride.
- **AC-022** — Ruff, format-check, mypy, compileall e SDD passam.
- **AC-023** — smokes bounded cobrem as consultas obrigatórias e CNJ exato.
- **AC-024** — feature flag e rollback restauram o ranking anterior sem deploy de
  código adicional.

## Fora de escopo

- índice próprio, crawler nacional ou corpus persistido;
- embeddings, vector database, LLM e modelos pagos;
- aconselhamento jurídico ou geração de teses;
- burlar proteção de fonte;
- promover providers ainda não aptos;
- commit, push, release, OCI/Terraform apply ou deploy.

## Riscos

- Precisão melhora apenas dentro dos candidatos recuperados pelas fontes.
- Vocabulário amplo demais pode introduzir falso positivo.
- Reordenação contínua pode causar instabilidade antes do freeze.
- Latência externa pode impedir metas de experiência mesmo com ranking rápido.
- Benchmark pequeno pode superajustar pesos; deve conter holdout.
