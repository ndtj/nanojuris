# `stm_jurisprudencia`

## Identidade

- Fonte oficial: Jurisprudencia da Justica Militar da Uniao / STM.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_jurisprudencia_eproc`.
- URL inicial: `https://jurisprudencia.stm.jus.br`.
- Status de acesso: publico parcial; inteiro teor pode depender de resposta do
  eproc.
- Status no NanoJuris: provider implementado.

## Contrato HTTP

- Rotas conhecidas:
  - `GET /consulta.php?search_filter_option=jurisprudencia&...`
  - `GET https://eproc2g.stm.jus.br/eproc_2g_prod/externo_controlador.php?acao=visualizar_acordao&uuid=<uuid>`
- Metodos: `GET`.
- Parametros usados: texto, ementa/resumo, numero do processo e intervalo de
  datas.
- Paginacao: pendente de estabilizacao documental.
- Facetas: observadas no portal, ainda nao promovidas como contrato estavel.

## Dados retornados

- Campos extraidos:
  - numero do processo;
  - classe;
  - relator;
  - assunto;
  - data de julgamento;
  - data de publicacao;
  - ementa/resumo;
  - URL do documento;
  - `uuid`.
- Campos canonicos: `CanonicalDecision` e `CanonicalDocument`.
- Inteiro teor: suportado quando a URL publica do eproc responder sem controle
  de acesso.

## Comportamento observado

- Busca com resultado: HTML de primeira pagina parseado pelo provider.
- Busca sem resultado: deve gerar pagina vazia.
- Controle de acesso: o provider deve parar quando houver bloqueio, login ou
  desafio.
- Mudanca de layout: risco medio por HTML institucional/eproc.

## Fixtures

- [ ] Busca com multiplos resultados.
- [ ] Busca vazia.
- [ ] Inteiro teor por `uuid`.
- [ ] HTML com labels acentuados/variantes.
- [ ] Controle de acesso esperado.

## MCP e agentes

- Quando usar: consultas de jurisprudencia militar e estudos setoriais.
- Quando pular: quando a fonte indicar controle de acesso ou retorno sem
  container de resultado.
- Mensagem segura: "A consulta usa jurisprudencia publica do STM e preserva a
  URL oficial do documento."
- Riscos: amostra setorial nao representa jurisprudencia brasileira geral.

## Proximos passos

- [ ] Documentar paginacao remota e facetas se forem estaveis.
- [ ] Adicionar fixtures de pagina vazia, multiplos resultados e inteiro teor.
- [ ] Mapear variacoes de labels no HTML.
