# `tjdf_juris`

## Identidade

- Fonte oficial: jurisprudencia publica TJDFT/SISTJ.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_jurisprudencia_tribunal`.
- Uso preferencial: demonstracoes, estudos jurimetricos iniciais e validacao de
  fluxo MCP.
- Nivel atual esperado: 5.

## Contrato conhecido

O provider declara busca textual, resumo, intervalo de data, paginacao e
documento por identificador. Retorna `CanonicalDecision` e preserva campos como
ementa/resumo, relator, datas, tipo, tribunal e metadados brutos.

## Superficie API JSON descoberta

O TJDFT tambem publica uma API oficial de consulta a jurisprudencia:

```text
POST https://jurisdf.tjdft.jus.br/api/v1/pesquisa
```

Payload minimo reproduzido:

```json
{
  "query": "dano moral",
  "pagina": 0,
  "tamanho": 2
}
```

`pagina` e baseada em zero. `tamanho` controla a quantidade da pagina. A
documentacao oficial tambem descreve `termosAcessorios`, uma lista de filtros
estruturados que pode conter `base`, `subbase`, `origem`, `uuid`,
`identificador`, `identificadorOrdenacao`, `processo`, `nomeRelator`,
`nomeRevisor`, `nomeRelatorDesignado`, `descricaoOrgaoJulgador`,
`dataJulgamento`, `dataPublicacao` e `descricaoClasseCnj`.

Resposta observada em sessao limpa:

```json
{
  "hits": 261606,
  "registros": [
    {
      "uuid": "...",
      "identificador": "...",
      "dataPublicacao": "...",
      "ementa": "...",
      "processo": "...",
      "nomeRelator": "...",
      "descricaoOrgaoJulgador": "...",
      "inteiroTeor": "...",
      "possuiInteiroTeor": true
    }
  ]
}
```

O retorno real tambem publica `agregações` e `paginação`. A API e uma rota
JSON estruturada e deve ser tratada como a proxima superficie de implementacao
do `tjdf_juris`; ela nao deve gerar um segundo provider para o mesmo tribunal.
O parser deve preservar `registros`, agregacoes e campos desconhecidos em
`raw`, alem de registrar a URL e os parametros no `SourceTrace`.

## Dados e mapeamento canonico

| Campo observado | Campo NanoJuris | Regra |
| --- | --- | --- |
| `uuid`/`identificador` | `id` e `raw.external_id` | preservar o identificador da API |
| `processo` | `case_number` | manter a mascara retornada |
| `ementa`/`inteiroTeor` | `summary`/`full_text` | nao confundir trecho com inteiro teor |
| `nomeRelator` | `rapporteur` | preservar o texto original |
| `dataJulgamento`/`dataPublicacao` | datas canonicas | normalizar para ISO e guardar o valor bruto |
| `descricaoOrgaoJulgador` | `judging_body` | preservar tambem em `raw` |

Registros sem `possuiInteiroTeor` ou sem texto completo permanecem parciais;
o provider nao infere inteiro teor a partir da ementa.

## Pontos fortes

- Fonte adequada para busca textual de jurisprudencia.
- Bom potencial para amostras comparativas.
- Boa candidata para exemplos publicos por ser menos sensivel que fontes com
  captcha frequente.

O contrato completo da superficie JSON esta em [API v1 de Jurisprudencia do
TJDFT](https://github.com/ndtj/nanojuris/blob/main/docs/providers/tjdf_juris/api-v1.md).

## Lacunas a aprofundar

- Completar dossie de parametros de detalhe e ordenacao.
- Integrar a superficie JSON `/api/v1/pesquisa` sem remover o fluxo HTML legado.
- Confirmar rota de detalhe ou inteiro teor associada a `uuid`/`identificador`.
- Definir se `inteiroTeor` e texto completo ou trecho condicionado por
  `possuiInteiroTeor`.
- Criar fixtures adicionais para pagina vazia e variacao de pagina de detalhe.
- Documentar campos que variam por classe, orgao julgador e tipo decisorio.

## MCP e agentes

Recomendacao: boa fonte para perguntas naturais de jurisprudencia. O agente
deve usar page size pequeno, preservar traces e avisar quando a amostra for
exploratoria.

## Fixtures esperadas

- busca com resultado;
- busca vazia;
- pagina de detalhe;
- resposta JSON da API com agregacoes e paginacao;
- erro ou HTML inesperado.

## Evidencia live

Em 2026-08-11, `POST /api/v1/pesquisa` com a consulta `dano moral`, pagina
zero e tamanho dois respondeu HTTP 200 com 261606 hits e dois registros. A
validacao foi feita sem login, cookie pessoal ou contorno de controle de
acesso. A rota e adequada para fixture publica reduzida, sem versionar o
acervo inteiro.

## Proximos passos

1. salvar fixture pequena da resposta JSON, mantendo um registro completo;
2. implementar parser JSON paralelo ao parser HTML existente;
3. validar pagina vazia, filtros de data e `termosAcessorios`;
4. localizar detalhe publico por `uuid` ou `identificador`;
5. comparar cobertura e campos com o fluxo HTML antes de tornar a API a rota
   preferencial.

## Inteiro teor e contrato de bytes

`get_document()` carrega o detalhe HTML publico por `numeroDoDocumento`. O
texto normalizado e disponibilizado em `CanonicalDocument.text`; a resposta
original permanece em `raw_bytes` e e identificada por SHA-256, tamanho,
content-type e `SourceTrace`. Isso comprova carregamento do documento HTML,
mas nao implica que a fonte ofereca PDF.

## Filtros e modo de detalhe

- `published_from`/`published_to` sao enviados ao SISTJ com
  `tipoDeData=DataPublicacao`.
- `updated_from`/`updated_to` representam a data de julgamento e sao enviados
  com `tipoDeData=DataJulgamento`.
- `rapporteur` e enviado como `desembargador`.
- `all_words`, `any_words` e `without_words` sao traduzidos para a sintaxe
  booleana observada no formulario publico (`e`, `ou` e `nao`).
- `fetch_details=False` usa somente a pagina de resultados, sem uma requisicao
  de detalhe por item; os registros ficam marcados como parciais e nao devem
  ser interpretados como inteiro teor.
- `fetch_details=True` carrega o detalhe publico de cada resultado e habilita o
  preenchimento dos campos detalhados e do documento quando a fonte o fornece.
