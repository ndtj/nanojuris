# `tjsp_eproc_jurisprudencia`

## Identidade

- Fonte oficial: Jurisprudencia eproc/TJSP.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_jurisprudencia_eproc`.
- URL inicial: `https://eproc-consulta.tjsp.jus.br/consulta_1g`.
- Status de acesso: publico parcial, com risco de controle de acesso.
- Status no NanoJuris: provider implementado.

## Contrato HTTP

- Rotas conhecidas:
  - `POST /externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados`
  - `GET /externo_controlador.php?acao=jurisprudencia@jurisprudencia/download_inteiro_teor&id_jurisprudencia=<id>`
- Parametros: texto integral, ementa/resumo, numero CNJ, intervalo de datas e
  origem.
- `source_origin`: aceita `colegio_recursal`, `primeiro_grau` e `segundo_grau`.
- Paginacao/ordenacao: pendente de documentacao completa.

## Dados retornados

- Campos extraidos:
  - numero do processo;
  - tipo decisorio;
  - classe;
  - relator;
  - orgao julgador;
  - data de julgamento;
  - data de publicacao;
  - resumo/ementa;
  - URL do documento;
  - URL de inteiro teor;
  - `id_jurisprudencia`;
  - origem.
- Campos canonicos: `CanonicalDecision`.
- Inteiro teor: ainda nao declarado como `supports_full_text`; a rota pode
  redirecionar para controle de acesso.

## Comportamento observado

- Rota publica descoberta e validada por requests limpo em 2026-08-02.
- Cards de resultado trazem texto decisorio.
- Inteiro teor separado pode exigir validacao.
- Mudancas de hash/layout/filtros devem ser esperadas.

## Fixtures

- [ ] Busca por termo.
- [ ] Busca por frase exata.
- [ ] Busca por origem.
- [ ] Resultado vazio.
- [ ] Redirecionamento/controle de acesso no inteiro teor.

## MCP e agentes

- Quando usar: jurisprudencia eproc/TJSP por origem e texto.
- Quando pular: quando o usuario precisar de inteiro teor garantido e a fonte
  nao entregar documento publico.
- Mensagem segura: "A busca retorna cards publicos de jurisprudencia eproc/TJSP;
  inteiro teor depende de validacao publica da fonte."
- Riscos: confundir texto do card com inteiro teor integral.

## Proximos passos

- [ ] Aprofundar contrato de `source_origin`.
- [ ] Validar estrategia de inteiro teor/documentos quando disponivel.
- [ ] Documentar limites por primeiro grau, segundo grau e colegio recursal.
- [ ] Criar dicionario de filtros aceitos.
