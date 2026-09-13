# trf6_eproc_jurisprudencia

## Identidade
- Fonte oficial: TNU/eproc, TRF2/eproc e TRF6/eproc.
- Providers implementados: `tnu_eproc_jurisprudencia`, `trf2_eproc_jurisprudencia`
  e `trf6_eproc_jurisprudencia`.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `eproc_jurisprudencia`.
- URL inicial TNU: `https://eproctnu.cjf.jus.br/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar`.
- URL inicial TRF2: `https://eproc.trf2.jus.br/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar`.
- URL inicial TRF6: `https://eproc-jur.trf6.jus.br/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar`.
- Status de acesso: publico no probe limpo de 2026-08-07.

## Contrato HTTP
- Rotas:
  - `GET /eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar`
  - `POST /eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados`
  - `GET /eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/download_inteiro_teor&id_jurisprudencia=<id>` pendente de fixture por tribunal.
- Metodos: `GET` para formulario e inteiro teor; `POST` para resultados.
- Parametros obrigatorios minimos do POST:
  - `txtPesquisa`
  - `rdoCampo`
- Parametros opcionais observados:
  - `hdnExibirPesquisaAvancada`
  - `txtProcesso`
  - `dtDecisaoInicio`
  - `dtDecisaoFim`
  - `dtPublicacaoInicio`
  - `dtPublicacaoFim`
  - `chkAgruparResultados`
  - `selTipoDocumento[]`
  - `selOrigem[]`
- Paginacao: HTML com controles e cards `resultadoItem`; repetir contrato antes de coletar em escala.
- Ordenacao: nao mapeada nesta rodada.
- Filtros: texto, campo de busca, processo, tipo documental, origem e datas.

## Dados retornados
- Campos extraidos: numero CNJ, classe, relator, orgao julgador, datas, decisao/ementa, links.
- Campos canonicos: `CanonicalDecision`.
- Campos opcionais: origem, tipo documental, id de jurisprudencia, URL de inteiro teor.
- Campos instaveis: labels HTML e lista de origens variam por instancia.
- Inteiro teor: link publico esperado pelo padrao eproc; a rota foi validada para TNU,
  TRF2 e TRF6 em chamada live bounded (ciclo 43), com HTML textual e hash registrados
  sem persistir o corpo.
- Documentos vinculados: `id_jurisprudencia`.

## Comportamento observado
- Busca com resultado:
  - TNU: `txtPesquisa=aposentadoria`, `rdoCampo=I`, HTTP 200, `resultadoItem`.
  - TRF2: `txtPesquisa=aposentadoria`, `rdoCampo=I`, HTTP 200, `resultadoItem`.
  - TRF6: `txtPesquisa=aposentadoria`, `rdoCampo=I`, HTTP 200, `resultadoItem`.
- Origens observadas:
  - TNU: `TNU`.
  - TRF2: `TRF2`, `TRU2`, Turmas Recursais.
  - TRF6: `TRF6`, `TRU6`, Turmas Recursais e Varas Federais.
- Contrato de grau: nos formulários TRF2, TRF4 e TRF6, `selOrigem[]=1` é a
  origem oficial do próprio tribunal. Quando a consulta solicita
  `degree=second` ou `instance=second`, o adapter envia esse valor e valida a
  identidade canônica retornada; não assume grau apenas por HTTP 200.
- Tipos documentais observados no TRF2:
  - `Acordao`;
  - `Decisao monocratica`;
  - `Sumula`;
  - `Despacho/Decisao da Vice-Presidencia`;
  - `Sentenca`.
- Busca sem resultado: pendente.
- Erro HTTP esperado: pendente.
- Controle de acesso/captcha: nao observado no fluxo testado.
- Mudanca de layout: risco medio por HTML de sistema.

## Fixtures
- Sucesso TNU: `tests/fixtures/tnu_eproc_aposentadoria.html`.
- Sucesso TRF2: `tests/fixtures/trf2_eproc_aposentadoria.html`.
- Sucesso TRF6: `tests/fixtures/trf6_eproc_aposentadoria.html`.
- Vazio: coberto por parser eproc quando a fonte retorna formulario sem cards.
- Erro/acesso: coberto por respostas fake em
  `tests/test_eproc_jurisprudencia_federal.py`.
- Documento: resposta fake cobre o parser offline; a disponibilidade live por
  instancia está registrada em `docs/provider-discovery/eproc-detail-live-20260905-cycle43.json`.

## MCP e agentes
- Quando usar: consultas federais/TNU/TRF2/TRF6 por tema, ementa, inteiro teor ou numero.
- Quando pular: quando o usuario pedir fonte estadual que nao use eproc ou quando houver sinal de controle de acesso.
- Mensagem segura para o usuario: "A consulta usa jurisprudencia publica do eproc e retorna apenas conteudo acessivel em sessao limpa."
- Riscos: HTML volumoso, mudanca de labels e necessidade de rate limit.

## Proximos passos
- [x] Parametrizar provider eproc por base URL, tribunal e origens.
- [x] Criar fixtures publicas representativas de TNU, TRF2 e TRF6.
- [x] Reusar parser de `trf4_eproc_jurisprudencia`.
- [x] Validar rota de inteiro teor com `id_jurisprudencia` real de cada fonte
  (TNU, TRF2 e TRF6; ciclo 43; corpos não persistidos).
- [x] Adicionar testes de sucesso, vazio e acesso restrito.

## Revalidação de grau e detalhe (2026-09-08)

O smoke bounded `docs/provider-discovery/eproc-detail-live-20260908-cycle75.json`
confirmou busca e inteiro teor público para TNU, TRF2 e TRF6. A consulta live
adicional do TRF6 com `selOrigem[]=1` retornou dois cards `degree=second`; a do
TRF2 inicialmente expôs apenas o tipo documental, então o parser passou a usar
o hint de grau somente quando o filtro oficial de origem `1` foi enviado. O
resultado continua sujeito à validação canônica e o total permanece não
autoritativo após pós-filtro.
