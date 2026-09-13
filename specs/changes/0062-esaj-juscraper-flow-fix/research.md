# Pesquisa - Contrato público eSAJ

- O Juscraper documenta um fluxo compartilhado para os tribunais eSAJ:
  `POST /cjsg/resultadoCompleta.do` seguido de `GET
  /cjsg/trocaDePagina.do?pagina=1` e GETs paginados.
- A resposta do POST é tratada como confirmação do envio; o HTML com os
  resultados é obtido pela rota de troca de página.
- O TJSP usa User-Agent de navegador e propaga `conversationId` extraído da
  primeira página para GETs posteriores.
- A rechecagem live do NanoJuris em 2026-09-01 encontrou controle de acesso no
  TJSP/CJSG; a correção não tenta contornar esse controle.

Fontes externas: repositório público `jtrecenti/juscraper`, arquivos
`src/juscraper/courts/_esaj/download.py` e
`src/juscraper/core/http.py`, snapshot MIT auditado no inventário local.
