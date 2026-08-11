# `comunica_pje`

## Identidade

- Fonte oficial: Comunica PJe / DJEN.
- Categoria: `judicial_communications`.
- Familia tecnica: `api_publica_comunicacoes`.
- URL inicial: `https://comunicaapi.pje.jus.br`.
- Status de acesso: publico, com possibilidade de indisponibilidade da fonte.
- Status no NanoJuris: provider implementado.

## Contrato HTTP

- Rota conhecida:
  - `GET /api/v1/comunicacao`
- Parametros observados:
  - texto livre;
  - `siglaTribunal`;
  - `numeroProcesso`;
  - `dataDisponibilizacaoInicio`;
  - `dataDisponibilizacaoFim`;
  - pagina.
- Paginacao: a API pode devolver ate 100 itens por pagina mesmo quando o
  provider solicita tamanho menor.
- Ordenacao: pendente de documentacao formal.

## Dados retornados

- Campos extraidos:
  - `communication_id`;
  - tribunal;
  - numero do processo;
  - classe processual;
  - data de disponibilizacao/publicacao;
  - tipo de comunicacao;
  - orgao/fonte;
  - resumo/texto;
  - URL do documento.
- Campos canonicos: atualmente normalizado como `CanonicalDecision` por
  compatibilidade de pipeline.
- Observacao critica: nao e base de jurisprudencia, acordaos ou precedentes.

## Comportamento observado

- Busca com resultado: retorna JSON publico com comunicacoes.
- Busca sem resultado: deve ser tratada como vazio, nao erro.
- Erro esperado: indisponibilidade ou erro HTTP da API.
- Controle de acesso/captcha: nao deve haver tentativa de bypass.

## Fixtures

- [ ] Sucesso com comunicacao publica.
- [ ] Vazio por termo/data.
- [ ] Erro HTTP/indisponibilidade.
- [ ] Variacao de tribunal/origem.

## MCP e agentes

- Quando usar: monitoramento objetivo de comunicacoes judiciais publicas.
- Quando pular: pesquisa de jurisprudencia, tese, acordao ou precedente.
- Mensagem segura: "Esta fonte retorna comunicacoes publicas do PJe/DJEN, nao
  jurisprudencia decisoria."
- Riscos: agentes podem confundir comunicacao processual com tese juridica.

## Proximos passos

- [ ] Isolar contrato de erros HTTP 500 e janelas de data.
- [ ] Documentar diferenca entre DJEN/Comunicacoes PJe e jurisprudencia.
- [ ] Adicionar matriz de campos por tribunal/origem quando houver variacao.
- [ ] Criar fixtures de sucesso, vazio e erro.
