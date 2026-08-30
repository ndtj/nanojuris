# Design

## Pipeline de coleta

Cada resultado será canonicalizado isoladamente quando necessário. Falhas de
um item incrementam `invalid_records` e entram no registro de falhas com fonte,
página e classe do erro; itens válidos seguem o fluxo de checkpoint e storage.
O lote só será interrompido quando não houver nenhum item aproveitável ou
quando a falha for estrutural da página.

## Identidade

A ordem da chave será: ID estável com `source`; número CNJ normalizado; número
local com `source` e tribunal; por fim um digest determinístico de campos
semânticos. A chave não deve depender de `hash()` do processo nem de texto
integral sensível.

## Observabilidade

O envelope de busca mantém `searched_sources`, `skipped_sources`, erros e
completude. Falhas permanecem distintas de vazio. Testes validarão a partição
sem sobreposição e a preservação do motivo.

## Segurança e compatibilidade

Não serão adicionados segredos aos artefatos. A alteração de identidade será
acompanhada de testes de compatibilidade e nota de migração; o comportamento
de deduplicação pode mudar apenas para evitar colisões incorretas.
