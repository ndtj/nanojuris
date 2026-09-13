# Qualidade de providers

Os artefatos desta pasta formam o gate offline de qualidade do NanoJuris.

- provider-quality.json: scorecard determinístico para todas as entradas do
  catálogo, com foco nos 50 providers runtime.
- provider-quality.md: visão humana da mesma matriz.
- ../schemas/provider-quality.schema.json: contrato do scorecard.
- ../../tests/fixtures/provider_quality_scenarios.json: golden set
  sanitizado com sucesso, vazio explícito, parcial, erro, timeout, controle de
  acesso, rate limit e mudança de schema.

Para regenerar e validar localmente:

```text
python tools/build_provider_quality.py --write
python tools/build_provider_quality.py --check
python -m pytest -q tests/test_quality.py tests/test_provider_quality.py
```

O scorecard não faz chamadas de rede. A situação live continua sendo registrada
separadamente no catálogo, com status como valid, blocked_access,
blocked_transport ou source_unavailable. Nenhum desses estados é tratado
como lista vazia.

Um tier gold é apenas um resultado técnico do gate local. Promoção,
licenciamento, termos de uso e publicação continuam exigindo revisão humana.
