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
```

O parser usa blocos `.clsInformativoBlocoItem` e preserva `SourceTrace`.

## Comportamento Observado

- Busca com resultado: uma ou mais notas oficiais.
- Busca sem resultado: `Nenhum item encontrado` vira `total=0`.
- Controle de acesso: challenge/captcha e reportado sem bypass.
- Inteiro teor: links de acordaos podem apontar para SCON, que pode exigir
  verificacao automatica separada.

## Fixtures

- Sucesso: `tests/fixtures/stj_informativo_infanticidio.html`.
- Vazio: fixture inline no teste.
- Erro: HTML sem contrato conhecido.

## MCP e Agentes

Use para perguntas de tese, resumo oficial, informativos, tema juridico e
referencias de julgados do STJ. Nao trate como contagem completa de acordaos.
Para busca integral, combine com `stj_scon` quando o acesso publico estiver
disponivel em sessao limpa.

## Proximos Passos

- [ ] Mapear filtros oficiais por ramo do direito, orgao julgador e ministro.
- [ ] Adicionar fixture com multiplas notas por termo.
- [ ] Separar links CNOT e links de acordao em campos dedicados.
