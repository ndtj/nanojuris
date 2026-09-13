# Contrato de providers v2

O contrato v2 adiciona semântica explícita sem quebrar as assinaturas dos
providers existentes. A migração é incremental: um adapter só pode declarar
um comportamento quando houver evidência reproduzível (fixture, documentação
oficial ou chamada pública registrada).

O esquema serializável está em `provider-contract-v2.schema.json` e a matriz
de transição v1/v2 em `provider-contract-v2-compatibility.md`.

## Capacidades

`ProviderCapabilities` mantém `supported_filters` e `unsupported_filters` por
compatibilidade. O mapa opcional `filter_semantics` permite diferenciar:

- `native`: filtro enviado ao campo nativo da fonte;
- `translated`: filtro convertido para o vocabulário da fonte;
- `local_postfilter`: filtro aplicado localmente após a coleta;
- `validated_scope`: dimensão fixa (por exemplo grau/coleção) validada pelo
  adapter antes da chamada, sem parâmetro remoto inventado;
- `unsupported`: fonte não garante o filtro;
- `unverified`: ainda não há evidência suficiente.

`ordering_modes` e `detail_modes` registram, de forma declarativa, ordenações
e níveis de detalhe que o provider consegue sustentar. Ausência de uma entrada
é desconhecido, nunca uma afirmação de que o recurso não existe.

## Vocabulário semântico canônico

Além dos filtros legados de texto, data e identificador, a matriz v2 audita
estas dimensões de forma explícita: `case_class`, `judging_body`, `degree`,
`instance`, `branch`, `legal_area`, `authority`, `collection`,
`document_type`, `decision_type`, `judgment_date_from` e
`judgment_date_to`. Aliases em português (por exemplo, `classe`, `grau`,
`instancia`, `ramo`, `colecao` e `tipo_documento`) são normalizados pelo
cliente, mas não mascaram a ausência de suporte nativo. Cada provider deve
declarar `native`, `translated`, `local_postfilter`, `validated_scope`, `unsupported` ou
`unverified`; filtros ausentes nunca são enviados silenciosamente.

## Resultado seguro

`ProviderOutcome` é um envelope serializável para uma operação individual. Ele
diferencia resultado válido, vazio e parcial de falhas de consulta, bloqueio,
limite, timeout, indisponibilidade e mudança de parser. Mensagens passam por
`safe_error_message`, removendo credenciais, URLs com query sensível e e-mails
antes de chegarem a payloads ou logs públicos.

`ProviderOutcome.from_page` preserva `total`, paginação, completude e
`SourceTrace`; uma página incompleta nunca é apresentada como lista vazia
completa.

## Paginação e compatibilidade

`SearchPage` ganhou apenas metadados opcionais (`cursor`, `ordering` e
`filters_applied`) ao final do dataclass. Construtores históricos continuam
válidos. Providers que ainda não possuem cursor devem deixar o campo `None` e
manter seu modo de paginação anterior.

## Adoção

1. Registrar a evidência do endpoint e dos filtros.
2. Preencher capacidades v2 sem remover os campos legados.
3. Emitir um `ProviderOutcome` por chamada e manter o `SourceTrace` original.
4. Adicionar fixtures de sucesso, vazio, erro e resposta incompleta.
5. Só promover o provider após Ruff, mypy, testes offline e chamada live
   limitada passarem. CAPTCHA, login, WAF, rate limit e robots continuam
   bloqueios reais e não devem ser contornados.
