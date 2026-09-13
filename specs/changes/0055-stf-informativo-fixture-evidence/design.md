# Design - Replay normalizado STF Informativo

A fixture contem um envelope `rows` com as chaves normalizadas pelo parser do
XLSX. Ela usa somente valores de fixture e nenhum dado pessoal. Um teste
provider-especifico passa essas linhas diretamente a
`parse_stf_informativo_rows`, enquanto os testes existentes continuam cobrindo
decodificacao XLSX, headers alterados, ZIP invalido e estados HTTP.

Assim a auditoria diferencia evidencia versionada de payload inline sem sugerir
que o replay seja uma copia do acervo oficial.
