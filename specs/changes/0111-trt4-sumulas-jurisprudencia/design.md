# Design — TRT4 Súmulas e precedentes

O provider usa `SharedHttpClient` com allowlist de `www.trt4.jus.br`, limite de
2 MB, sem retry automático e com estados explícitos de transporte. O HTML é
analisado em memória por BeautifulSoup. Títulos curados são deduplicados por
número de súmula, orientação ou processo; texto e documento são preservados
com proveniência. Links de documento só são registrados quando a página os
publica; âncoras vazias (`#`) não são convertidas em URL falsa.

O resultado recebe grau/instância de segundo grau por escopo oficial da
coleção, não por inferência do texto. A página é uma janela estática local e
permanece opt-in, pois não fornece contrato de pesquisa geral ou total do
acervo TRT4.
