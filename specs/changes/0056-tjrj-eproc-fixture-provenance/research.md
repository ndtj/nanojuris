# Pesquisa - Proveniencia TJRJ/eproc

O teste estadual reutilizava `tjsp_eproc_jurisprudencia_result.html`, que
continha processo `.8.26`, UF SP e links TJSP. Isso contaminava a evidencia do
TJRJ embora a classe do provider substituisse apenas `court` e `source`.

A fixture dedicada replica somente o contrato estrutural necessario ao parser,
com valores ficticios de RJ e sem qualquer corpo live.
