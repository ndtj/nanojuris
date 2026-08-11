# `tjsp_nugepnac`

## Identidade

- Fonte oficial: NugepNac/TJSP.
- Categoria: `court_precedents`.
- Familia tecnica: `catalogo_precedentes`.
- URL inicial: `https://www.tjsp.jus.br/NugepNac`.
- Status de acesso: publico parcial.
- Status no NanoJuris: provider implementado.

## Contrato HTTP

- Rotas conhecidas:
  - `GET /NugepNac/Irdr`
  - `GET /NugepNac/Iac`
  - `GET /NugepNac/(Irdr|Iac)/DetalheTema?codigoNoticia=<id>&pagina=1`
- Metodos: `GET`.
- Modos de busca: texto, numero, tipo de precedente e detalhe de catalogo.
- Paginacao: pagina de detalhe usa `pagina=1`; demais fluxos precisam
  aprofundamento.

## Dados retornados

- Campos extraidos:
  - numero do tema;
  - tipo de precedente;
  - status;
  - numero do processo;
  - assunto;
  - orgao julgador;
  - relator;
  - data de admissao;
  - data de julgamento de merito;
  - questao;
  - tese;
  - links de decisoes relacionadas.
- Campos canonicos: `CanonicalPrecedent`.
- Inteiro teor: nao declarado; links CJSG podem exigir verificacao separada.

## Comportamento observado

- Catalogo publico em HTML institucional.
- Pagina de detalhe contem questao e tese.
- Links de inteiro teor podem apontar para rotas CJSG com controle.

## Fixtures

- [ ] Lista IRDR.
- [ ] Lista IAC.
- [ ] Detalhe por `codigoNoticia`.
- [ ] Tema sem tese.
- [ ] Link relacionado indisponivel.

## MCP e agentes

- Quando usar: pesquisa de IRDR/IAC e precedentes locais do TJSP.
- Quando pular: amostragem decisoria comum ou acordaos sem vinculacao a tema.
- Mensagem segura: "Esta fonte cobre precedentes qualificados do TJSP, nao toda
  a jurisprudencia do tribunal."
- Riscos: tratar catalogo de precedentes como base exaustiva de decisoes.

## Proximos passos

- [ ] Completar dossie com casos reais publicos.
- [ ] Criar fixtures de lista e detalhe.
- [ ] Documentar criterio de atualizacao/sincronizacao do catalogo.
