# `tjsp_eproc_jurisprudencia`

## Identidade

- Fonte oficial: Jurisprudencia eproc/TJSP.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_jurisprudencia_eproc`.
- URL inicial: `https://eproc-consulta.tjsp.jus.br/consulta_1g`.
- Status de acesso: publico parcial, com risco de controle de acesso.
- Status no NanoJuris: provider implementado.

## Contrato HTTP

- Rotas conhecidas:
  - `POST /externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados`
  - `GET /externo_controlador.php?acao=jurisprudencia@jurisprudencia/download_inteiro_teor&id_jurisprudencia=<id>`
- Parametros: texto integral, ementa/resumo, numero CNJ, intervalo de datas e
  origem.
- `source_origin`: aceita `colegio_recursal`, `primeiro_grau` e `segundo_grau`.
- Paginacao: o primeiro POST retorna `frmJurisprudenciaResultado` com
  `hdnPaginaAtual`, `hdnTotalResultado`, `selTamanhoPagina` (10, 25, 50 ou
  100) e `hdnUrlPaginar`. Paginas posteriores usam POST na rota AJAX indicada
  por `hdnUrlPaginar`, mantendo a sessao. A pagina 2 foi identificada na
  fixture, mas a reproducao live completa ainda depende da resposta publica da
  fonte. Ordenacao nao foi anunciada sem contrato reproduzido.

## Dados retornados

- Campos extraidos:
  - numero do processo;
  - tipo decisorio;
  - classe;
  - relator;
  - orgao julgador;
  - data de julgamento;
  - data de publicacao;
  - resumo/ementa;
  - URL do documento;
  - URL de inteiro teor;
  - `id_jurisprudencia`;
  - origem.
- Campos canonicos: `CanonicalDecision`.
- Inteiro teor: a rota e exposta por `get_document()` e carregada sob demanda.
  O adaptador preserva os bytes da resposta, `content_type`, tamanho, SHA-256 e
  trace de extracao. Uma URL ou card de resultado nao equivale a documento
  carregado; redirecionamento para controle de acesso continua sendo reportado
  explicitamente.

## Comportamento observado

- Rota publica descoberta e validada por requests limpo em 2026-08-02.
- Cards de resultado trazem texto decisorio.
- Inteiro teor separado pode exigir validacao.
- Mudancas de hash/layout/filtros devem ser esperadas.

## Fixtures

- [x] Busca por termo, frase exata, numero, datas, origem e tipo documental.
- [x] Documento HTML publico em fixture, incluindo bytes, tipo, tamanho, hash
  e trace de extracao.
- [x] Controle de acesso identificado sem bypass.
- [x] Resultado vazio coberto por fixture de contrato; uma página vazia real
  continua sendo estado válido quando a fonte o retornar.
- [x] Redirecionamento/controle de acesso de inteiro teor observado em chamada
  live recente e classificado explicitamente, sem bypass.

## MCP e agentes

- Quando usar: jurisprudencia eproc/TJSP por origem e texto.
- Quando pular: quando o usuario precisar de cobertura nacional completa ou de
  paginação remota comprovada.
- Mensagem segura: "O NanoJuris pode carregar o documento publico por demanda;
  confirme `access_status`, `extraction_status`, hash e tamanho antes de tratar
  o conteudo como inteiro teor utilizavel."
- Riscos: confundir texto do card com inteiro teor integral ou assumir que toda
  rota documental permanecera publica.

## Proximos passos

- [x] Aprofundar contrato de `source_origin`: `colegio_recursal`,
  `primeiro_grau` e `segundo_grau` são os valores aceitos e preservados.
- [x] Implementar carregamento documental com bytes, SHA-256 e trace.
- [x] Registrar validação live datada de documento e resposta vazia/controle de
  acesso no ciclo 63.
- [x] Documentar limites por primeiro grau, segundo grau e colégio recursal.
- [x] Criar dicionário dos filtros efetivamente aceitos; filtros avançados não
  enviados permanecem fora do contrato comum.

## Evidencia live 2026-09-05 (ciclo 63)

Busca pública limitada em duas páginas retornou cards de jurisprudência HTTP
200. A resposta da segunda página apresentou uma sobreposição, portanto a
paginação permanece explicitamente não comprovada e não é declarada completa.
A amostra de inteiro teor foi classificada como controle de acesso, sem
converter bloqueio em vazio. O envelope redigido está em
`docs/provider-discovery/tjsp-eproc-live-20260905-cycle63.json`.
## Transporte compartilhado (2026-09-08)

As requisições de listagem, paginação e inteiro teor usam `SharedHttpClient`
com allowlist exclusiva do host eproc oficial, TLS verificado, limite de
16 MB, timeout, intervalo por host e sem retry automático. POSTs não são
repetidos para evitar replay de estado ou controle de acesso. CAPTCHA, 401/403,
429, timeout, TLS, resposta excedente, redirecionamento fora da allowlist e
schema inválido permanecem explícitos; nenhum é convertido em vazio. O trace
preserva URL final, hash, bytes e latência.
