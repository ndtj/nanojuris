# stf_informativo

## Identidade

- Fonte oficial: Supremo Tribunal Federal.
- Categoria: jurisprudencia de tribunal superior.
- Familia tecnica: XLSX publico estruturado.
- URL inicial: `https://portal.stf.jus.br/textos/verTexto.asp?servico=informativoSTF`.
- Status de acesso: publico para a planilha de dados do Informativo STF.

## Contrato HTTP

Rota publica usada:

```text
GET https://www.stf.jus.br/arquivo/cms/informativoSTF/anexo/Informativo_Dados/Dados_InformativosSTF.xlsx
```

O arquivo foi validado em 07/08/2026 como XLSX publico com dimensao observada
`A1:X11577`. O provider usa download direto e filtra localmente, sem depender
da API JSON `jurisprudencia.stf.jus.br/api/search/search`, que pode retornar
AWS WAF em sessoes limpas.

## Dados Retornados

Colunas oficiais mapeadas:

```text
Informativo
Classe Processo
Numero Processo
Incidente Julgamento
UF
Observacao
Data Julgamento
Relator
Redator Acordao
Orgao Julgador
Tipo Julgamento
Situacao Julgamento
Titulo
Tese Julgado
Resumo
Noticia
Ramo Direito
Materia
Repercussao Geral
Tema RG
Legislacao
ODS ONU 2030
Covid-19
Noticia completa
```

O resultado e normalizado como `JurisprudenceResult` e depois
`CanonicalDecision` para interoperabilidade com busca, store, CLI e MCP.

## Comportamento Observado

- Busca com resultado: linhas oficiais do Informativo STF com tese/resumo.
- Busca sem resultado: pagina vazia normalizada com `total=0`.
- Data: serial Excel convertido para ISO date.
- Inteiro teor: nao e baixado por este provider.
- Risco conhecido: a planilha e fonte curada, nao a base integral de acordaos.
- SSL: em alguns ambientes Windows, a cadeia local pode falhar. O padrao do
  NanoJuris mantem `verify_ssl=True`; para diagnostico local explicito, use
  `NanoJurisConfig(verify_ssl=False)`.

## Fixtures

- Sucesso de replay normalizado: `tests/fixtures/stf_informativo_rows.json`.
- Sucesso estrutural XLSX: builder minimo mantido em
  `tests/test_stf_informativo.py` para detectar drift de cabecalho e ZIP.
- Erro: header alterado e payload nao-XLSX.
- Decisao de rastreabilidade: a fixture JSON e sintetica e nao e uma resposta
  oficial arquivada; a evidencia live permanece separada e sem corpo persistido.

## MCP e Agentes

Use quando o advogado pergunta por entendimento do STF, tese resumida, ramo do
direito, materia, RG ou linhas oficiais do Informativo. E uma fonte muito boa
para IA porque entrega dados estruturados sem exigir download de PDF.

Quando a pergunta exigir voto completo, informe a limitacao e preserve a URL da
fonte oficial.

## Proximos Passos

- [ ] Adicionar fixture real publica representativa com repercussao geral.
- [ ] Mapear pagina HTML do Informativo para links por edicao.
- [ ] Criar exemplos de jurimetria por ramo do direito, materia e relator.

## Validacao live 2026-08-11

Com `trust_env=False` e SSL desabilitado somente para diagnostico local, o XLSX
oficial foi lido e a busca `ICMS` retornou 394 linhas, com uma linha na pagina
solicitada. Com SSL padrao habilitado, este ambiente apresentou falha de cadeia
local. O projeto permanece com `verify_ssl=True` por padrao.

Veja a matriz completa em
[live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/live-validation-2026-08-11.md).

## Rechecagem bounded 2026-09-01

A rota recebeu `SSLError` com TLS padrao e HTTP 403 em tentativa diagnostica
sem verificacao. O estado e operacional e especifico do ambiente; nao e
tratado como lista vazia nem altera o contrato runtime. Metadados sem corpo:
[`stf-informativo-live-recheck-20260901-cycle1.json`](../../provider-discovery/stf-informativo-live-recheck-20260901-cycle1.json).

## Transporte compartilhado e limites (2026-09-08)

O download XLSX usa o `SharedHttpClient` com allowlist do host oficial,
HTTP/1.1, limite de 20 MB, timeout, rate limit e circuito compartilhado. Erros
TLS, timeout, HTTP 403/429 e respostas acima do limite permanecem estados de
transporte explícitos; o parser só recebe bytes após uma resposta HTTP válida e
não transforma falhas em vazio.
