# `tjrj_eproc_jurisprudencia`

## Identidade

- Fonte oficial: modulo de jurisprudencia do eproc/TJRJ.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_jurisprudencia_eproc`.
- URL inicial: `https://eproc1g.tjrj.jus.br/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar`.
- Status de acesso: rota publica revalidada; paginas consecutivas retornaram
  cards e IDs novos na Wave 2.
- Status no NanoJuris: implementado para busca e inteiro teor publico.

O TJRJ mantem bases distintas durante a transicao do sistema: o eJURIS legado
e o eproc. Este dossie cobre somente o eproc. O eJURIS nao deve ser tratado
como fallback automatico, pois possui contrato WebForms proprio.

## Contrato HTTP observado

- Formulario:
  - `GET /eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar`
- Resultados:
  - `POST /eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados`
- Inteiro teor:
  - `GET /eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/download_inteiro_teor&id_jurisprudencia=<id>`
- Metodo de busca: `application/x-www-form-urlencoded`.
- Payload minimo reproduzido:
  - `txtPesquisa=dano moral`;
  - `rdoCampo=I`;
  - campos de pesquisa avancada vazios;
  - `chkAgruparResultados=on`.
- Campos opcionais aceitos pela familia eproc:
  - `txtProcesso`;
  - `dtDecisaoInicio`, `dtDecisaoFim`;
  - `dtPublicacaoInicio`, `dtPublicacaoFim`;
  - `selTipoDocumento[]`;
  - `selOrigem[]`.

## Evidencia de sucesso

Probe executado em 2026-08-10 com `requests`, sem cookie pessoal, login,
captcha, token privado ou sessao de navegador:

- consulta: `dano moral`;
- resposta: HTTP 200, HTML ISO-8859-1;
- resultado: 10 cards `resultadoItem` na pagina retornada;
- campos observados: numero CNJ, classe, tipo documental, orgao julgador,
  data de julgamento, data de publicacao, texto decisorio e links;
- inteiro teor: link publico com `id_jurisprudencia` e termos pesquisados.

O primeiro resultado observado continha, entre outros, `AC - Apelacao Civel`,
`7a Camara de Direito Privado`, UF `RJ` e um processo CNJ. Datas devem ser
preservadas como vieram da fonte e validadas antes de qualquer analise: o
probe tambem encontrou uma data de julgamento posterior a data de publicacao,
um possivel dado inconsistente da origem.

## Dados retornados

- Campos canonicos:
  - numero do processo;
  - tipo decisorio;
  - classe;
  - relator;
  - orgao julgador;
  - data de julgamento;
  - data de publicacao;
  - ementa/decisao;
  - URL do processo;
  - URL de inteiro teor.
- Identificador tecnico: `id_jurisprudencia` numerico.
- Codificacao: resposta observada como `iso-8859-1`; parser deve respeitar a
  codificacao declarada pela resposta e testar acentuacao.
- Paginacao: o contrato compartilhado envia `hdnPaginaAtual`,
  `selTamanhoPagina` e a rota AJAX declarada por `hdnUrlPaginar`; a pagina
  seguinte nao foi promovida porque a rodada live de 2026-08-16 nao encontrou
  cards de resultado.

## Limites e controles

- A disponibilidade publica pode mudar sem aviso.
- O eproc do TJRJ e uma base recente; a propria fonte informa coexistencia
  com o eJURIS legado.
- O provider deve retornar `SourceTrace`, URL original e payload efetivo.
- O provider nao deve tentar contornar captcha, bloqueio, WAF ou limites.
- Resultado vazio, indisponibilidade e alteracao de parser sao estados
  diferentes e devem ser expostos ao MCP.
- Texto do card e inteiro teor sao campos distintos; nao rotular o primeiro
  como PDF ou documento integral.

## Fixtures necessarias

- [x] `tests/fixtures/tjrj_eproc_jurisprudencia_result.html` (replay sintetico
  com UF RJ e processo `.8.19`).
- [x] `tests/fixtures/tjrj_eproc_jurisprudencia_empty.html` (pagina publica sem
  cards).
- [x] `tests/fixtures/tjrj_eproc_jurisprudencia_access_control.html` (desafio
  sintetico, nunca tratado como vazio).
- [x] Sucesso por numero de processo.
- [x] Resultado vazio.
- [x] Paginacao ou limite de resultados.
- [x] Inteiro teor publico com `id_jurisprudencia` real.
- [x] Resposta de acesso bloqueado/indisponibilidade.

## MCP e agentes

- Quando usar: busca de jurisprudencia recente do TJRJ no acervo eproc por
  tema, ementa, numero, classe, origem ou intervalo de datas.
- Quando complementar: consultar tambem o provider eJURIS quando este tiver
  contrato independente e acesso reproduzivel.
- Mensagem segura: "A consulta usa o modulo publico de jurisprudencia eproc
  do TJRJ; a base eproc e distinta do acervo eJURIS legado."

## Implementacao 2026-08-11

`TjrjEprocJurisprudenciaProvider` usa o parser eproc compartilhado, mas declara
o host, tribunal, identificador e trace do TJRJ. O runtime classifica resposta
sem cards como alteracao de contrato, sem converter o caso em vazio. A base
eproc continua separada do eJURIS legado.

## Fechamento do contrato local

- [x] Sucesso por numero de processo: `tests/fixtures/tjrj_eproc_jurisprudencia_result.html`.
- [x] Resultado vazio: `tests/fixtures/tjrj_eproc_jurisprudencia_empty.html`.
- [x] Paginacao/limite: janela de tres paginas validada na evidencia live de
      2026-08-16; o parser preserva o limite remoto.
- [x] Inteiro teor publico: o teste de runtime valida `id_jurisprudencia` e
      `SourceTrace` sem persistir corpo externo.
- [x] Controle de acesso: `tests/fixtures/tjrj_eproc_jurisprudencia_access_control.html`.
- [x] O parser compartilhado foi comparado com os labels especificos do TJRJ
      e a base continua separada do eJURIS legado.
- [x] Testes opt-in e chamadas live permanecem bounded e sem bypass.

Os artefatos de resultado, vazio e controle sao sanitizados; a evidencia live
continua sendo uma fotografia de disponibilidade e nao implica SLA.

## Proximos passos

Monitorar periodicamente a disponibilidade publica e qualquer alteracao do
markup, mantendo a coleta bounded e sem bypass de controles de acesso.

## Validacao live 2026-08-11

- GET do formulario e POST `listar_resultados` responderam HTTP 200; foram observados 10 cards com ementa, processo e relator.
- O payload minimo usa `txtPesquisa`, `rdoCampo`, `hdnExibirPesquisaAvancada` e `chkAgruparResultados`.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Revalidacao de capacidade - 2026-08-16

- A consulta controlada `transporte aereo dano moral`, `page_size=25`, retornou
  25 IDs novos em cada uma das paginas 1, 2 e 3; total remoto observado: 187.
- Estado: `valid` para a paginacao observada. A rodada anterior sem cards segue
  registrada como instabilidade histórica, não como resultado vazio.
- O provider pode ser usado para coleta paginada dentro do contrato observado,
  mantendo rate limit e tratamento explícito de alteração de fonte.

Evidencia estruturada: `docs/validation/runs/20260816T094054Z-wave2-acceptance-20260816.json`.

## Rechecagem de primeiro grau - 2026-09-10

Uma sonda bounded repetiu o fluxo público do eproc/TJRJ com `degree=first`,
`instance=first` e origem `primeiro_grau`. A fonte respondeu HTTP 200, mas os
cards não apresentaram identidade consistente de primeiro grau; o parser rejeitou
a página como incompatível. A evidência redigida está em
`docs/provider-discovery/tjrj-first-degree-eproc-boundary-live-20260910.json`.
O binding continua restrito ao contrato de segundo grau e não é contado como
CJPG.

## Referencias oficiais

- https://portaltj.tjrj.jus.br/web/portal-conhecimento/consulta-a-jurisprudencia
- https://eproc1g.tjrj.jus.br/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar
- https://www.tjrj.jus.br/web/portal-conhecimento/noticias/noticia/-/visualizar-conteudo/5736540/405630882
