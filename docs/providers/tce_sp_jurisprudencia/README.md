# `tce_sp_jurisprudencia`

## Identidade

- Fonte oficial: Boletim de Jurisprudencia do TCE-SP.
- Categoria: `administrative_jurisprudence`.
- Familia tecnica: `catalogo_administrativo`.
- URL inicial: `https://www.tce.sp.gov.br/boletim-de-jurisprudencia`.
- Status de acesso: publico parcial.
- Status no NanoJuris: provider implementado.

## Contrato HTTP

- Rotas conhecidas:
  - `GET /boletim-de-jurisprudencia/sumulas`
  - `GET /boletim-de-jurisprudencia/publicacoes`
  - `GET /boletim-de-jurisprudencia/indice-alfabetico-remissivo`
- Metodos: `GET`.
- Paginacao: catalogos estaticos, a depender da pagina oficial.
- Busca dinamica: nao automatizada quando exigir reCAPTCHA.

## Dados retornados

- Campos extraidos:
  - numero da sumula;
  - enunciado;
  - historico;
  - fundamento;
  - edicao do boletim;
  - URL do boletim.
- Campos canonicos: `CanonicalPrecedent`.
- Inteiro teor: nao declarado como fluxo completo; URLs publicas sao
  preservadas.

## Comportamento observado

- Catalogos publicos: acessados por HTML.
- Busca dinamica: pode exigir reCAPTCHA e nao deve ser automatizada.
- Mudanca de layout: risco medio por paginas institucionais.

## Fixtures

- [ ] Lista de sumulas.
- [ ] Lista de publicacoes.
- [ ] Indice alfabetico.
- [ ] Pagina com estrutura alterada.

## MCP e agentes

- Quando usar: pesquisa de sumulas e jurisprudencia administrativa do TCE-SP.
- Quando pular: quando o usuario pedir acordaos judiciais ou jurisprudencia de
  tribunais judiciais.
- Mensagem segura: "Esta fonte e administrativa e cobre conteudo publico do
  TCE-SP, nao acordaos judiciais."
- Riscos: confundir controle externo/administrativo com jurisprudencia judicial.

## Proximos passos

- [ ] Completar fixtures de catalogo.
- [ ] Documentar limites da busca dinamica com reCAPTCHA.
- [ ] Separar melhor sumula, boletim e indice no catalogo MCP.
