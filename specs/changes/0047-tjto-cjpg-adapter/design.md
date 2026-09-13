# Design - TJTO CJPG

O upstream Juscraper descreve uma busca HTML/Solr em
`POST /consulta.php`, diferenciando primeiro grau por
`tip_criterio_inst=1`. A primeira chamada bounded de 2026-09-01 recebeu HTTP
403 sem marcadores de resultado. O pacote permanece proposto e nao inclui
codigo runtime.

Antes de qualquer implementacao, e necessario reproduzir a rota com politica
publica documentada, confirmar filtros e mapear o detalhe `ementa.php` ou
`documento.php` sem contornar acesso.
