# TJSE - Pesquisa de Jurisprudencia Judicial

Status atual: `blocked_or_inconclusive` para busca decisoria automatizada.

## Identidade Da Fonte

- Tribunal: Tribunal de Justica do Estado de Sergipe.
- Portal oficial: `https://www.tjse.jus.br/portal/consultas/jurisprudencia/judicial`.
- Superficie de pesquisa: `https://www.tjse.jus.br/Dgorg/paginas/jurisprudencia/consultarJurisprudencia.tjse`.
- Categoria: jurisprudencia judicial estadual.
- O portal principal carrega a pesquisa em um `iframe`.

## Fluxo Observado

A superficie de pesquisa responde com um formulario JSF/PrimeFaces publico,
contendo filtros para:

- termo livre, numero do processo e numero CNJ;
- acordaos ou decisoes monocraticas;
- segundo grau ou turma recursal;
- relator, orgao julgador e classe processual;
- periodo de distribuicao ou julgamento;
- pesquisa na ementa e no voto.

O formulario usa `POST` para a propria rota, `javax.faces.ViewState` dinamico e
uma sessao `JSESSIONID` criada no carregamento inicial. Esses valores devem ser
obtidos por sessao e nunca ficar hardcoded.

## Reproducao Controlada

Com uma sessao HTTP nova, foi reproduzido:

1. `GET` da superficie de pesquisa.
2. Leitura do formulario e do `javax.faces.ViewState` atual.
3. `POST` com o termo `dano moral`, tipo `AC`, competencia `SG` e botao de
   pesquisa.

O retorno foi HTTP 200 e a pagina continuou contendo os filtros, mas o resultado
funcional foi a mensagem `Captcha invalido`. Nao houve decisoes, ementas ou
links de inteiro teor reproduziveis na sessao automatizada.

## Decisao De Mapeamento

Classificacao: `blocked_or_inconclusive`.

O formulario e uma evidencia relevante de uma base jurisprudencial publica,
mas a rota de resultados ainda nao esta validada para uso automatizado sem a
etapa de protecao. O NanoJuris nao deve simular ou contornar captcha, Turnstile,
tokens de desafio ou controles de frequencia.

## Promocao Futura

Para mudar para `candidate_ready`, sera necessario um HAR limpo do fluxo normal
realizado por um usuario, contendo:

- requisicao de busca com token emitido legitimamente pela pagina;
- resposta com pelo menos uma decisao real;
- processo, classe, orgao, relator, datas, ementa e link de inteiro teor,
  quando publicados;
- paginacao ou limite de resultados;
- comportamento de busca vazia e de erro.

Cookies pessoais, credenciais e tokens de sessao nao devem ser versionados.

## Validacao live 2026-08-11

- O formulario JSF respondeu HTTP 200 e confirmou filtros, ViewState, datas e botoes de pesquisa.
- O bundle referencia Cloudflare Turnstile; nenhuma busca foi promovida sem token humano autorizado.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/lucmolero/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Fontes Oficiais

- [Pagina de jurisprudencia judicial do TJSE](https://www.tjse.jus.br/portal/consultas/jurisprudencia/judicial)
- [Pesquisa de jurisprudencia do TJSE](https://www.tjse.jus.br/Dgorg/paginas/jurisprudencia/consultarJurisprudencia.tjse)
- [Regimento Interno do TJSE](https://www.tjse.jus.br/portal/arquivos/documentos/publicacoes/legislacao/tjse/novo_regimento_interno_tjse.pdf?v=18032024)
