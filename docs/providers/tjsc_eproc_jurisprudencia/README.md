# `tjsc_eproc_jurisprudencia`

## Identidade

- Tribunal: Tribunal de Justica de Santa Catarina.
- Familia tecnica: `html_jurisprudencia_eproc`.
- Categoria: `court_jurisprudence`.
- Entrada institucional: `https://www.tjsc.jus.br/web/tjsc/pesquisa-jurisprudencia`.
- Superficie de pesquisa observada:
  `https://eprocwebcon.tjsc.jus.br/consulta1g/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar`.
- Status do mapeamento: `candidate_ready`.
- Status no NanoJuris: implementado para busca e inteiro teor publico.

O TJSC informa a pesquisa no modulo de jurisprudencia do eproc. O contrato
deve ser tratado como uma instancia propria da familia eproc, porque os labels,
origens, tipos documentais e identificadores podem divergir dos contratos
federais e do TJRJ.

## Contrato HTTP observado

Fluxo publico reproduzido com uma sessao HTTP nova:

```text
GET  /consulta1g/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar
POST /consulta1g/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados
GET  /consulta1g/externo_controlador.php?acao=jurisprudencia@jurisprudencia/download_inteiro_teor&id_jurisprudencia=<id>
```

O formulario inicial declara os seguintes campos publicos:

- `txtPesquisa`;
- `rdoCampo` com pesquisa em inteiro teor (`I`) ou ementa (`E`);
- `chkPrecedenteRelevante`;
- `chkAgruparResultados`;
- `selOrigem[]`, `selTipoDocumento[]`, `selClasse[]`, `selRelator[]` e
  `selOrgao[]`;
- `txtProcesso`;
- `dtDecisaoInicio`, `dtDecisaoFim`, `dtPublicacaoInicio` e
  `dtPublicacaoFim`;
- campos ocultos de data e controle da pesquisa avancada.

Payload minimo reproduzido:

```text
txtPesquisa=dano moral
rdoCampo=I
hdnExibirPesquisaAvancada=
chkAgruparResultados=on
```

O POST retorna HTML `iso-8859-1` com cards `.resultadoItem`. O primeiro
resultado observado declarou `Documento 1 de 475091` e continha processo,
classe, tipo documental, UF, orgao julgador, datas, relator e texto de
decisao/ementa. A pagina inicial retornou 10 cards.

## Inteiro teor

Cada card publica um link com o identificador tecnico
`id_jurisprudencia` e, quando aplicavel, `termosPesquisados`:

```text
GET /consulta1g/externo_controlador.php?acao=jurisprudencia@jurisprudencia/download_inteiro_teor&id_jurisprudencia=<id>&termosPesquisados=<base64>
```

O detalhe validado retornou HTTP 200, `text/html`, aproximadamente 121 KB e
`Content-Disposition: inline; filename=jurisprudencia.html`. O resultado
tambem publica links oficiais para consulta processual no eproc2g. O parser
deve manter separados o card resumido, o inteiro teor e a consulta processual.

## Campos canonicos

- `process_number`;
- `decision_type`;
- `case_class`;
- `judging_body`;
- `judgment_date`;
- `publication_date`;
- `rapporteur`;
- `summary` ou `decision_text`;
- `document_url`;
- `id_jurisprudencia`;
- `source_origin` e tipo documental original.

O texto deve preservar a codificacao declarada pela resposta. Nomes de partes,
advogados e outros dados publicos eventualmente presentes no inteiro teor nao
devem ser inventados, removidos ou substituidos pelo parser; a camada canonica
deve apenas manter o conteudo que a fonte publica.

## Paginacao e limites

O primeiro POST aceita `selTamanhoPagina` e retorna `hdnTotalResultado`,
`hdnPaginaAtual`, `selTamanhoPagina` e `hdnUrlPaginar`. A rota AJAX indicada
por `hdnUrlPaginar` e reutilizada pelo parser eproc compartilhado para paginas
posteriores, mantendo a sessao publica.

Uma resposta live observada retornou 50 cards, IDs tecnicos em `id`/`data-id`,
datas em texto e links de inteiro teor. Na revalidacao Wave 2, paginas 1, 2 e 3
retornaram 25 cards e IDs novos por pagina, com total remoto de 10.075. O
payload de paginacao agora respeita a semantica do formulario: selects
multivalorados sem selecao nao sao enviados artificialmente. Controle de
acesso/indisponibilidade deve permanecer observavel e nunca ser contornado.

## Implementacao 2026-08-11

`TjscEprocJurisprudenciaProvider` usa o parser eproc compartilhado, mas declara
o host, tribunal, identificador e trace do TJSC. Busca, normalizacao dos cards,
download do inteiro teor e classificacao de controles de acesso estao
disponiveis no runtime. Campos, origens e limites continuam sujeitos ao
contrato especifico do TJSC.

## Decisao de mapeamento

Promovido de `candidate_needs_har` para provider implementado porque uma
chamada HTTP limpa retornou conteudo decisorio real, campos canonicos,
paginacao e inteiro teor publico. O contrato ainda nao deve ser usado para
coleta em escala sem:

1. fixture HTML de formulario e sucesso;
2. fixture de resultado vazio;
3. fixture de inteiro teor;
4. fixture de protecao/erro;
5. parser offline resiliente a labels e IDs dinamicos;
6. teste offline de paginacao e filtros de processo/data; a paginacao live foi
   validada na Wave 2;
7. teste live opt-in com intervalo conservador.

## MCP e uso responsavel

Usar quando o agente pedir jurisprudencia do TJSC por termo, processo, classe,
orgao, relator, tipo documental ou intervalo de datas. O resultado deve
identificar a origem como `TJSC/eproc` e informar quando o inteiro teor nao
estiver disponivel. O MCP nao deve reutilizar cookies, ViewState, tokens de
navegador ou tentar atravessar captcha, WAF ou bloqueios de frequencia.

## Validacao live 2026-08-11

- GET do formulario e POST `listar_resultados` responderam HTTP 200; foram observados 10 itens com ementa, processo, relator e paginacao.
- O contrato confirma a familia eproc compartilhada com TJRJ, mas campos e hosts permanecem especificos por tribunal.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Revalidacao de contrato - 2026-08-16

- O card TJSC sem a classe `a.numero-processo` agora e aceito pelo parser por
  `id_jurisprudencia`, processo textual, datas e link `data-link` oficial.
- O ID tecnico e preservado como identidade do resultado e o inteiro teor
  continua sob demanda.
- Estado live atual: `valid` para paginas 1 a 3 na Wave 2, com 25 IDs novos por
  pagina e total remoto de 10.075. Uma rodada anterior sem cards permanece
  registrada como instabilidade histórica, não como resultado vazio.

Evidencia estruturada: `docs/validation/runs/20260816T094054Z-wave2-acceptance-20260816.json`.

## Referencias oficiais

- [Pesquisa de jurisprudencia do TJSC](https://www.tjsc.jus.br/web/tjsc/pesquisa-jurisprudencia)
- [Formulario publico eproc/TJSC](https://eprocwebcon.tjsc.jus.br/consulta1g/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar)
