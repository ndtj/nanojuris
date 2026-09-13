# Verificação

## Resultados

- `python tools/run_cjsg_live_smoke.py --output docs/provider-discovery/cjsg-live-legitimate-recheck-20260906.json --text "responsabilidade civil" --page-size 1`
  — 7/7 buscas bounded válidas; TJCE total 107086, TJPE registro textual,
  TJSP total 2741745; quatro detalhes públicos e três detalhes e-SAJ exigindo
  controle adicional.
- TJAP: HTML `Just a moment...`/Turnstile e envelope de aplicação sem token;
  classificado `access_controlled`.
- TJMA: catálogos oficiais públicos; busca de acórdãos exige CAPTCHA
  server-side; classificado `access_controlled`.
- TJAP: uma tentativa bounded adicional no host alternativo documentado
  (`services.tjap.jus.br`) falhou por resolucao DNS; o host oficial
  `tucujuris.tjap.jus.br` respondeu HTTP 403 Cloudflare `Cf-Mitigated:
  challenge`. Nenhuma cookie ou token de desafio foi persistido.
- TJSP: a busca continua reproduzivel em consulta bounded (1 ementa, total
  2741747) e o detalhe conhecido foi recuperado pelo fluxo publico
  `getArquivo.do?cdAcordao=14138012&cdForo=0&casChecked=true`, HTTP 200,
  PDF de 442374 bytes e extracao completa. Evidencia:
  `docs/provider-discovery/tjsp-cjsg-detail-continuation-live-20260907.json`.
- Uma sessao Chromium limpa, sem cookies importados, proxy, stealth ou
  resolucao de desafios, revalidou TJAP, TJTO, STJ, STF, TJRN, TJCE, TJSE,
  CJF e TJMG. Os hosts protegidos continuaram em 403/challenge; os formularios
  TJCE/TJSE voltaram ao CAPTCHA no envio normal; o indice CJF nao expôs rota
  adicional de resultados. Evidencia redigida:
  `docs/provider-discovery/blocked-browser-session-recheck-20260907.json`.
- As alternativas oficiais do TJAP tambem foram verificadas: o portal de
  sumulas retornou HTTP 200, mas somente sumulas; a busca do portal antigo
  retornou HTTP 200, mas apenas conteudo institucional; e a entrada oficial do
  Diario da Justica retornou HTTP 403. Nenhuma delas fornece uma busca geral
  CJSG reproduzivel sem o limite do Tucujuris. Evidencia:
  `docs/provider-discovery/tjap-repository-alternatives-live-20260907.json`.
- O shell publico do TJMA tambem foi inspecionado sem executar desafio: o
  catalogo distingue explicitamente CJSG (acordaos e decisoes monocraticas),
  CJPG (sentencas) e filtros de ``Inteiro Teor``. As rotas de resultados
  retornaram ``captcha_required`` e nao foram promovidas nem tratadas como
  vazias. Evidencia:
  `docs/provider-discovery/tjma-public-route-inventory-live-20260907.json`.
- A auditoria local de `C:\Users\admin\Downloads\lib template` encontrou
  componentes aproveitaveis apenas para navegacao publica normal, observacao
  de rede redigida, parsing CSS/XPath e pooling bounded. Fingerprint spoofing,
  stealth, solver de desafio, rotacao de proxy, replay de cookies e alteracao
  de TLS foram explicitamente classificados como nao aplicaveis. Evidencia:
  `docs/provider-discovery/lib-template-technique-audit-20260907.json`.
- As superficies oficiais adicionais foram rechecadas com GETs normais: o PJe
  2G do TJAP e uma consulta processual, o portal de sumulas do TJAP e uma
  colecao especializada, e o bundle/portal do JurisConsult do TJMA confirma a
  aplicacao e o limite de desafio sem expor uma rota de resultados sem token.
  Nenhuma dessas rotas foi promovida como jurisprudencia geral. Evidencia:
  `docs/provider-discovery/official-alternative-surface-recheck-20260907.json`.
- `python -m pytest -q tests/test_cjsg_live_smoke.py tests/test_tjce_cjsg.py tests/test_tjsp_cjsg.py`
  — aprovado após a inclusão do escopo canônico CJSG nos resultados e-SAJ.
- Nenhum commit, push, publicação ou deploy foi executado.

## Rastreabilidade

| Requisito | Evidência |
|---|---|
| REQ-001 | envelope `cjsg-live-legitimate-recheck-20260906.json` |
| REQ-002 | `run_cjsg_live_smoke.py` reutiliza sessões e transporte dos providers |
| REQ-003 | classificações `access_blocked` preservadas para TJAP/TJMA |
| REQ-004 | teste focado e validação SDD |
