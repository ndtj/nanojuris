# TCU - Jurisprudencia E Dados Abertos

Status atual: `implemented` para o adapter de dados abertos; pesquisa
interativa classificada separadamente como `blocked_or_inconclusive` no probe.

## Identidade Da Fonte

- Orgao: Tribunal de Contas da Uniao.
- Categoria: jurisprudencia administrativa e controle externo.
- Portal institucional: `https://portal.tcu.gov.br/jurisprudencia`.
- Pesquisa textual: `https://pesquisa.apps.tcu.gov.br/pes`.
- Dados abertos: `https://sites.tcu.gov.br/dados-abertos/jurisprudencia/`.
- Atualizacao observada no manifesto: `07/08/2026`.

O TCU separa acordaos, jurisprudencia selecionada, publicacoes, respostas a
consultas e sumulas. A fonte deve ser apresentada como jurisprudencia de
controle externo, e nao como jurisprudencia judicial estadual ou federal.

## Canal 1 - Pesquisa Interativa

O frontend publica a aplicacao e o contrato conceitual das bases:

```text
GET https://pesquisa.apps.tcu.gov.br/pes
GET https://pesquisa.apps.tcu.gov.br/pesquisa/jurisprudencia
```

O bundle oficial observou a rota de resultados resumidos para uma base, com
parametros de termo, ordenacao, quantidade e inicio:

```text
GET /rest/publico/base/acordao-completo/documentosResumidos
  ?termo=<termo>
  &ordenacao=<ordenacao>
  &quantidade=<limite>
  &inicio=<offset>
```

Ordenacao observada para acordaos:

`DTRELEVANCIA desc, NUMACORDAOINT desc, COPIACOLEGIADO desc`

No probe sem login, a pagina HTML e publica e a rota de resultados retornou
HTTP 200 com uma pagina de rejeicao do firewall de aplicacoes do TCU, em vez de
JSON. Isso nao deve ser tratado como busca vazia nem como contrato pronto para
fetcher. Nao foi usado login, cookie exportado, captcha, proxy ou bypass.

Classificacao do canal: `blocked_or_inconclusive` para automacao interativa.

## Canal 2 - Manifesto De Dados Abertos

Manifesto:

```text
GET https://sites.tcu.gov.br/dados-abertos/jurisprudencia/arquivos/jurisprudencia-arquivos.csv
```

Formato observado: texto delimitado por `|`, com cabecalho e colunas:

```text
BASE | ANO | TAMANHO | ARQUIVO
```

O manifesto publica os arquivos oficiais e o tamanho aproximado. Rotas
observadas:

| Base | Arquivo publico |
| --- | --- |
| Acordaos | `.../arquivos/acordao-completo/acordao-completo-YYYY.csv` |
| Acordaos - resumo | `.../arquivos/acordao-completo/acordao-completo-resumo.csv` |
| Jurisprudencia selecionada | `.../arquivos/jurisprudencia-selecionada/jurisprudencia-selecionada.csv` |
| Respostas a consultas | `.../arquivos/resposta-consulta/resposta-consulta.csv` |
| Sumulas | `.../arquivos/sumula/sumula.csv` |
| Boletim de jurisprudencia | `.../arquivos/boletim-jurisprudencia/boletim-jurisprudencia.csv` |
| Boletim de pessoal | `.../arquivos/boletim-pessoal/boletim-pessoal.csv` |
| Informativo de licitacoes e contratos | `.../arquivos/boletim-informativo-lc/informativo-lc.csv` |

Os arquivos aceitam requisicao parcial HTTP (`Range`), o que permite validar
cabecalho e schema sem baixar centenas de megabytes. O adapter deve suportar
download incremental e nao carregar o acervo inteiro em memoria.

## Schemas Observados

### Acordaos - resumo

```text
KEY | VISAOGERAL
```

O campo `VISAOGERAL` contem HTML com resumo do acordao. Deve ser preservado no
campo bruto e convertido para texto somente na camada canonica.

### Jurisprudencia selecionada

Campos observados:

```text
KEY, NUMACORDAO, ANOACORDAO, COLEGIADO, AREA, TEMA, SUBTEMA,
ENUNCIADO, EXCERTO, NUMSUMULA, DATASESSAOFORMATADA, AUTORTESE,
FUNCAOAUTORTESE, TIPOPROCESSO, TIPORECURSO, INDEXACAO,
INDEXADORESCONSOLIDADOS, PARAGRAFOLC, REFERENCIALEGAL,
PUBLICACAOAPRESENTACAO, PARADIGMATICO
```

### Respostas a consultas

Campos observados incluem identificacao do acordao, colegiado, area, tema,
subtema, enunciado, excerto, autor da tese, tipo de processo e referencias
legais.

### Sumulas

Campos observados:

```text
KEY, NUMERO, ENUNCIADO, TIPOPROCESSO, AREA, TEMA, SUBTEMA,
APROVACAO, NUMAPROVACAO, ANOAPROVACAO, COLEGIADO,
FUNCAOAUTORTESE, AUTORTESE, INDEXACAO, VIGENTE,
DATASESSAOFORMATADA, EXCERTO, REFERENCIALEGAL,
INDEXADORESCONSOLIDADOS, PUBLICACAO
```

### Boletim de jurisprudencia

```text
KEY | TITULO | ENUNCIADO | REFERENCIA | TEXTOACORDAO
```

`REFERENCIA` e `TEXTOACORDAO` podem conter tags HTML e elementos
institucionais. O parser nao deve remover a referencia oficial nem inventar
campos de processo ausentes.

## Mapeamento Canonico

- `source`: `tcu`.
- `source_system`: `tcu_jurisprudencia_abertos`.
- `source_id`: `KEY`.
- `dataset` e o discriminador semantico: `acordao-completo-resumo` representa
  decisoes; datasets de jurisprudencia selecionada, sumulas ou boletins devem
  ser tratados como corpus distintos.
- `decision_type`: `acordao`, `jurisprudencia_selecionada`, `resposta_consulta`,
  `sumula` ou `boletim`.
- `court`: `TCU`.
- `judging_body`: `COLEGIADO`, quando presente.
- `decision_number`: `NUMACORDAO` ou `NUMERO`.
- `decision_year`: `ANOACORDAO` ou `ANOAPROVACAO`.
- `thesis`: `ENUNCIADO`.
- `excerpt`: `EXCERTO`.
- `full_text`: `TEXTOACORDAO` ou `VISAOGERAL`, quando presentes.
- `subjects`: `AREA`, `TEMA`, `SUBTEMA` e `INDEXACAO`.
- `legal_references`: `REFERENCIALEGAL`.
- `published_at`: `DATASESSAOFORMATADA` ou data disponivel no registro.
- `raw`: registro original, sem mascaramento ou perda de campos.

Quando o dataset nao possuir ementa, relator ou processo, o provider deve
deixar o campo nulo e preservar o dado original. Ausencia de campo nao e
motivo para fabricar uma equivalencia judicial.

## Fixtures E Testes

- `tests/fixtures/tcu_manifest.csv`: manifesto publico reduzido;
- `tests/fixtures/tcu_acordao_resumo.csv`: sucesso com HTML em `VISAOGERAL`;
- `tests/fixtures/tcu_acordao_resumo_empty.csv`: vazio real;
- `tests/fixtures/tcu_manifest_contract_changed.txt`: contrato invalido;
- `tests/test_tcu_jurisprudencia.py`: parsing, preservacao do campo bruto,
  vazio e mudanca de contrato sem download integral.

Ainda faltam fixture representativa para cada schema adicional, deduplicacao em
sincronizacao local e teste opt-in limitado para `Range`.

## Uso Via MCP

O MCP pode expor o TCU em duas operacoes distintas:

1. `search_jurisprudence`: pesquisa local no dataset sincronizado, com a
   origem e a data de atualizacao do manifesto visiveis;
2. `get_public_dataset_manifest`: lista bases, anos, tamanhos e URLs oficiais.

A pesquisa interativa do TCU somente deve ser usada quando o endpoint retornar
JSON valido e sem controle de acesso. Uma pagina de firewall, HTTP 200 com HTML
de bloqueio ou ausencia de resultados deve produzir `access_control_required`,
nao `empty`.

## Implementacao 2026-08-11

`TcuJurisprudenciaProvider` consulta o manifesto oficial, expõe os datasets
como catalogo e faz busca limitada no CSV `acordao-completo-resumo.csv`. A
leitura e streaming e possui limite local de 80 MB por chamada. O provider
preserva `KEY`, `VISAOGERAL`, dataset, URL e trace de origem; detalhe de acordo
e download integral ainda nao fazem parte do contrato executavel.

## Promocao Para Provider

- [x] adicionar fixtures e testes offline do manifesto e do resumo;
- [x] declarar `ProviderCapabilities` como fonte de dados abertos;
- [x] documentar limite de leitura e atualizacao;
- [ ] adicionar fixture representativa versionada para cada schema adicional;
- [ ] validar um arquivo pequeno em live opt-in;
- [ ] implementar cache local com metadados de origem;
- [ ] manter a pesquisa interativa fora do provider ate o firewall permitir um
  contrato reproduzivel sem identidade ou desafio.

## Validacao live 2026-08-11

- O manifesto respondeu HTTP 200 com 5.945 bytes; o CSV de resumo aceitou Range e respondeu HTTP 206 com schema `KEY|VISAOGERAL`.
- A pesquisa interativa permanece separada: o endpoint de resultados respondeu firewall HTML, nao JSON.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Validacao Live 2026-08-16

O adapter executavel consultou o CSV publico de resumo com a consulta
`responsabilidade civil`, retornando um registro em 12,8 s. A evidencia
estruturada esta em
[`docs/validation/runs/20260816T023226Z-tcu-open-data-contract.json`](https://github.com/ndtj/nanojuris/blob/main/docs/validation/runs/20260816T023226Z-tcu-open-data-contract.json).
O provider registra HTTP, URL final, tipo/tamanho quando fornecidos pelo
servidor e `access_status=public` para resultados efetivamente extraidos. Como
a leitura e streaming, hash e tamanho do corpo so sao afirmados quando a fonte
os fornecer sem exigir a retencao integral do arquivo.

## Fontes Oficiais

- [Jurisprudencia do TCU](https://portal.tcu.gov.br/jurisprudencia)
- [Pesquisa textual do TCU](https://pesquisa.apps.tcu.gov.br/pes)
- [Pesquisa integrada do TCU](https://pesquisa.apps.tcu.gov.br/#/pesquisa/integrada)
- [Dados abertos de jurisprudencia](https://sites.tcu.gov.br/dados-abertos/jurisprudencia/)
- [Dicionario de dados](https://sites.tcu.gov.br/dados-abertos/jurisprudencia/dicionario-dados.html)
