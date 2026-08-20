# Design

## Camadas

```text
Provider HTTP/browser
        |
Fetcher bounded -> HtmlDocument/payload JSON -> parser do provider
        |                                      |
SourceTrace + raw bytes                    JurisprudenceResult
                                               |
                                 normalização -> CanonicalDecision
                                               |
                                  dedupe/checkpoint -> SQLiteStore
```

## Compatibilidade

O parser compartilhado é um adapter, não uma reescrita automática dos providers.
O backend HTML será selecionado em runtime; dependências de performance ficam
opcionais e o fallback atual continua disponível.

## Persistência e retomada

O runner salva estado serializável com provider, consulta, próxima página,
identificadores vistos e contadores. O checkpoint será substituído de forma
atômica. Registros canônicos serão salvos por chave única existente no store.

## Observabilidade

Cada lote preserva source trace, hash de conteúdo, status de extração, número de
registros vistos/salvos/duplicados/inválidos e motivo de parada.
