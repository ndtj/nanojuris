# stj_informativo

## Identidade

- Fonte oficial: Superior Tribunal de Justica.
- Categoria: jurisprudencia de tribunal superior.
- Familia tecnica: HTML publico curado.
- URL inicial: `https://processo.stj.jus.br/jurisprudencia/externo/informativo/`.
- Status de acesso: publico para notas do Informativo de Jurisprudencia.

## Contrato HTTP

Rota publica usada:

```text
GET /jurisprudencia/externo/informativo/
```

Parametros principais:

```text
acao=pesquisar
livre=<termo>
operador=E
b=INFJ
tp=T
```

Exemplo validado em 07/08/2026:

```text
GET https://processo.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisar&livre=INFANTICIDIO&operador=E&b=INFJ&tp=T
```

Retornou HTML publico do Informativo n. 507 com nota sobre `HC 228.998-MG`.

## Dados Retornados

Campos extraidos:

```text
informativo
period
case_number
rapporteur
judging_body
judgment_date
title
summary
document_url
acordao_url
cnot_url
```

O parser usa blocos `.clsInformativoBlocoItem` e preserva `SourceTrace`.

## Comportamento Observado

- Busca com resultado: uma ou mais notas oficiais.
- Busca sem resultado: `Nenhum item encontrado` vira `total=0`.
- Controle de acesso: challenge/captcha e reportado sem bypass.
- Inteiro teor: links de acordaos podem apontar para SCON, que pode exigir
  verificacao automatica separada.
- A nota CNOT pública pode ser recuperada por `get_document` somente a partir
  da URL observada; o link SCON continua separado. Evidência bounded:
  `docs/provider-discovery/stj-informativo-cnot-live-20260906.json`.
- A superficie publica suporta somente `livre`, `operador`, `b` e `tp`. Nao ha
  filtros independentes comprovados para ramo do direito, orgao julgador ou
  ministro; esses campos sao extraidos quando aparecem na nota e nao sao
  anunciados como filtros remotos.

## Fixtures

- Sucesso: `tests/fixtures/stj_informativo_infanticidio.html`.
- Multiplas notas e links: `tests/fixtures/stj_informativo_multiplas_notas.html`.
- Vazio: fixture inline no teste.
- Erro: HTML sem contrato conhecido.

## MCP e Agentes

Use para perguntas de tese, resumo oficial, informativos, tema juridico e
referencias de julgados do STJ. Nao trate como contagem completa de acordaos.
Para busca integral, combine com `stj_scon` quando o acesso publico estiver
disponivel em sessao limpa.

## Transporte compartilhado (2026-09-08)

A consulta pÃºblica do Informativo e a rota de documento CNOT observado agora
usam `SharedHttpClient`, com allowlist STJ, limite de 8 MB, timeout, rate limit
e circuito. 401/403, 429, TLS, timeout, redirecionamento e HTML de desafio
continuam estados explÃ­citos; nenhum bloqueio Ã© convertido em nota vazia e nÃ£o
hÃ¡ retry automÃ¡tico apÃ³s desafio ou rate limit.

## Proximos Passos

- [x] Confirmar o conjunto de filtros publicos (`livre`, `operador`, `b`, `tp`)
      e registrar como nao suportados os filtros sem rota comprovada.
- [x] Adicionar fixture com multiplas notas por termo.
- [x] Separar links CNOT e links de acordao em campos dedicados.
