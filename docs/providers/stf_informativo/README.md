# stf_informativo

## Identidade

- Fonte oficial: Supremo Tribunal Federal.
- Categoria: jurisprudencia de tribunal superior.
- Familia tecnica: XLSX publico estruturado.
- URL inicial: `https://portal.stf.jus.br/textos/verTexto.asp?servico=informativoSTF`.
- Status de acesso: publico; a rota oficial exige um User-Agent de navegador
  comum e devolveu HTTP 200 no smoke live de 2026-10-12.

## Contrato HTTP

Rota publica usada:

```text
GET https://www.stf.jus.br/arquivo/cms/informativoSTF/anexo/Informativo_Dados/Dados_InformativosSTF.xlsx
```

O arquivo foi validado em 12/10/2026 como XLSX publico com 11.626 linhas de
dados observadas. O provider usa download direto e filtra localmente, sem depender
da API JSON `jurisprudencia.stf.jus.br/api/search/search`, que pode retornar
AWS WAF em sessoes limpas.

O IIS/WAF do arquivo rejeita o User-Agent padrao `NanoJuris/` com HTTP 403,
mas entrega a mesma rota publica para um User-Agent de navegador comum. O
provider usa esse formato apenas para compatibilidade da rota, sem resolver
desafio, captcha ou autenticacao.

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
- Acesso: User-Agent de navegador comum e necessario nesta rota publica; HTTP
  403 continua sendo reportado como indisponibilidade quando a origem bloqueia.
- SSL: o padrao do NanoJuris mantem `verify_ssl=True`.

## Fixtures

- Sucesso: XLSX minimo gerado em `tests/test_stf_informativo.py`.
- Erro: header alterado e payload nao-XLSX.
- Decisao de rastreabilidade: o XLSX permanece um builder inline, pois o
  conteudo atual e um contrato sintetico versionado e nao uma resposta oficial
  arquivada; nao foi promovido a fixture live por inferencia.

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

## Validacao live 2026-10-12

Com SSL habilitado e User-Agent de navegador comum, o XLSX oficial respondeu
HTTP 200, foi parseado em 11.626 linhas e a busca `dano moral` retornou 41
ocorrencias, com o primeiro resultado `RE 662055/SP`.

Veja a matriz completa em
[live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/live-validation-2026-08-11.md).
