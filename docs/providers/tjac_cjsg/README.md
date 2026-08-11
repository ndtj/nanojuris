# tjac_cjsg

## Identidade
- Fonte oficial: pesquisa publica de jurisprudencia CJSG/e-SAJ do TJAC.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_esaj_cjsg`.
- URL inicial: `https://esaj.tjac.jus.br/cjsg/consultaCompleta.do`.
- Status de acesso: resultado publico validado em sessao limpa em 2026-08-07.

## Contrato HTTP
- Rotas observadas:
  - `GET /cjsg/consultaCompleta.do`
  - `GET /cjsg/resultadoSimples.do?conversationId=&nuProcOrigem=<numero_cnj>&nuRegistro=`
- Exemplo publico usado no probe:
  - `0700309-51.2015.8.01.0001`
- Metodos: `GET` para formulario e resultado simples por numero.
- Paginacao: pendente.
- Busca textual completa: pendente.

## Dados retornados
- Campos observados:
  - numero CNJ;
  - ementa;
  - relator;
  - orgao julgador;
  - data de julgamento;
  - data de publicacao;
  - link/conteudo de inteiro teor.
- Campos canonicos: `CanonicalDecision`.
- Familia reutilizavel: parser CJSG/e-SAJ deve ser compartilhado com TJSP, TJMS e outros tribunais e-SAJ quando o HTML real permitir.

## Comportamento observado
- Formulario: HTTP 200, CJSG publico.
- Resultado por numero: HTTP 200 com conteudo juridico objetivo.
- Controle de acesso/captcha: nao observado no probe inicial.
- Risco: alto por HTML e-SAJ e possivel controle de acesso dinamico.

## Decisao
- Promover TJAC/CJSG como fonte forte para endurecer a familia e-SAJ.
- Criar fixture publica representativa antes de ampliar fetcher live.
- Nao usar rotas de captcha ou controle de acesso para bypass.

## MCP e agentes
- Quando usar: demonstracoes de CJSG/e-SAJ com fonte estadual que respondeu em sessao limpa.
- Quando pular: se a fonte retornar captcha, sessao vazia ou login.
- Mensagem segura para o usuario: "A busca usa jurisprudencia publica do TJAC/CJSG e retorna apenas conteudo disponivel sem validacao humana."

## Proximos passos
- [ ] Criar fixture de resultado simples por numero.
- [ ] Testar busca por termo em `consultaCompleta`.
- [ ] Validar inteiro teor.
- [ ] Reusar diagnosticos de `tjsp_cjsg`.
