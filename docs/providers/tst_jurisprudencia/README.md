# `tst_jurisprudencia`

## Identidade

- Fonte oficial: Tribunal Superior do Trabalho (TST).
- Categoria: `court_jurisprudence`.
- Familia tecnica: SPA React + API REST JSON.
- URL inicial: `https://jurisprudencia.tst.jus.br/`.
- Status de acesso: publico, reproduzido em sessao HTTP limpa.
- Status no NanoJuris: provider implementado com fixtures e testes offline.

## Contrato descoberto

O frontend publica `GET /config.json`, que informa a base atual da API e as
URLs oficiais de consulta. Na rodada de 2026-08-11, a configuracao respondeu:

```json
{
  "base_url": "https://jurisprudencia-backend2.tst.jus.br",
  "consulta_acordao_url": "https://consultadocumento.tst.jus.br/consultaDocumento/acordao.do",
  "consulta_despacho_url": "https://consultadocumento.tst.jus.br/consultaDocumento/despacho.do",
  "consulta_proc_url": "https://consultaprocessual.tst.jus.br/consultaProcessual/resumoForm.do"
}
```

### Busca textual

```text
POST https://jurisprudencia-backend2.tst.jus.br/rest/pesquisa-textual/{inicio}/{limite}?a={cache_buster}
Content-Type: application/json
```

O corpo observado pelo frontend possui estes grupos:

```json
{
  "e": "responsabilidade civil",
  "ou": "",
  "termoExato": "",
  "naoContem": "",
  "ementa": "",
  "dispositivo": "",
  "numeracaoUnica": {"numero": "", "digito": "", "ano": "", "orgao": "5", "tribunal": "", "vara": ""},
  "orgaosJudicantes": [],
  "ministros": [],
  "convocados": [],
  "classesProcessuais": [],
  "indicadores": [],
  "assuntos": [],
  "tipos": ["ACORDAO"],
  "orgao": "TST",
  "publicacaoInicial": "",
  "publicacaoFinal": "",
  "julgamentoInicial": "",
  "julgamentoFinal": "",
  "ordenacao": "data"
}
```

`inicio` e 1-based. O frontend envia, por exemplo, `1/20` para a primeira
pagina. O retorno observado e JSON com `totalRegistros`, `registros` e
`agregacoes`.

### Catalogos de filtros

As seguintes rotas responderam JSON em sessao limpa:

```text
GET /rest/orgaos-judicantes
GET /rest/ministros
GET /rest/convocados
GET /rest/classes-processuais
GET /rest/indicadores
GET /rest/assuntos
```

Os objetos de catalogo devem ser preservados no campo bruto, pois seus codigos
sao necessarios para montar filtros estaveis.

### Inteiro teor

```text
GET https://jurisprudencia-backend2.tst.jus.br/rest/documentos/{id}
```

O `id` vem do registro da busca. A rota retornou `text/html` com ementa,
relatorio, fundamentacao e dispositivo. A resposta do registro tambem trouxe
`inteiroTeorHtml`, `inteiroTeorHTMLHighlight` e campos textuais; o provider deve
preferir o documento sob demanda e manter apenas um resumo controlado na
busca.

## Campos retornados

O objeto `registro` observado incluiu:

- `id`, `numero`, `numFormatado` e `numeracaoUnica`;
- `tipo`, `codFase` e `indTipAcordao`;
- `orgao` e `orgaoJudicante`;
- `nomRelator` e `codMinRelator`;
- `dtaJulgamento`, `dtaPublicacao`, `dtaAtualizacao`;
- `ementa`, `ementaHtml`, `txtEmentaHighlight`;
- `dispositivo`;
- `inteiroTeorHtml` e `inteiroTeorHTMLHighlight`;
- `txtTemaProc` e `temaProcs` quando existentes.

O retorno usa HTML com marcacoes de destaque da busca. O parser canonico deve
remover apenas as marcacoes de apresentacao, preservando o texto juridico e a
resposta HTML original no campo bruto ou no documento recuperado.

## Mapeamento canonico

| Campo TST | Campo NanoJuris |
| --- | --- |
| `id` | `external_id` |
| `numFormatado` / `numeracaoUnica` | `case_number` |
| `tipo.nome` | `document_type` |
| `codFase` | `case_class` |
| `orgao.sigla` / `orgao.nome` | `court` / `court_name` |
| `orgaoJudicante.descricao` | `chamber` |
| `nomRelator` | `rapporteur` |
| `dtaJulgamento` | `judgment_date` |
| `dtaPublicacao` | `publication_date` |
| `ementa` | `summary` |
| `dispositivo` | `disposition` |
| `/rest/documentos/{id}` | `document_url` |

O `SourceTrace` registra a base efetiva, rota, pagina, limite, termo e horario
da consulta. Quando observados pela resposta HTTP, tambem sao preservados
`http_status`, `final_url`, `content_type`, `content_sha256`, `response_bytes`,
`elapsed_ms` e `retrieval_status`. O provider deve sinalizar que o acervo e de
jurisprudencia trabalhista do TST.

## Limites e responsabilidade

- A rota publica pode mudar a base configurada pelo frontend; o provider deve
  consultar `config.json` ou permitir URL explicitamente configurada.
- A busca vazia deve ser rejeitada ou limitada para evitar varredura acidental.
- `page_size` deve ser limitado localmente e respeitar o rate limit configurado.
- O provider nao usa cookies pessoais, login, captcha, proxy de contorno ou
  mecanismo de evasao de controle de acesso.
- O HTML de inteiro teor pode conter dados pessoais publicados pela fonte. O
  NanoJuris deve preservar o retorno publico e registrar a origem.

## Fixtures e testes obrigatorios

- [x] Fixture JSON de busca com registro decisorio e agregacao.
- [x] Parser offline de catalogos, resultados e documento HTML.
- [x] Busca de sucesso com termo textual e `tipos=["ACORDAO"]`.
- [x] Rejeicao de busca vazia para evitar varredura acidental.
- [x] Registro com HTML de ementa e destaque removivel.
- [x] Documento HTML por `GET /rest/documentos/{id}`.
- [x] HTTP 401/429 e contrato nao-JSON tratados explicitamente.
- [ ] Teste live opt-in, com `page_size` pequeno e sem termo vazio.

## Uso pelo MCP

O MCP deve expor o TST como fonte especializada e informar no resultado:

1. `source=tst_jurisprudencia` e `court=TST`;
2. filtros e termo efetivamente enviados;
3. link oficial para resultado/documento;
4. diferenca entre resultado vazio, indisponibilidade e controle de acesso;
5. aviso de que o conteudo pertence a jurisprudencia trabalhista.

## Criterio de promocao

Promover para `implemented` somente depois de fixture publica versionada,
parser offline, testes de contrato, capability declaration, tratamento de
HTML/documento e teste live opt-in passarem no CI local.

## Inteiro teor e contrato de bytes

`GET /rest/documentos/{id}` e uma rota publica de inteiro teor HTML. O
provider preserva os bytes originais recebidos, calcula SHA-256 e tamanho e
extrai o texto para `CanonicalDocument.text`. O Studio e o MCP devem expor
esses metadados e deixar claro que a extração textual nao substitui o
documento bruto.
