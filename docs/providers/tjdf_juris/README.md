# `tjdf_juris`

## Identidade

- Fonte oficial: jurisprudencia publica TJDFT/SISTJ.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_jurisprudencia_tribunal`.
- Uso preferencial: demonstracoes, estudos jurimetricos iniciais e validacao de
  fluxo MCP.
- Nivel atual esperado: 5.

## Contrato conhecido

O provider declara busca textual, resumo, intervalo de data, paginacao e
documento por identificador. Retorna `CanonicalDecision` e preserva campos como
ementa/resumo, relator, datas, tipo, tribunal e metadados brutos.

## Pontos fortes

- Fonte adequada para busca textual de jurisprudencia.
- Bom potencial para amostras comparativas.
- Boa candidata para exemplos publicos por ser menos sensivel que fontes com
  captcha frequente.

## Lacunas a aprofundar

- Completar dossie de parametros de detalhe e ordenacao.
- Criar fixtures adicionais para pagina vazia e variacao de pagina de detalhe.
- Documentar campos que variam por classe, orgao julgador e tipo decisorio.

## MCP e agentes

Recomendacao: boa fonte para perguntas naturais de jurisprudencia. O agente
deve usar page size pequeno, preservar traces e avisar quando a amostra for
exploratoria.

## Fixtures esperadas

- busca com resultado;
- busca vazia;
- pagina de detalhe;
- erro ou HTML inesperado.
