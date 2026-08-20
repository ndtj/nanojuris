# Design — contrato unificado orientado a evidências

## Camadas

1. `ProviderCapabilities`: declaração operacional por fonte.
2. `audit_unified_contract.py`: matriz derivada offline, combinando runtime, smoke e discovery.
3. `routing.py`: decisão conservadora de consultar, pular ou advertir.
4. `client.search_many`: envelope federado, deduplicação e completude por fonte.
5. Dossiê, contrato de fonte, fixture e teste: evidência promocional provider a provider.

## Classificação de filtros

Cada filtro terá uma classificação futura explícita: `native`, `translated`, `local_postfilter`, `unsupported` ou `unverified`. A versão inicial usa a declaração atual como `native` somente quando o provider a declara; ausência é lacuna, não equivalência.

## Perfis de dados

- `decision`: decisão/acórdão com campos textuais e datas.
- `precedent`: precedente qualificado, tese, questão, status e casos paradigma.
- `curated`: informativo ou seleção oficial, útil para tese e contexto, não automaticamente corpus integral.
- `document`: documento/metadado de apoio, cuja densidade textual precisa ser comprovada.

O perfil deve acompanhar a fonte e, quando necessário, o registro. Não haverá achatamento silencioso de `CanonicalPrecedent` em decisão.

## Política de promoção

Uma lacuna só é encerrada com contrato de rota/payload, fixture pública/replay, parser determinístico, campos canônicos, estados de erro/vazio e teste. Discovery gera hipótese e TODO, não implementação automática.
