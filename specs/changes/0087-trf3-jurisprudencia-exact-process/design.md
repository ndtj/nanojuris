# Design — TRF3 acórdãos por processo exato

## Rotas

```text
GET /acordaos/Acordao/PesquisarDocumento?processo=<20 dígitos>
GET /acordaos/Acordao/BuscarDocumentoPje/<id>
```

O primeiro endpoint é a única operação de busca implementada. Cada link de
data é convertido em um `JurisprudenceResult`; o segundo endpoint é buscado
somente quando `fetch_details=true` ou por `get_document` explícito.

## Limites deliberados

- sem tentativa de descobrir ou reproduzir o formulário textual geral;
- sem login, CAPTCHA, WAF bypass, replay de cookie ou relaxamento TLS;
- no máximo 20 documentos por processo e uma página remota;
- `supports_unified_search=false`, `opt_in_unified_search=true`;
- timeout e bloqueio permanecem visíveis no trace.

## Qualidade

Fixtures cobrem lista com duas datas, lista vazia autoritativa, shape
desconhecido e documento HTML. O parser rejeita resposta sem cabeçalho ou sem
links de documento. A rota pública observada é federal e de segundo grau;
isso não é extrapolado para o formulário de texto.

## Promoção

Somente após live direta reproduzir a lista e ao menos um detalhe, além de
verificação de identidade, tamanho/MIME e smoke opt-in. Até então a fonte é
diagnóstica e não altera a busca federada padrão.
