# Especificação de mudança

ID: `0002-provider-discovery`
Status: `accepted`
Owner: `NanoJuris engineering`
Data: `2026-08-20`

## Problema e intenção

A descoberta de providers dinâmicos exige identificar rotas, métodos, payloads,
paginação, links de inteiro teor, sinais de acesso e campos candidatos. O
`route_probe` atual cobre HTTP de forma segura, mas não observa páginas que
dependem de JavaScript nem oferece um pacote de evidências e artefatos SDD.

## Objetivos

- criar um modelo de evidência reproduzível para descoberta;
- ampliar a descoberta para links, formulários, scripts e respostas XHR;
- oferecer navegador Playwright opcional, sem dependência de produção;
- aplicar allowlist, limites, timeout, redirects controlados e replay;
- sugerir seletores e rotas sem promovê-los automaticamente;
- gerar rascunhos SDD a partir da execução;
- manter compatibilidade com `SourceTrace` e `ExtractionTrace`;
- cobrir sucesso, vazio, bloqueio, timeout, indisponibilidade e mudança.

## Fora de escopo

- criar ou alterar provider automaticamente;
- editar catálogo gerado;
- bypass de CAPTCHA, WAF, login, rate limit ou controle de acesso;
- uso de dados autenticados, segredos, proxies ou perfis pessoais;
- crawling ilimitado ou execução em produção;
- substituir `route_probe.py` ou os providers existentes.

## Atores e contexto

- Usuário: inicia uma descoberta bounded e revisa o resultado.
- Agente: executa coleta, organiza evidências e gera rascunho.
- Sistema externo: fonte pública oficial permitida.
- Provider: implementação futura derivada do rascunho aprovado.

## Requisitos funcionais

### RF-001 — Descoberta HTTP

O sistema deve consultar uma URL permitida, capturar status, headers
redigidos, URL final, redirects, tipo de conteúdo, bytes, hash e duração.

### RF-002 — Descoberta de rotas

O sistema deve extrair links, actions de formulários, scripts e referências de
endpoint de uma resposta HTML ou JSON, normalizando URLs e removendo duplicatas.

### RF-003 — Descoberta dinâmica

Quando Playwright estiver disponível, o sistema deve observar a navegação e
respostas `document`, `xhr` e `fetch`, registrando método, URL, payload
redigido, status, headers, corpo limitado e hash.

### RF-004 — Política bounded

Toda execução deve aplicar allowlist de domínios, limite de páginas, bytes,
profundidade, respostas, redirects, timeout e intervalo entre requisições.

### RF-005 — Classificação

Cada observação deve ser classificada sem converter bloqueio, timeout, erro TLS,
indisponibilidade ou mudança em `empty`.

### RF-006 — Candidatos de extração

O sistema pode sugerir campos e seletores, indicando confiança, quantidade de
matches e evidência, mas não pode modificar parser oficial.

### RF-007 — Artefatos SDD

O sistema deve gerar relatório JSON e rascunhos de pesquisa, especificação,
design, tarefas, verificação, rastreabilidade e threat model.

### RF-008 — Replay

Uma resposta capturada deve poder ser reanalisada offline pelo hash, sem nova
consulta à fonte.

### RF-009 — Continuidade observável

Uma observação de controle de acesso não deve interromper a execução de outras
rotas permitidas. Ela deve ser registrada com estado explícito e seguir para a
revisão, sem ser apresentada como resultado vazio.

### RF-010 — Interfaces de operação

A capacidade de discovery deve estar disponível pelo CLI principal e por uma
ferramenta MCP, retornando métricas e referências aos artefatos gerados.

## Cenários de aceite

### Cenário: página pública com links legais

- Dado: uma página HTML pública com links de busca, detalhes e PDF;
- Quando: a descoberta é executada com o domínio permitido;
- Então: a evidência é `public`, os links são candidatos e o relatório contém
  hash, status, conteúdo e recomendações.

### Cenário: endpoint dinâmico

- Dado: uma página que dispara uma chamada XHR pública;
- Quando: o modo Playwright opcional é usado;
- Então: a chamada aparece com método, URL, payload redigido, status e hash.

### Cenário: controle de acesso

- Dado: CAPTCHA, WAF, login ou resposta 401/403;
- Quando: a fonte é observada;
- Então: o estado é `access_controlled` ou equivalente e nenhum retry de bypass
  é executado.

### Cenário: replay

- Dado: um envelope persistido;
- Quando: o relatório é reprocessado offline;
- Então: a classificação e os candidatos são reproduzidos sem rede.

## Critérios de aceite

- `AC-001` - O módulo HTTP passa testes sem rede.
- `AC-002` - URLs fora da allowlist são rejeitadas antes da requisição.
- `AC-003` - Redirections fora da allowlist são interrompidos.
- `AC-004` - Respostas têm hash e limite de bytes.
- `AC-005` - Estados operacionais têm classificação explícita.
- `AC-006` - HTML, formulário, script, JSON e XHR produzem candidatos.
- `AC-007` - O modo browser é opcional e falha com mensagem acionável sem Playwright.
- `AC-008` - O replay não acessa a rede.
- `AC-009` - O relatório gera rastreabilidade para a evidência.
- `AC-010` - Lint, tipos, testes e validações SDD passam.
- `AC-011` - Uma observação de acesso controlado não impede a análise de outras rotas permitidas.
- `AC-012` - CLI e MCP expõem discovery sem duplicar o contrato de evidência.

## Riscos e questões em aberto

- Respostas de terceiros podem conter dados pessoais; o relatório deve minimizar
  conteúdo e fixtures.
- A semântica de um seletor não é provada pela similaridade estrutural.
- O browser pode observar recursos externos; a política deve permitir somente
  hosts declarados.
