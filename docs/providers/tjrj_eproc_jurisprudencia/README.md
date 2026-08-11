# `tjrj_eproc_jurisprudencia`

## Identidade

- Fonte oficial: modulo de jurisprudencia do eproc/TJRJ.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_jurisprudencia_eproc`.
- URL inicial: `https://eproc1g.tjrj.jus.br/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar`.
- Status de acesso: publico, validado em sessao HTTP limpa.
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
- Paginacao: controles HTML presentes; contrato de pagina seguinte ainda
  precisa de fixture antes de coleta em escala.

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

- [ ] Sucesso com termo (`dano moral`).
- [ ] Sucesso por numero de processo.
- [ ] Resultado vazio.
- [ ] Paginacao ou limite de resultados.
- [ ] Inteiro teor publico com `id_jurisprudencia` real.
- [ ] Resposta de acesso bloqueado/indisponibilidade.

## MCP e agentes

- Quando usar: busca de jurisprudencia recente do TJRJ no acervo eproc por
  tema, ementa, numero, classe, origem ou intervalo de datas.
- Quando complementar: consultar tambem o provider eJURIS quando este tiver
  contrato independente e acesso reproduzivel.
- Mensagem segura: "A consulta usa o modulo publico de jurisprudencia eproc
  do TJRJ; a base eproc e distinta do acervo eJURIS legado."

## Implementacao 2026-08-11

`TjrjEprocJurisprudenciaProvider` usa o parser eproc compartilhado, mas declara
o host, tribunal, identificador e trace do TJRJ. Busca, normalizacao dos cards,
download do inteiro teor e classificacao de controles de acesso estao
disponiveis no runtime. A base eproc continua separada do eJURIS legado.

## Proximos passos

1. Capturar uma fixture pequena e estavel de sucesso, vazio e detalhe.
2. Reusar o parser eproc somente depois de comparar todos os labels do TJRJ.
3. Validar o link de inteiro teor com um identificador real.
4. Adicionar fixtures especificas do TJRJ antes de coleta em escala.
5. Adicionar teste live opt-in com baixa frequencia e limite pequeno.

## Validacao live 2026-08-11

- GET do formulario e POST `listar_resultados` responderam HTTP 200; foram observados 10 cards com ementa, processo e relator.
- O payload minimo usa `txtPesquisa`, `rdoCampo`, `hdnExibirPesquisaAvancada` e `chkAgruparResultados`.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/lucmolero/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Referencias oficiais

- https://portaltj.tjrj.jus.br/web/portal-conhecimento/consulta-a-jurisprudencia
- https://eproc1g.tjrj.jus.br/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar
- https://www.tjrj.jus.br/web/portal-conhecimento/noticias/noticia/-/visualizar-conteudo/5736540/405630882
