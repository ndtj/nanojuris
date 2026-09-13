# TJMRS Jurisprudência — processo exato

Status: `implemented`, `live_validated` para consulta exata por processo,
runtime opt-in e fora da federação padrão.

## Identidade

- Fonte oficial: [Tribunal de Justiça Militar do Rio Grande do Sul](https://www.tjmrs.jus.br/).
- Autoridade: `TJMRS`.
- Ramo: `military`.
- Grau/instância: `second` quando o documento publicado contém acórdão,
  relator e ementa.
- Coleção: `TJMRS_JURISPRUDENCIA`.

## Contrato observado

```text
GET https://www.tjmrs.jus.br/abreJurisprudencia.php?processo=<20 dígitos CNJ>
```

A rota pública retorna uma decisão HTML inline para um processo exato. O
parser extrai o número formatado, classe, relator, ementa, inteiro teor e
identidade institucional. Quando a página contém somente mensagens como
“Não houve registro de acórdão”, o resultado é vazio autoritativo. Uma página
que não contenha nem decisão nem esse marcador é rejeitada como mudança de
contrato.

Não foi observado contrato reproduzível de busca textual geral, de paginação
ou de total do corpus. Por isso a superfície é opt-in e não compete com a
jurisprudência geral na federação padrão.

## Limites e uso responsável

- Uma requisição por processo e janela única.
- O transporte compartilhado aplica HTTPS, allowlist, timeout, limite de
  bytes, rate limit e circuito.
- 403, 429, CAPTCHA, WAF, TLS, timeout e schema inválido permanecem estados
  diagnósticos; nunca são convertidos em vazio.
- Nenhum cookie, credencial, token, proxy ou tentativa de contorno foi usado.
- O inteiro teor é obtido somente por chamada explícita de documento e não é
  persistido como corpus pesquisável.

## Fixtures, testes e evidência

- `tests/fixtures/tjmrs_jurisprudencia_result.html`
- `tests/fixtures/tjmrs_jurisprudencia_empty.html`
- `tests/test_tjmrs_jurisprudencia.py`
- `docs/provider-discovery/tjmrs-jurisprudencia-live-20260909.json`

## Promoção

Os gates técnicos do adapter estão fechados para a consulta exata: fonte
oficial, contrato, parser, fixture, vazio, erro de acesso, trace, inteiro teor
e chamada live bounded. A fonte permanece `supports_unified_search=false` e
`opt_in_unified_search=true` porque não há busca geral nem paginação provadas.
Essa promoção técnica local não declara aprovação jurídica, release ou deploy.
