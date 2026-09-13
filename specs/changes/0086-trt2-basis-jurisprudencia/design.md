# Design

O adapter usa `JurisprudenceProvider` e `JurisprudenceQuery`. `GET /discover`
é compilado com escopo fixo da coleção e uma consulta por provider. Como o
total depois do filtro curado não é confiável, `total_known=False` impede parada
prematura da federação.

O parser converte cada cartão em `JurisprudenceResult` e registra somente links
oficiais. A recuperação do PDF é lazy e passa por `build_canonical_document`,
mantendo proveniência, hash, MIME e bytes. Erros são mapeados para as exceções
de transporte já usadas pela biblioteca.

O provider é uma fonte `curated_jurisprudence`: pode participar do roteamento
quando a consulta é trabalhista e de segundo grau, mas não declara que o BASIS
substitui a superfície PJe completa.
