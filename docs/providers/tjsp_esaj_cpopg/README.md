# `tjsp_esaj_cpopg`

## Identidade

- Fonte oficial: Consulta Processual e-SAJ 1o Grau do TJSP.
- Categoria: `case_lookup`.
- Familia tecnica: `html_esaj_cpopg`.
- URL inicial: `https://esaj.tjsp.jus.br`.
- Status de acesso: publico parcial, com possibilidade de controle de acesso.
- Status no NanoJuris: provider implementado.

## Contrato HTTP

- Rotas conhecidas:
  - `GET /cpopg/search.do`
  - `GET /cpopg/show.do`
- Modos mapeados:
  - numero CNJ;
  - nome da parte;
  - documento da parte;
  - nome do advogado;
  - OAB;
  - precatoria;
  - documento de delegacia;
  - CDA.
- Paginacao: presente em listas publicas; precisa fixtures adicionais.

## Dados retornados

- Campos extraidos:
  - numero do processo;
  - status;
  - classe;
  - assunto;
  - comarca/origem;
  - unidade/vara;
  - juiz;
  - distribuicao;
  - numero de controle;
  - area;
  - partes;
  - movimentacoes;
  - URL do documento;
  - modo de busca;
  - papel do resultado;
  - data de recebimento.
- Campos canonicos: `CanonicalDocument` e `JurisprudenceResult`.
- Observacao critica: consulta processual, nao jurisprudencia decisoria.

## Comportamento observado

- Busca por numero: detalhe direto validado.
- Busca por parte e OAB: lista publica validada.
- Autos/documentos: podem ser restritos.
- Controle de acesso: a fonte pode exibir captcha ou validacao em algumas rotas.

## Fixtures

- [ ] Detalhe por numero CNJ.
- [ ] Lista por parte.
- [ ] Lista por OAB.
- [ ] Processo nao encontrado.
- [ ] Controle de acesso.

## MCP e agentes

- Quando usar: contexto processual publico com numero, parte ou OAB.
- Quando pular: pesquisa de tese, acordao ou jurisprudencia geral.
- Mensagem segura: "Esta fonte consulta dados processuais publicos do TJSP; nao
  substitui pesquisa de jurisprudencia."
- Riscos: agentes podem usar movimento processual como se fosse fundamento
  decisorio.

## Proximos passos

- [ ] Registrar como a fonte representa filtros, classes e tipos sem catalogo formal.
- [ ] Mapear indisponibilidade, hash e tamanho de inteiro teor.
- [ ] Separar claramente consulta processual de jurisprudencia no MCP.
