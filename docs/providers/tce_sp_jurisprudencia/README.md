# `tce_sp_jurisprudencia`

## Identidade

- Fonte oficial: Boletim de Jurisprudencia do TCE-SP.
- Categoria: `administrative_jurisprudence`.
- Familia tecnica: `catalogo_administrativo`.
- URL inicial: `https://www.tce.sp.gov.br/boletim-de-jurisprudencia`.
- Status de acesso: publico parcial.
- Status no NanoJuris: provider implementado.

## Contrato HTTP

- Rotas conhecidas:
  - `GET /boletim-de-jurisprudencia/sumulas`
  - `GET /boletim-de-jurisprudencia/publicacoes`
  - `GET /boletim-de-jurisprudencia/indice-alfabetico-remissivo`
- Metodos: `GET`.
- Paginacao: catalogos estaticos, a depender da pagina oficial.
- Busca dinamica: nao automatizada quando exigir reCAPTCHA.

O método `get_catalog()` usa as rotas públicas de súmulas e publicações como
alternativa segura à busca dinâmica. Ele retorna as espécies disponíveis,
quantidade de itens por coleção e mantém os registros completos em `raw`;
nenhum desafio de acesso é automatizado.

## Rota adicional

`get_index()` consulta o Ã­ndice alfabÃ©tico/remissivo pÃºblico, preservando cada
tema e o boletim oficial relacionado. A rota nÃ£o Ã© tratada como busca dinÃ¢mica
e continua sujeita a validaÃ§Ã£o de schema.

## Dados retornados

- Campos extraidos:
  - numero da sumula;
  - enunciado;
  - historico;
  - fundamento;
  - edicao do boletim;
  - URL do boletim.
- Campos canonicos: `CanonicalPrecedent` e `CanonicalDocument`.
- Inteiro teor: páginas públicas de boletins podem ser obtidas por
  `get_document` somente a partir de URL observada; MIME, tamanho, hash,
  allowlist e `SourceTrace` são validados pelo transporte compartilhado.
  Evidência bounded: `docs/provider-discovery/tce-sp-document-live-20260906.json`.

## Comportamento observado

- Catalogos publicos: acessados por HTML.
- Busca dinamica: pode exigir reCAPTCHA e nao deve ser automatizada.
- Mudanca de layout: risco medio por paginas institucionais.

## Fixtures

- [x] Lista de sumulas: `tests/fixtures/tce_sp_sumulas.html`.
- [x] Lista de publicacoes: `tests/fixtures/tce_sp_boletins.html`.
- [x] Indice alfabetico: `tests/fixtures/tce_sp_indice.html`.
- [x] Pagina com estrutura alterada: parser falha explicitamente quando os
  headings ou links oficiais desaparecem.

## MCP e agentes

- Quando usar: pesquisa de sumulas e jurisprudencia administrativa do TCE-SP.
- Quando pular: quando o usuario pedir acordaos judiciais ou jurisprudencia de
  tribunais judiciais.
- Mensagem segura: "Esta fonte e administrativa e cobre conteudo publico do
  TCE-SP, nao acordaos judiciais."
- Riscos: confundir controle externo/administrativo com jurisprudencia judicial.

## Proximos passos

- [x] Completar fixtures de catalogo.
- [x] Documentar limites da busca dinamica com reCAPTCHA.
- [x] Separar melhor sumula, boletim e indice no catalogo MCP.

## Transporte compartilhado (2026-09-08)

As rotas públicas de súmulas, boletins e índice usam `SharedHttpClient` com
allowlist exclusiva do host oficial, TLS verificado, limite de 8 MB, timeout,
intervalo por host e sem retry automático. A busca dinâmica protegida por
reCAPTCHA continua deliberadamente fora do fluxo. HTTP 403/429, timeout, TLS,
redirecionamento fora da allowlist, resposta excedente e schema inválido são
estados explícitos e nunca são convertidos em vazio; documentos observados
continuam passando pelo pipeline documental compartilhado.
