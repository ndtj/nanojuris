# Verification — SDD 0108

## Resultados

- O dispatcher exige `authority` e aceita TNU, TRF2/TRF02, TRF4/TRF04 e
  TRF6/TRF06.
- A delegação usa os adapters existentes; não há fan-out nem total agregado.
- A família aparece no cliente normal como binding runtime explícito; sua
  capability permanece opt-in (`supports_unified_search=False`).
- `NanoJurisClient()` registra 77 providers, incluindo o dispatcher; a
  federação continua restrita às capabilities `supports_unified_search=True`.
- Nenhum acesso autenticado, token, CAPTCHA ou bypass foi usado.
- Smoke live bounded em 2026-09-10: TNU, TRF2 e TRF6 retornaram HTTP 200,
  um resultado de segundo grau e inteiro teor HTML válido por autoridade.
  A evidência redigida está em
  `docs/provider-discovery/federal-eproc-detail-live-20260910.json`; corpos
  não foram persistidos. O dispatcher continua opt-in e cada autoridade
  mantém gates próprios.

## Rastreabilidade

## Evidência

- Implementação: `src/nanojuris/providers/eproc_jurisprudencia_federal.py`.
- Cliente: `src/nanojuris/client.py`.
- Testes: `tests/test_eproc_jurisprudencia_federal.py`.
- Contratos: `docs/providers/eproc_jurisprudencia_federal/README.md` e
  `docs/source-contracts/eproc_jurisprudencia_federal.md`.

## Comandos executados

```text
python -m pytest -q tests/test_eproc_jurisprudencia_federal.py
python -m pytest -q
python tools/validate_sdd.py
python tools/validate_executor_packet.py
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
git diff --check
```

Resultado: suíte completa verde; gates estáticos verdes. Os gates live e de
promoção permanecem abertos por autoridade e não são mascarados pela família.
