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

- Sucesso: XLSX minimo gerado em `tests/test_stf_informativo.py`.
- Erro: header alterado e payload nao-XLSX.

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
