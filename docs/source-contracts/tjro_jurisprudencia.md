# Contrato de fonte — TJRO jurisprudência textual

Status: `implemented` — busca federada habilitada após contrato mínimo
reproduzível. O download de inteiro teor continua uma operação explícita
(`fetch_details=True`/`get_document`), sempre bounded e sem promoção de
facetas não contratadas.

O mesmo endpoint possui dois bindings de grau independentes: `CJPG` usa
`fields.grau_jurisdicao=[1]` e registros `PJEPG`; `CJSG` usa
`fields.grau_jurisdicao=[2]` e registros `PJESG`. O smoke bounded de CJPG de
06/09/2026 confirmou duas páginas sem sobreposição, dez sentenças por página,
resumo textual, identificador, processo e data. A evidência está em
`docs/provider-discovery/tjro-cjpg-live-20260906.json`.

## Identidade da fonte

Tribunal: Tribunal de Justiça do Estado de Rondônia (TJRO). Coleção nativa:
busca textual geral; os bindings canônicos `CJPG` e `CJSG` filtram grau
explicitamente e não misturam documentos. É uma
identidade diferente de `tjro_liame`, que permanece restrito a precedentes
qualificados.

## Superfície oficial

- Busca: `https://juris-back.tjro.jus.br/search/varios_parametros/`
- Facetas: `POST /search/agregacoes` (observada ao vivo; permanece pendente de
  modelo canônico e política de retenção)
- Inteiro teor: `GET /pje/buscar_pdf_ou_docx/<sistema_origem>/<id_processo_documento>/<pdf|docx>/`
- Documentos relacionados PJESG: `GET /search/documentos_relacionados/<id_documento_principal>`
- Autenticação: não observada na busca ou no download público bounded

## Contrato operacional

O adapter envia `POST` JSON com `from` (offset base zero), `size` limitado
localmente a 100, `fields.query`, ordenação e `highlight`. A resposta precisa
manter `hits.total.value` e `hits.hits`. Filtros confirmados no runtime são
texto, expressão exata traduzida, número, relator e intervalo de atualização.
O campo divergente `fields.tipo` é omitido por padrão; chamadas live com
vocabulário não confirmado retornaram zero e não são usadas para concluir que
o acervo está vazio.

Quando `fetch_details=True`, cada hit da página é enriquecido por uma chamada
GET de inteiro teor. O documento é identificado pela combinação observada de
`id_processo_documento` e `sistema_origem`; os formatos permitidos são `pdf` e
`docx`. A rota relacionada é chamada somente por `get_related_documents` para
um identificador principal explícito, sem fan-out durante a busca normal.

## Dados canonicos

Cada hit é mapeado para `JurisprudenceResult`, preservando o hit em `raw` e
URL, status, hash, tamanho e duração em `SourceTrace`. Documentos preservam
bytes, hash, formato e URL em `CanonicalDocument`. HTTP 401/403/420, 429,
400/422, 5xx, timeout, TLS, JSON inválido, documento inválido e schema drift
são erros explícitos; nenhum é convertido em lista vazia. Total zero só é
vazio autoritativo com payload válido e filtros confirmados.

## Estados e falhas

Estados observáveis são `valid`, `empty`, `partial`, `blocked`, `rate_limited`,
`timeout`, `unavailable` e `parser_changed`. Uma página com total conhecido e
janela incompleta permanece marcada como parcial. Bloqueio, erro HTTP ou
indisponibilidade nunca são apresentados como “zero resultados”.

## Fixtures e testes

As fixtures sanitizadas cobrem sucesso, vazio, hit inválido, schema drift,
acesso, rate limit e erro upstream, além de documento PDF e relacionados:

- `tests/fixtures/tjro_jurisprudencia_results.json`;
- `tests/fixtures/tjro_jurisprudencia_empty.json`;
- `tests/fixtures/tjro_jurisprudencia_invalid.json`;
- `tests/fixtures/tjro_jurisprudencia_schema_drift.json`;
- `tests/fixtures/tjro_jurisprudencia_access_control.json`;
- `tests/fixtures/tjro_jurisprudencia_error.json`;
- `tests/fixtures/tjro_jurisprudencia_related.json`.

Os testes do adapter estão em `tests/test_tjro_jurisprudencia.py` e cobrem
identidade, paginação, erro explícito, detalhe documental e roteamento.

## MCP e federação

O módulo pode ser chamado explicitamente por `source="tjro_jurisprudencia"` e
está registrado na instância padrão do `NanoJurisClient`. Como
`supports_unified_search=True`, a busca textual bounded participa da federação
automática. O roteador emite avisos para refinamentos sem contrato confirmado;
isso não transforma filtros ignorados em resultados vazios. O provider não
substitui nem reclassifica `tjro_liame`, que permanece a coleção de precedentes
qualificados.

## Proximos passos

Confirmar vocabulário de classe, órgão, grau e tipo antes de expô-los no modelo
canônico; definir facetas sem reter listas extensas; repetir smoke live bounded
e revisar os gates globais de release/licença. Essas melhorias não bloqueiam a
busca textual mínima já integrada.
## Mapeamento canonico de grau

Cada hit preserva o valor nativo em `raw.degree` e expone `degree`/`instance`
normalizados. `PJEPG` e `grau_jurisdicao=1` tornam-se `first`; `PJESG` e `2`
tornam-se `second`; valores nao reconhecidos ficam `unknown`. A superficie
unificada usa `authority=TJRO`, `branch=state` e `collection=JURISPRUDENCIA`;
isso nao credita automaticamente CJPG/CJSG na matriz.

## Rechecagem bounded de inteiro teor - 2026-09-08

Uma chamada publica bounded com `degree=second`, `instance=second` e
`fetch_details=True` retornou um registro PJESG valido. O PDF respondeu
`application/pdf` com 29.618 bytes e o texto extraido possui 11.949 caracteres.
O hash SHA-256 do documento e
`ed3c357720fd7744dfd0f6f79a35d000ae89e45efb6957744dfd0f6f86b80a0`.
A evidencia esta em
`docs/provider-discovery/tjro-jurisprudencia-fulltext-live-20260908.json`;
nenhum corpo bruto foi persistido. Isso confirma a rota de inteiro teor para
uma decisao de segundo grau, mas nao altera por si so os gates nacionais.
