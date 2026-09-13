# Design — família SJUR/TRE

O provider de família é um dispatcher fino. Ele mantém uma instância por UF,
normaliza a autoridade antes da construção do endpoint e reutiliza integralmente
o adapter específico, que já aplica os gates conservadores de grau e paginação.

IDs produzidos pela UF carregam o prefixo `tre_{uf}_sjur_jurisprudencia`; isso
permite recuperar detalhe/documento somente de um resultado previamente
observado. A família não tenta transformar o total da janela em total de
corpus e não faz fallback para outra UF.

O registro de catálogo é único (`tre_sjur_jurisprudencia`), enquanto a
superfície nacional continua separada por autoridade. Assim, métricas podem
mostrar cada TRE sem multiplicar código ou documentação contratual.
