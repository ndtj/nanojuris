# `trf5_jurisprudencia`

## Identidade

- Fonte oficial: pesquisa de jurisprudencia do TRF5.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_form_jurisprudencia`.
- URL: `https://jurisprudencia.trf5.jus.br/jurisprudencia/pesquisa.wsp`.
- Status observado: busca publica reproduzida em sessao limpa em 2026-08-11.
- Status no NanoJuris: implementado para busca HTML e inteiro teor publico.

## Contrato observado

A pagina inicial usa ISO-8859-1 e possui dois formularios HTML. O primeiro
monta a consulta e fornece um token publico de sessao em `wi.token`; o segundo
envia a consulta para `resultado_pesquisa.wsp`.

Fluxo minimo observado:

```text
GET  /jurisprudencia/pesquisa.wsp
POST /jurisprudencia/resultado_pesquisa.wsp
```

Payload minimo reproduzido:

```text
tmp.search.query=dano moral
tmp.search.query_complemento=
tmp.ds_legislacao_2=
tmp.search.qtdade_registros=10
tmp.search.acao=novapesquisa
```

O formulario inicial tambem declara filtros publicos para orgao julgador,
classe, relator, processo, assunto, ementa, datas de julgamento/publicacao,
legislacao e tipo documental. Os tipos incluem `ACORDAOS`, decisoes da
Presidencia, decisoes monocraticas, informativos, jurisprudencia comparada e
sumulas.

## Evidencia live

Em 2026-08-11, uma sessao HTTP limpa com `dano moral` retornou:

- HTTP 200 e `Resultado da Pesquisa`;
- HTML de aproximadamente 12 KB;
- resultados com ementa, orgao julgador, tipo documental, data de julgamento
  e numero de processo;
- links/ancoras de `Exibir Inteiro Teor`, incluindo estados como `Pendente de
  Envio ao CJF`.

O resultado observado incluiu decisoes do TRF5, TRU e Turmas Recursais. O
provider deve conservar a origem especifica exibida no resultado, sem
classificar todas as linhas como acordao do Plenario.

## Campos canonicos

- `process_number`: numero CNJ quando presente;
- `decision_type`: tipo documental;
- `judging_body`: orgao julgador;
- `judgment_date`: data de julgamento;
- `summary`: ementa/indexacao;
- `document_url`: link oficial de inteiro teor quando houver;
- `raw`: HTML e labels originais para auditoria.

## Limites e riscos

- `wi.token` e dinamico; nunca deve ser fixado em codigo ou fixture de
  sucesso.
- O fluxo depende da sequencia GET da pagina e POST do resultado.
- O contrato HTML e sensivel a mudancas de labels e codificacao.
- A busca tem campos obrigatorios definidos pela propria pagina; o provider
  deve rejeitar consultas vazias antes do POST.
- Nao foram promovidos nesta rodada pagina 2, ordenacao e download automatico
  de inteiro teor.

## MCP

O agente pode usar a fonte para pesquisas do TRF5, mas deve declarar a fonte
e a data de consulta. Deve limitar `page_size`, respeitar intervalo entre
chamadas e distinguir resultado vazio de falha na sessao. O MCP nao deve
reutilizar cookies, token salvo ou estado de navegador.

## Implementacao 2026-08-11

`Trf5JurisprudenciaProvider` abre a pagina publica para criar a sessao,
obtem `wi.token` sem persistencia e envia o formulario para
`resultado_pesquisa.wsp`. O parser normaliza linhas `td.grid`, preserva labels
originais, id numerico e URL de `exibe_modelo.wsp`; o inteiro teor e exposto
como `CanonicalDocument` HTML.

## Fixtures e criterio de promocao

- `tests/fixtures/trf5_jurisprudencia_results.html` cobre token de sessao,
  resultado, ementa e inteiro teor referenciado;
- `tests/fixtures/trf5_jurisprudencia_empty.html` cobre zero resultado;
- `tests/fixtures/trf5_jurisprudencia_access_control.html` cobre bloqueio;
- `tests/fixtures/trf5_jurisprudencia_contract_changed.html` cobre mudanca de
  contrato;

- [x] fixture HTML da pagina inicial/resultados com token normalizado;
- [x] fixture HTML de resultado com acordao e metadados canonicos;
- [x] fixture de resultado vazio, acesso controlado e contrato alterado;
- [ ] teste de paginacao;
- [x] parser offline e `ProviderCapabilities`;
- [ ] teste live opt-in com limite pequeno.

O provider so deve ser implementado depois que o parser offline reproduzir os
campos canonicos e os estados vazio/erro.

## Proximos passos

1. Criar fixture do formulario inicial com `wi.token` normalizado e codificacao
   preservada.
2. Criar fixture de resultado com pelo menos acordao, decisao monocratica e
   informativo, quando observados publicamente na mesma superficie.
3. Criar fixture de resultado vazio para termo improvavel e classificar como
   `SearchPage` vazia, nao como erro.
4. Mapear paginacao, ordenacao e quantidade maxima de registros sem assumir
   parametros nao testados.
5. Validar `exibe_modelo.wsp` como rota de inteiro teor separada, preservando
   content type, bytes, hash e access status.
6. Testar filtros por orgao julgador, classe, relator, numero de processo,
   datas e legislacao com chamadas pequenas.
7. Registrar teste live opt-in com timeout curto e intervalo entre chamadas.

## Validacao live 2026-08-11

- GET do formulario e POST de resultado com `dano moral` responderam HTTP 200 com processo, ementa e links de inteiro teor.
- `wi.token` foi obtido somente da sessao corrente e nao deve ser persistido.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Referencias oficiais

- [Pesquisa de jurisprudencia do TRF5](https://jurisprudencia.trf5.jus.br/jurisprudencia/pesquisa.wsp)
- [Noticia oficial sobre a busca de jurisprudencia do TRF5](https://www.trf5.jus.br/index.php/noticias/leitura-de-noticias?%2Fid=324960)

## Aprofundamento De Filtros E Tipos Documentais - 2026-08-12

A tela oficial de pesquisa do TRF5 confirma uma consulta em camadas. Os
filtros visiveis devem ser representados no contrato do futuro provider sem
reduzir tudo a um unico campo textual.

| Grupo | Filtros observados |
| --- | --- |
| Basico | pesquisa livre, orgao julgador, quantidade de processos |
| Processo | classe da acao, numero do processo, assunto |
| Relatoria | relator |
| Decisao | periodo inicial/final da decisao |
| Publicacao | periodo inicial/final da publicacao |
| Texto | ementa, indexacao |
| Legislacao | sigla/norma, origem legislativa, descricao, numero, ano |
| Tipo documental | acordaos, decisoes da presidencia, decisoes monocraticas, informativos, jurisprudencia comparada e sumulas |

### Fluxo E Limites

```text
GET  /jurisprudencia/pesquisa.wsp
POST /jurisprudencia/resultado_pesquisa.wsp
```

O formulario gera `wi.token` na sessao corrente; o token deve ser obtido por
execucao, nunca persistido em fixture ou documentacao com valor real. A
validacao live retornou processo, ementa e links de inteiro teor para uma
consulta de dano moral. Ainda faltam contrato estavel de paginacao, ordenacao,
detalhe, tipos de fonte e comportamento de resultado vazio.

O provider deve preservar o tipo documental e a origem institucional em cada
registro. A busca por ementa/indexacao nao prova que o inteiro teor esteja
disponivel; o estado de acesso precisa ser reportado separadamente.

Fixtures de promocao: formulario com token normalizado, busca com cada grupo
de filtro, resultado misto de tipos documentais, pagina vazia, erro de sessao,
detalhe e link de inteiro teor.

## Inteiro teor e contrato de bytes

`GET /jurisprudencia/exibe_modelo.wsp?tmp.anexo.id_documento=<id>` retorna o
detalhe HTML observado. O provider preserva os bytes da resposta, extrai o
texto HTML e registra SHA-256, tamanho, content-type e URL final. A fonte
continua com paginacao remota e ordenacao pendentes de contrato; a existencia
de link nao e usada como prova de PDF.
