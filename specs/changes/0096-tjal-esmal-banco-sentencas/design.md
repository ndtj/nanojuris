# Design — TJAL ESMAL Banco de Sentenças

## Fluxo

```text
GET formulario/resultado
  -> parsear linhas Data/Título/PDF
  -> validar host e extensão do PDF
  -> CanonicalDecision (primeiro grau / CJPG curado)
  -> get_document opcional com política compartilhada
```

O endpoint público usa `cat` para categoria e `text` para palavra-chave. A
primeira página e as páginas seguintes são independentes e o total do acervo
permanece desconhecido; `SearchPage.total_known` será falso.

## Limites

- HTML de busca: 2 MiB.
- PDF: 10 MiB e 300 páginas.
- 20 resultados por página observada; máximo local 100.
- Uma requisição de busca por chamada e uma requisição de documento somente por
  registro observado.
- Respeitar `rate_limit_interval` do transporte compartilhado.

## Identidade e documentos

A própria página oficial identifica a coleção como Banco de Sentenças da ESMAL.
Isso prova primeiro grau/`sentenca`, mas não tribunal de origem individual além
de TJAL; o campo fica no `raw` e no `field_provenance`. O PDF continua ligado
ao resultado por URL e hash, e texto vazio é `extraction_status=empty`.

## Segurança e uso responsável

Hosts permitidos: `esmal.tjal.jus.br` para busca e `intranetlegado.tjal.jus.br`
para os PDFs explicitamente ligados pela página. Não seguir URLs inventadas,
não enumerar hashes, não ignorar TLS e não tentar superar autenticação ou
desafio.
