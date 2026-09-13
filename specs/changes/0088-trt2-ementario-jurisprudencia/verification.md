# Verificação

## Resultados

Implementação local concluída com parser, fixtures e contrato de segundo grau.
Após a rechecagem bounded de 2026-09-08, o provider foi habilitado tecnicamente
na federação padrão como fonte parcial. A resposta preserva
`total_known=false`/`is_complete=false`; isso não representa exaustividade do
ementário nem substitui o PJe protegido.

## Evidência live

- Índice oficial: HTTP 200 e HTML com tópicos observados em 2026-09-07.
- Tópico oficial `ACAO_Conexao.html`: HTTP 200, ementa textual e link PDF.
- Tentativas posteriores: HTTP 403 CloudFront intermitente; classificadas como
  `access_controlled/source_unavailable`, nunca como vazio.
- Evidência redigida: `docs/provider-discovery/trt2-ementario-live-20260907.json`.
- Rechecagem 2026-09-08: as raízes `Tribunal_Pleno.html` e `Corregedoria.html`
  retornaram ementas de segundo grau; um PDF oficial respondeu
  `application/pdf` com 489.171 bytes (hash registrado sem corpo bruto).
- Evidência redigida: `docs/provider-discovery/trt2-ementario-live-20260908.json`.

## Testes

```text
python -m pytest -q tests/test_trt2_ementario_jurisprudencia.py
python -m ruff check src/nanojuris/providers/trt2_ementario_jurisprudencia.py tests/test_trt2_ementario_jurisprudencia.py
python -m mypy src/nanojuris/providers/trt2_ementario_jurisprudencia.py
```

## Decisão

Adapter implementado em runtime e habilitado na federação como fonte parcial.
O rollout não afirma cobertura completa; bloqueios CloudFront, vazio
autoritativo e total desconhecido continuam estados distintos.

## Rastreabilidade

| Critério | Evidência |
| --- | --- |
| AC-001/AC-003 | adapter e testes de identidade, janela e total desconhecido |
| AC-004 | `get_document`, allowlist, pipeline compartilhado e fixture PDF |
| AC-005/AC-006 | capabilities, exceções de acesso e testes de filtros |
| AC-007 | `supports_unified_search=true`, `opt_in_unified_search=false`, `total_known=false` |
| AC-008 | política de acesso e evidência redigida |
