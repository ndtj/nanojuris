# Design

O adapter usa somente endpoints REST públicos do DSpace da Biblioteca Digital
do TJMG. Uma busca é feita por coleção, os resultados são mesclados por ordem
de publicação e o total é a soma apenas quando as três respostas informam
`totalElements`. O item e o bitstream ORIGINAL são resolvidos lazy em
`get_document`, usando o transporte configurado e o limite de tamanho do
pipeline de documentos.

O formulário de jurisprudência legado continua separado: sua proteção por
CAPTCHA é registrada como bloqueio externo e não é contornada. A coleção DSpace
é uma superfície pública verificável, não uma afirmação de que todo o acervo
histórico do formulário esteja indexado.
