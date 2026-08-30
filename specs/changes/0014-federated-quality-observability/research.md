# Pesquisa

A auditoria 0013 encontrou isolamento por item no `CollectionRunner`, mas o
fluxo federado ainda canonicaliza uma página inteira de uma vez. Também foi
identificado que mensagens de erro podem variar em tamanho e que a métrica de
execução precisa de semântica explícita.
