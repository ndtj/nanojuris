# Design — runtime compartilhado

## Fluxo

    ProviderPolicy -> SafeHttpClient -> SourceResponse -> parser específico
          |                |
          |                +-> telemetry segura
          +-> budget, host, timeout, retry e cache

## Módulos propostos

- transport/policy.py
- transport/http.py
- transport/retry.py
- transport/cache.py
- transport/circuit.py
- transport/redaction.py

Browser headed permanece ferramenta de discovery e teste humano autorizado,
não implementação padrão de provider.

## Defaults

Defaults devem ser conservadores e sobrescrevíveis por declaração. Retry não
ocorre para parser_changed, invalid_query, 401/403 de controle ou CAPTCHA.
