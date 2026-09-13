# Design — observabilidade live

## Arquitetura

    scheduler autorizado
      -> probe policy
      -> provider canary
      -> redacted observation
      -> SLI store/report
      -> alert and runbook

## SLIs

- access_success_ratio;
- valid_contract_ratio;
- parser_change_ratio;
- latency percentiles;
- rate_limit events;
- last_confirmed_valid_at;
- completeness drift;
- field presence drift.

SLOs serão definidos por tier e frequência permitida pela fonte. Gold não
significa disponibilidade contínua do tribunal.
