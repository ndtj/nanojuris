# Design

`DiscoveryCache.put` escreve em arquivo temporário no mesmo diretório e usa
`os.replace`, garantindo troca atômica no filesystem. `get` captura apenas
falhas de leitura/decodificação esperadas e retorna `None`; o chamador então
executa discovery normal. O temporário é removido em `finally`.

O padrão é uma adaptação conceitual do template, não uma cópia de código; o
comportamento permanece compatível com a API pública de `DiscoveryCache`.
