# Pesquisa - Fallback HTML TJES/CJSG

- A chamada publica bounded de 2026-09-01 retornou JSON `pje2g` com os campos
  `ementa`, `ementa_html`, `acordao` e `acordao_html` no mesmo documento.
- O contrato atual ja preserva `raw`, mas o parser usa apenas os campos planos.
- O fallback segue o padrao ja utilizado por outros providers NanoJuris com
  BeautifulSoup e nao importa codigo Juscraper em runtime.
- A resposta live nao sera copiada para o repositorio; a fixture sera
  sanitizada e minima.
