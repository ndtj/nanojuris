# Validação live: TJCE SJURIS

- Data: 2026-08-16 08:14:31 BRT.
- Consulta: `transporte aereo dano moral`.
- Endpoint: `POST https://gateway.tjce.jus.br/sjuris/api/v1/jurisprudencia/`.
- Resultado: HTTP 200, total remoto 266 e 5 resultados na primeira página.
- Inteiro teor: `conteudo` presente nos 5 itens observados.
- Paginação: página 2 retornou 5 IDs novos.
- PDF: o campo contratual existe, mas nenhum dos 5 itens desta rodada trouxe
  `pdfAutenticadoBase64`; não foi anunciado como disponibilidade garantida.
- Limite observado: `size=50` e `size=100` retornaram HTTP 504; o provider
  limita o tamanho efetivo a 20.

O JSON desta rodada é a evidência machine-readable para o catálogo e para o
Studio/MCP. A fonte está implementada e validada para busca textual pública,
mas permanece abaixo de Gold enquanto filtros avançados e detalhe independente
não forem reproduzidos.
