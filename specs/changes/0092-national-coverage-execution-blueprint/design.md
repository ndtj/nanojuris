# Design — cobertura nacional ouro

## 1. Modelo de superfície

O identificador estável é:

```text
<authority>/<branch>/<degree>/<instance>/<collection>/<provider>
```

`degree` e `instance` aceitam `first`, `second` e `unknown`; desconhecido não
é inferido por nome de endpoint. `collection` identifica CJPG, CJSG, SJUR,
EPROC, JURIS, PORTAL, INFORMATIVOS ou outra coleção comprovada.

O registro de superfície contém `provider`, `lifecycle`, `maturity`,
`live_status`, `contract_status`, `federation_status`, `document_capability`,
`last_live_check` e `evidence_ids`. O arquivo de template define o formato.

## 2. Pipeline por provider

```text
descoberta oficial → contrato → chamada bounded → parser → validação canônica
→ fixture → smoke opt-in → promoção técnica → inventário gerado
```

O parser não deve inferir grau por texto livre quando a fonte não o declara.
Nesse caso, o registro permanece `unknown` até evidência de primeira fonte.

## 3. Contrato de filtros

O compilador recebe a consulta canônica e produz `ProviderQueryPlan`:

```json
{
  "remote": {},
  "translated": {},
  "local": [],
  "ignored": [],
  "unsupported": [],
  "page_size": 20,
  "timeout_seconds": 8
}
```

Filtros identificadores, grau ou tipo documental não suportados devem gerar
diagnóstico explícito. Não se deve simular filtro remoto nem eliminar registros
sem indicar filtragem local.

## 4. Estados de acesso e resultado

O envelope de fonte usa os estados:

```text
success_with_results | authoritative_empty | unconfirmed_empty |
timeout | access_blocked | rate_limited | transport_error |
schema_invalid | partial | cancelled
```

`unconfirmed_empty` é usado quando a resposta não permite provar que a coleção
está vazia. `authoritative_empty` exige sinal explícito da fonte.

## 5. Documentos

`DocumentReference` deve manter URL allowlisted, URL final, MIME declarado e
observado, magic bytes, bytes lidos, hash, páginas, idioma, método de extração,
confiança e `source_trace`. Downloads são sob demanda e limitados; o cache é
efêmero e não pesquisável.

## 6. Juscraper

O trabalho de paridade compara comportamento, não código. O executor deve:

1. fixar commit e licença;
2. listar módulos e rotas;
3. reproduzir a chamada em fonte oficial;
4. registrar diferenças de campos e filtros;
5. escrever parser NanoJuris independente;
6. usar fixture e teste diferencial;
7. registrar qualquer bloqueio sem tentar evasão.

## 7. Federação

A federação recebe apenas providers com gate de promoção válido. O planner
reserva fontes primárias, precedentes e contextuais em papéis diferentes. A
ordem de chegada não altera a ordem consolidada; ondas posteriores apenas
recalculam o ranking antes da interação do usuário.

## 8. Observabilidade

Cada chamada produz `trace_id`, provider, endpoint lógico, latência, bytes,
status, páginas, filtros e motivo de parada. Logs não devem conter credenciais,
tokens, cookies, consulta original ou inteiro teor não minimizado.
