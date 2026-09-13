# Verification

## Evidência live

Em 2026-09-06 foi executada consulta pública bounded na API DSpace oficial:

`GET https://bd.tjmg.jus.br/server/api/discover/search/objects`

Termo: `responsabilidade`; escopos: cível, criminal e órgão especial; HTTP
200; 400 elementos somados. O item
`4e35d890-2618-4c84-abb5-6fa980f0a7a2` foi resolvido pelo endpoint de item e seu
bitstream ORIGINAL retornou HTTP 200, `application/pdf`, 72.816 bytes, quatro
páginas e 22.282 bytes de texto extraído.

## Gates

- runtime: aprovado
- contrato explícito CJSG: aprovado
- fixtures/testes: aprovados
- live bounded: aprovado
- qualidade canônica e documento: aprovados
- acesso público: aprovado
- federação técnica: habilitada

Comandos focados: `python -m pytest -q tests/test_tjmg_dspace_jurisprudencia.py`
(2 aprovados), Ruff, mypy e compileall. Nenhum commit, push ou deploy foi feito.

## Resultados

- Adapter, contrato e normalização: aprovados.
- Fixture de busca e testes de erro/documento: aprovados (2 testes).
- Chamada live e PDF original: aprovados conforme evidência registrada.
- Promoção técnica federada: habilitada; limitações do acervo preservadas.

## Rastreabilidade

- REQ-001/REQ-003/AC-001/AC-003: `tests/test_tjmg_dspace_jurisprudencia.py`.
- REQ-002/REQ-004/AC-002: evidência live e resolução do bitstream ORIGINAL.
- REQ-005/AC-004: testes de transporte, schema e documento indisponível.
