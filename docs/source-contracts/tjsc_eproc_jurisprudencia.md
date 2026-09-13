# `tjsc_eproc_jurisprudencia`

## Rechecagem de primeiro grau (2026-09-07)

Embora a rota contenha `consulta1g`, uma consulta bounded com
`degree=first`/`instance=first` retornou registros sem identidade de primeiro
grau; o parser rejeitou a resposta por misturar o grau solicitado. A mesma
rota com `degree=second` retornou registro explicitamente identificado como
TJSC/segundo grau. A tentativa de baixar o inteiro teor desse registro
retornou HTML de controle de acesso, sem credenciais ou replay de sessão.

Evidência: `docs/provider-discovery/tjsc-first-degree-eproc-boundary-live-20260907.json`.

Conclusão: este binding permanece CJSG/segundo grau. Não contar a rota como
CJPG até existir uma superfície oficial que identifique primeiro grau e cujo
detalhe público seja reproduzível.

## Identidade

- Tribunal: Tribunal de Justica de Santa Catarina.
- Familia tecnica: `html_jurisprudencia_eproc`.
- Categoria: `court_jurisprudence`.
- Entrada institucional: `https://www.tjsc.jus.br/web/tjsc/pesquisa-jurisprudencia`.
- Superficie de pesquisa observada:
  `https://eprocwebcon.tjsc.jus.br/consulta1g/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar`.
- Status do mapeamento: `live_validated` para busca; detalhe condicionado por
  controle de acesso da fonte.
- Status no NanoJuris: implementado para busca pública; inteiro teor é tentado
  sob demanda e pode retornar `access_control_required`.

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

O detalhe foi observado historicamente como HTTP 200 `text/html`, mas na
revalidação do ciclo 54 a fonte retornou uma página de controle de acesso. O
parser mantém separados o card resumido, o inteiro teor e a consulta
processual e nunca tenta contornar esse controle.

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

## Fixtures

- [x] Resultado HTML mínimo derivado do card TJSC versionado no teste:
  `tests/fixtures/tjsc_eproc_jurisprudencia_result.html`.
- [x] Formulário e paginação reduzidos, sem credenciais, em
  `tests/fixtures/tjsc_eproc_jurisprudencia_form.html`.
- [x] Resultado vazio em `tests/fixtures/tjsc_eproc_jurisprudencia_empty.html`.
- [x] Controle de acesso em
  `tests/fixtures/tjsc_eproc_jurisprudencia_access_control.html`; detalhe
  público permanece condicionado pela fonte.

Os fixtures são reduzidos e sanitizados; não contêm cookies, tokens ou corpos
de decisões reais. O estado de acesso do detalhe é sempre propagado ao
consumidor.

## Decisao de mapeamento

Promovido de `candidate_needs_har` para provider implementado porque chamadas
HTTP limpas retornaram conteúdo decisório real, campos canônicos e paginação.
O detalhe público continua sujeito a controle da fonte e o contrato não tenta
contorná-lo.

O contrato deve ser usado com:

1. fixture HTML de formulário e sucesso;
2. fixture de resultado vazio;
3. fixture de proteção/erro;
4. parser offline resiliente a labels e IDs dinâmicos;
5. teste offline de paginação e filtros de processo/data; a paginação live foi
   validada na Wave 2;
6. teste live opt-in com intervalo conservador.

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

## Evidência live ciclo 54 — 2026-09-05

- Páginas 1 e 2 com `responsabilidade civil`: HTTP 200 HTML, 2 registros por
  página, total remoto 785.591 e IDs sem sobreposição.
- A tentativa de detalhe do primeiro ID recebeu HTML de controle de acesso;
  foi classificada como `access_control_required`, sem mascaramento como vazio.
- Correção aplicada: IDs TJSC com 7 dígitos agora são aceitos pelo extrator
  específico do provider (o parser TJSP continua exigindo seu contrato próprio).
- Artefato redigido: `docs/provider-discovery/tjsc-eproc-live-20260905-cycle54.json`.
- Busca textual e paginação estão aptas à federação; inteiro teor permanece
  condicional e é reportado no trace.

## Referencias oficiais

- [Pesquisa de jurisprudencia do TJSC](https://www.tjsc.jus.br/web/tjsc/pesquisa-jurisprudencia)
- [Formulario publico eproc/TJSC](https://eprocwebcon.tjsc.jus.br/consulta1g/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar)
