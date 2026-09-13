# Pesquisa

## Evidência oficial

- Portal: `https://sistemas.tjes.jus.br/consulta-jurisprudencia/`.
- Rota pública observada: `GET /consulta-jurisprudencia/api/search`.
- Chamada bounded em 2026-09-01: `core=pje2g`, termo jurídico, página 1,
  `per_page=1`, HTTP 200, JSON, um documento e total remoto 68.421.
- Campos observados: `id`, `id_bin`, `nr_processo`, `ementa`, `acordao`,
  `magistrado`, `orgao_julgador`, `classe_judicial`, `assunto_principal` e
  `dt_juntada`.
- Evidência resumida: `docs/provider-discovery/juscraper-live-smoke-20260901.json`.

O corpo live não foi persistido; a fixture do teste é sanitizada e mantém
somente a forma do contrato.
