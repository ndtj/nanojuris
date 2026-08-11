# `tjac_esaj_cpopg`

## Identidade

- Fonte oficial: Consulta Processual e-SAJ 1o Grau do TJAC.
- Categoria: `case_lookup`.
- Familia tecnica: `html_esaj_cpopg`.
- URL inicial: `https://esaj.tjac.jus.br`.
- Status de acesso: publico parcial, com possibilidade de controle de acesso.
- Status no NanoJuris: provider implementado.

## Contrato HTTP

- Rotas conhecidas:
  - `GET /cpopg/search.do`
  - `GET /cpopg/show.do`
- Metodos: `GET`.
- Busca validada: numero CNJ com redirect oficial `search.do -> show.do`.
- Busca por nome/OAB: ainda nao promovida para TJAC.

## Dados retornados

- Campos extraidos:
  - numero do processo;
  - status;
  - classe;
  - assunto;
  - comarca/origem;
  - vara/unidade;
  - distribuicao;
  - numero de controle;
  - area;
  - partes;
  - movimentacoes;
  - URL final.
- Campos canonicos: `CanonicalDocument` e `JurisprudenceResult`.
- Observacao critica: consulta processual, nao jurisprudencia decisoria.

## Comportamento observado

- Busca por numero: detalhe publico validado.
- Dados restritos: autos e documentos podem exigir permissao.
- Controle de acesso/captcha: nao deve ser contornado.

## Fixtures

- [ ] Detalhe por numero CNJ.
- [ ] Processo inexistente.
- [ ] HTML com controle de acesso.
- [ ] Variacao de partes/movimentos.

## MCP e agentes

- Quando usar: perguntas sobre processo publico identificado por CNJ.
- Quando pular: perguntas gerais sobre tese ou jurisprudencia.
- Mensagem segura: "Esta fonte consulta dados processuais publicos do TJAC, nao
  base de acordaos."
- Riscos: misturar linha do tempo processual com tese juridica.

## Proximos passos

- [ ] Validar busca por nome/OAB apenas se a fonte responder sem desafio.
- [ ] Salvar fixture de processo publico representativa.
- [ ] Reusar diagnosticos de acesso do e-SAJ/TJSP.
