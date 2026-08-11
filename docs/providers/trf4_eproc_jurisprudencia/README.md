# `trf4_eproc_jurisprudencia`

## Identidade

- Fonte oficial: jurisprudencia publica eproc/TRF4.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_jurisprudencia_eproc`.
- Uso preferencial: jurisprudencia federal e estudos com inteiro teor publico.
- Nivel atual esperado: 5.

## Contrato conhecido

O provider declara busca por texto integral, resumo, numero CNJ e intervalo de
data. Retorna decisoes canonicas e suporta fluxo de inteiro teor publico quando
disponivel.

## Pontos fortes

- Boa fonte para validar arquitetura eproc reutilizavel.
- Boa candidata para estudos jurimetricos federais.
- Menor risco operacional que fontes com captcha frequente.

## Lacunas a aprofundar

- Expandir fixtures por tipo decisorio e orgao julgador.
- Documentar paginacao, ordenacao e limites de consulta.
- Registrar comportamento de inteiro teor indisponivel.

## MCP e agentes

Recomendacao: fonte forte para perguntas naturais sobre jurisprudencia federal.
O agente deve preservar `document_url`, traces e indicar que a busca retorna
amostra conforme filtros publicos.

## Fixtures esperadas

- busca com resultado;
- zero resultado;
- inteiro teor publico;
- variacao de tipo decisorio.
