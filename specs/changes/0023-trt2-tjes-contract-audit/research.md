# Research

Official evidence checked on 2026-08-28:

- TRT2 shell: `https://pje.trt2.jus.br/jurisprudencia/` returned HTTP 200.
- TRT2 options: `GET /juris-backend/api/opcoes` returned HTTP 200 JSON.
- TRT2 documents: `POST /juris-backend/api/documentos` returned
  `tokenDesafio` and `imagem`, not result records.
- TJES current portal returned HTTP 503.
- TJES legacy result URL returned HTTP 404.

Search-indexed TJES pages and official ementario PDFs are evidence of public
content, but not a current machine-readable search contract.
