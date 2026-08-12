# API v1 de Jurisprudencia do TJDFT

## Status do contrato

- Fonte: Tribunal de Justica do Distrito Federal e dos Territorios.
- Identificador no NanoJuris: `tjdf_juris`.
- Superficie: API JSON publica de jurisprudencia.
- Estado: rota operacional reproduzida em sessao HTTP limpa.
- Autenticacao observada: nenhuma.
- Login, cookie pessoal, captcha, token privado ou proxy: nao utilizados.
- Ultima validacao: 2026-08-11.

Esta pagina documenta especificamente a API JSON. O provider tambem possui um
fluxo HTML legado do SISTJ, descrito no README do provider. As duas superficies
pertencem ao mesmo tribunal e nao devem virar providers duplicados.

## Fonte oficial

O TJDFT publica a API como um ponto de acesso estruturado a acordaos e decisoes
disponiveis para consulta publica. A documentacao institucional indica que a
API foi feita para consultas programaticas por tribunais, pesquisadores,
advogados e desenvolvedores.

Documentos oficiais:

- Documentacao: `https://www.tjdft.jus.br/transparencia/tecnologia-da-informacao-e-comunicacao/dados-abertos/documentacao_api_seti_transparencia.pdf`
- Pagina de dados abertos: `https://www.tjdft.jus.br/transparencia/tecnologia-da-informacao-e-comunicacao/dados-abertos/webservice-ou-api`
- Endpoint: `https://jurisdf.tjdft.jus.br/api/v1/pesquisa`

## Endpoint e transporte

```text
POST https://jurisdf.tjdft.jus.br/api/v1/pesquisa
Content-Type: application/json
Accept: application/json
```

O endpoint responde JSON. A consulta deve ser feita com POST. Nao foi
observada uma rota publica separada de detalhe, download ou autocomplete. O
resultado da pesquisa ja pode conter ementa, decisao, marcadores e um campo de
inteiro teor, sujeito a disponibilidade por registro.

### Exemplo minimo

```json
{
  "query": "dano moral",
  "pagina": 0,
  "tamanho": 10
}
```

`pagina` e baseada em zero. A primeira pagina e `0`, nao `1`.

### Exemplo com filtro

```json
{
  "query": "dano moral",
  "termosAcessorios": [
    {
      "campo": "nomeRelator",
      "valor": "CARMEN BITTENCOURT"
    },
    {
      "campo": "dataPublicacao",
      "valor": "2025-01-01"
    }
  ],
  "pagina": 0,
  "tamanho": 10
}
```

A documentacao oficial define `termosAcessorios` como uma lista de objetos
`campo`/`valor`. A semantica formal de combinacao de varios filtros nao esta
descrita no PDF; o adapter deve testar e registrar o comportamento real antes
de prometer operadores AND/OR na interface.

## Parametros da requisicao

| Campo | Tipo | Obrigatorio | Regra |
| --- | --- | --- | --- |
| `query` | string | sim | termo principal da pesquisa |
| `pagina` | integer | sim | pagina zero-based |
| `tamanho` | integer | sim | quantidade de registros por pagina |
| `termosAcessorios` | array | nao | filtros estruturados permitidos pela fonte |

O TJDFT nao publica, na documentacao consultada, limite maximo de `tamanho`,
limite de caracteres de `query`, politica de rate limit, ordenacao configuravel
ou janela temporal maxima. O cliente deve usar limites conservadores,
timeout, retries apenas para falhas transientes e intervalo entre chamadas.
Nao se deve afirmar que `tamanho` ilimitado e suportado.

## Filtros oficiais

Os campos permitidos em `termosAcessorios` sao:

| `campo` | Tipo esperado | Uso |
| --- | --- | --- |
| `base` | string | base de dados da decisao |
| `subbase` | string | subbase de dados |
| `origem` | string | origem da decisao |
| `uuid` | string | UUID da decisao |
| `identificador` | string | identificador da decisao |
| `identificadorOrdenacao` | string | identificador usado para ordenacao |
| `processo` | string | numero do processo |
| `nomeRelator` | string | relator |
| `nomeRevisor` | string | revisor |
| `nomeRelatorDesignado` | string | relator designado |
| `descricaoOrgaoJulgador` | string | orgao julgador |
| `dataJulgamento` | `YYYY-MM-DD` | data do julgamento |
| `dataPublicacao` | `YYYY-MM-DD` | data da publicacao |
| `descricaoClasseCnj` | string | classe processual CNJ |

Os nomes acima sao contrato da fonte. O NanoJuris nao deve traduzir ou
inventar nomes alternativos no payload sem manter um mapa explicito e testado.

### Filtros reproduzidos

| Filtro | Consulta | Resultado observado |
| --- | --- | --- |
| texto | `query="dano moral"` | HTTP 200, `hits.value=261606` em 2026-08-11 |
| relator | `nomeRelator="CARMEN BITTENCOURT"` | HTTP 200, `hits.value=2183` |
| data de julgamento | `dataJulgamento="2026-01-01"` | HTTP 200 com pagina vazia nessa combinacao |
| processo | filtro documentado; replay live ainda precisa de nova tentativa estavel | pendente de fixture |

Uma pagina vazia com HTTP 200 e schema valido significa zero resultados para
os criterios usados. Nao deve ser confundida com falha de rede.

## Resposta real

A resposta observada live possui estas chaves de topo:

```json
{
  "hits": {"value": 261606},
  "agregacoes": {},
  "paginacao": {"pagina": 0, "tamanho": 1},
  "registros": []
}
```

O PDF institucional representa alguns nomes com acentuacao (`agregações`,
`paginação`) e simplifica `hits` como total. Na resposta JSON live usada pelo
provider, as chaves observadas foram `agregacoes`, `paginacao` e `hits.value`.
O parser deve aceitar `hits` como objeto ou inteiro para tolerar variacoes da
fonte.

### Agregacoes

Em uma consulta com resultado, `agregacoes` publicou as facetas:

```text
relator
relatorDesignado
revisor
orgaoJulgador
base
segredoJustica
classe
```

Cada faceta normalmente e uma lista de buckets com `nome` e `total`; algumas
podem incluir `filhos`. Essas facetas sao uteis para construir filtros
assistidos no Studio e para orientar agentes, mas nao substituem a lista de
registros.

### Paginacao

`paginacao` publicou, na validacao live:

```json
{
  "pagina": 0,
  "tamanho": 1
}
```

O total deve ser lido de `hits.value` quando `hits` for objeto. O cliente deve
calcular a proxima pagina a partir de `pagina` e `tamanho`, respeitando o
limite configurado localmente.

## Registro de jurisprudencia

Os campos observados em registros live foram:

| Campo | Tipo | Significado |
| --- | --- | --- |
| `sequencial` | integer | posicao do registro no retorno |
| `base` | string | base documental |
| `subbase` | string | subbase documental |
| `uuid` | string | identificador UUID |
| `identificador` | string | identificador publico do julgado |
| `dataJulgamento` | timestamp/string | data do julgamento |
| `dataPublicacao` | timestamp/string | data de publicacao |
| `decisao` | string/null | resultado ou dispositivo |
| `ementa` | string/null | ementa e, em alguns registros, texto extenso estruturado |
| `localDePublicacao` | string/null | origem de publicacao, como PJe |
| `processo` | string/null | numero do processo |
| `nomeRelator` | string/null | relator |
| `relatorAtivo` | boolean/null | indicador de relator ativo |
| `uf` | string/null | unidade federativa |
| `segredoJustica` | boolean/null | sinal publicado pela fonte |
| `turmaRecursal` | boolean/null | indicador de turma recursal |
| `descricaoOrgaoJulgador` | string/null | orgao julgador |
| `versao` | string/null | versao do registro |
| `codigoClasseCnj` | integer/null | codigo da classe CNJ |
| `codigoSistjOrgaoJulgador` | integer/null | codigo interno do orgao julgador |
| `inteiroTeor` | string/null | campo apresentado no exemplo oficial |
| `inteiroTeorHtml` | string/null | campo observado na resposta live |
| `marcadores` | object/null | trechos marcados por campo |
| `jurisprudenciaEmFoco` | array/null | referencias destacadas, quando presente |
| `descricaoOrgao` | string/null | descricao alternativa do orgao |
| `possuiInteiroTeor` | boolean/null | indicador de disponibilidade declarado pela fonte |

O schema varia por tipo documental e versao. Campos desconhecidos devem ser
preservados em `raw`. Campos ausentes devem ser nulos, nunca preenchidos por
inferencias.

### Marcadores

O objeto `marcadores` pode conter listas para:

```text
ementa
termosAuxiliares
decisao
```

O provider deve preservar o objeto inteiro. A ausencia de marcadores nao
significa ausencia de ementa ou decisao.

### Inteiro teor

A presenca de `possuiInteiroTeor` nao deve ser usada isoladamente para afirmar
que o texto integral esta disponivel. Na validacao live houve registro com
`possuiInteiroTeor=true` e `inteiroTeorHtml="Inteiro Teor indisponível."`.

Regra do adapter:

1. usar `inteiroTeor` quando for uma string substantiva;
2. usar `inteiroTeorHtml` quando trouxer conteudo real, preservando HTML bruto;
3. tratar mensagens de indisponibilidade como ausencia de documento;
4. manter `possuiInteiroTeor` e o valor bruto para auditoria;
5. nao fabricar uma URL de detalhe quando a fonte nao a fornecer.

## Acesso por ferramentas

### Python

```python
import requests

payload = {
    "query": "dano moral",
    "termosAcessorios": [
        {"campo": "nomeRelator", "valor": "CARMEN BITTENCOURT"},
        {"campo": "dataJulgamento", "valor": "2025-01-01"},
    ],
    "pagina": 0,
    "tamanho": 10,
}

response = requests.post(
    "https://jurisdf.tjdft.jus.br/api/v1/pesquisa",
    json=payload,
    headers={"Accept": "application/json"},
    timeout=30,
)
response.raise_for_status()
data = response.json()
total = data["hits"].get("value", data["hits"]) if isinstance(data["hits"], dict) else data["hits"]
records = data.get("registros", [])
```

### cURL

```bash
curl --fail-with-body --request POST \
  --url https://jurisdf.tjdft.jus.br/api/v1/pesquisa \
  --header 'Accept: application/json' \
  --header 'Content-Type: application/json' \
  --data '{"query":"dano moral","pagina":0,"tamanho":10}'
```

### PowerShell

```powershell
$payload = @{
  query = "dano moral"
  pagina = 0
  tamanho = 10
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "https://jurisdf.tjdft.jus.br/api/v1/pesquisa" `
  -Method Post `
  -ContentType "application/json" `
  -Body $payload
```

## Erros e diagnostico

| Condicao | Classificacao NanoJuris | Regra |
| --- | --- | --- |
| HTTP 200 com `registros=[]` | vazio | retornar pagina vazia e `hits` |
| HTTP 200 sem `hits` ou `registros` | contrato alterado | nao tratar como vazio |
| JSON malformado | contrato alterado | preservar status e corpo limitado |
| HTTP 400/422 | parametro invalido | erro acionavel ao usuario |
| HTTP 401/403 | acesso controlado | nao tentar bypass |
| HTTP 429 | rate limit | respeitar Retry-After se houver |
| HTTP 5xx ou timeout | indisponivel | retry limitado e trace |
| conexao encerrada antes do JSON | indisponivel | repetir com backoff; nao concluir zero resultados |

O endpoint foi acessado sem autenticacao na validacao. Isso nao garante
disponibilidade permanente nem autoriza contornar bloqueios futuros.

## Mapeamento canonico

Para `CanonicalDecision`:

- `id`: `tjdf-api-{uuid}`; usar `identificador` como fallback;
- `source`: `tjdf_juris`;
- `court`: `TJDFT`;
- `type`: derivar de `base`/`subbase` apenas quando a fonte permitir;
- `number`: `processo` ou `identificador`;
- `summary`: `ementa`;
- `status`: `decisao`;
- `rapporteur`: `nomeRelator`;
- `updated_at`: `dataPublicacao`, com `dataJulgamento` preservada separadamente;
- `raw`: registro inteiro;
- `SourceTrace`: endpoint, payload, timestamp e resposta da fonte.

Para o documento, somente criar `CanonicalDocument` quando houver texto real em
`inteiroTeor` ou `inteiroTeorHtml`. A flag `possuiInteiroTeor` sozinha nao basta.

## Uso via MCP e Studio

O agente deve:

1. consultar `list_sources` e `source_contracts`;
2. usar `tjdf_juris` quando a pergunta pedir decisoes do TJDFT;
3. converter filtros naturais para `termosAcessorios` somente entre os campos
   oficiais;
4. limitar `tamanho` e paginas para evitar coleta acidental excessiva;
5. informar total, pagina, filtros aplicados e campos ausentes;
6. preservar `searched_sources`, `skipped_sources`, `errors` e `SourceTrace`;
7. distinguir ementa, decisao, texto integral e agregacao de filtros.

Exemplos de perguntas suportadas:

- "Busque no TJDFT dano moral e filtre pelo relator X.";
- "Quais classes aparecem nos resultados sobre violencia domestica?";
- "Localize decisoes do processo informado e mostre ementa e decisao.";
- "Traga resultados publicados a partir de uma data, indicando se o filtro
  retornou zero registros."

O agente nao deve afirmar que uma tese foi juridicamente correta apenas porque
apareceu na ementa. A API extrai e organiza; a interpretacao profissional deve
ser feita pelo usuario.

## Limites conhecidos e lacunas

- nao ha limite maximo de pagina/tamanho publicado no documento consultado;
- ordenacao explicita nao foi documentada;
- combinacao formal de varios filtros nao foi especificada;
- rota publica de detalhe/download nao foi localizada;
- o formato e a disponibilidade do inteiro teor variam por registro;
- categorias e valores de agregacoes devem ser descobertos na propria resposta;
- a API pode mudar sem versionamento visivel alem do prefixo `/api/v1`.

Antes de promover o fluxo como rota preferencial do provider, criar fixtures de:

- resultado com ementa e decisao;
- pagina vazia;
- filtro por relator;
- filtro por data;
- registro com `inteiroTeor`;
- registro com `inteiroTeorHtml` indisponivel;
- resposta com schema alterado;
- timeout, HTTP 429 e erro 5xx.

## Evidencia live desta documentacao

As chamadas publicas realizadas em 2026-08-11 confirmaram:

- consulta textual `dano moral`: HTTP 200, 261606 hits e dois registros com
  `tamanho=2`;
- filtro por `nomeRelator=CARMEN BITTENCOURT`: HTTP 200 e 2183 hits;
- filtro por `dataJulgamento=2026-01-01`: HTTP 200 e pagina vazia;
- agregacoes de relator, relator designado, revisor, orgao julgador, base,
  segredo de justica e classe;
- paginacao zero-based com `pagina` e `tamanho`;
- campos de ementa, decisao, processo, relator, classe, marcadores e indicador
  de inteiro teor.

## Referencias oficiais

- [Documentacao da API publica do TJDFT](https://www.tjdft.jus.br/transparencia/tecnologia-da-informacao-e-comunicacao/dados-abertos/documentacao_api_seti_transparencia.pdf)
- [Pagina oficial de Webservice e API](https://www.tjdft.jus.br/transparencia/tecnologia-da-informacao-e-comunicacao/dados-abertos/webservice-ou-api)
- [Endpoint publico da API](https://jurisdf.tjdft.jus.br/api/v1/pesquisa)
