# `trt3_ementario_jurisprudencia`

Provider opt-in para a colecao publica **Ementario de Jurisprudencia** da
Biblioteca Digital oficial do TRT3. A colecao e uma busca paginada de volumes
editoriais de ementas de segundo grau (`TRT3_EMENTARIO`), nao uma busca geral do
tribunal.

Contrato executavel: POST para a pesquisa avancada oficial
`/bd-trt3/handle/11103/3797/advanced-search`, seguido de no maximo tres
volumes por consulta e GET dos respectivos PDFs oficiais via
`SharedHttpClient` (HTTPS allowlist, 8 MB, sem retry). A extracao e bounded com
`pypdf`; filtros textuais, frase e numero sao aplicados localmente as ementas.
Cada registro preserva `authority=TRT3`, `branch=labor`, `degree=second`,
`instance=second`, numero CNJ, data do volume quando identificavel, ementa,
URL, `raw` e `SourceTrace`.

HTML/PDF invalido, schema sem resultados, 403, 429, timeout e TLS nao sao
convertidos em vazio. O total remoto e de volumes, nao de decisoes; por isso
`total_known=false` na pagina de decisoes e a completude permanece parcial.
Inteiro teor nao e declarado: os documentos sao volumes de ementas. A fonte
permanece opt-in e fora da federacao padrao.

Evidencias: `docs/provider-discovery/trt3-ementario-live-20260909.json` e
`docs/provider-discovery/trt3-ementario-dspace-live-20260910.json`.

