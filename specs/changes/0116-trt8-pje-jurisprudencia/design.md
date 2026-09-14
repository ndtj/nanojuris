# Design — TRT8 PJe

```text
PJe SPA oficial
   -> POST /filtros (contrato/agregações)
   -> POST /documentos (janela paginada de acórdãos de 2º grau)
   -> POST /documentos/{id} (ementa, dispositivo e inteiro teor HTML)
   -> JurisprudenceResult / CanonicalDocument
```

O backend retorna UTF-8 JSON sem charset confiável; o transporte do NanoJuris
decodifica o corpo UTF-8 antes do parser. O provider usa uma requisição de
busca por página e uma requisição de detalhe somente quando solicitada.

O contrato exige `hits` inteiro e lista `documents`. Registros fora de segundo
grau ou que não sejam acórdãos são rejeitados como schema/contrato inválido,
pois não podem contaminar a superfície CJSG.
