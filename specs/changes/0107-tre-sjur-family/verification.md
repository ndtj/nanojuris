# Verification — SDD 0107

## Resultados

- A família está disponível somente com `NanoJurisClient(include_candidate_providers=True)`.
- `authority` ausente ou fora do formato `TRE-XX` é rejeitada.
- O adapter mantém `total_known=false`, `is_complete=false` e rejeita páginas
  remotas não comprovadas.
- A revalidacao bounded de 2026-09-10 para TRE-SP retornou HTTP 200, tres
  registros locais de segundo grau e um PDF oficial de sete paginas com
  extracao completa; isso nao fecha o gate de paginacao nem promove a familia.
- Nenhuma credencial, sessao, token ou bypass foi usado.

## Rastreabilidade

- Implementação: `src/nanojuris/providers/tse_sjur_jurisprudencia.py`.
- Registro: `docs/registry/providers.json`.
- Evidencia anterior: `docs/provider-discovery/tre-sjur-route-inventory-live-20260909.json`.
- Evidencia atual: `docs/provider-discovery/tre-sp-sjur-live-20260910.json`.
- Revalidacao adicional: `docs/provider-discovery/tre-ac-mg-sjur-pagination-live-20260911.json`;
  TRE-AC e TRE-MG tambem repetiram a janela na pagina 2.
- Testes: `tests/test_tre_sjur_jurisprudencia.py`.

## Comandos

```text
python -m pytest -q tests/test_tre_sjur_jurisprudencia.py
python -m ruff check src/nanojuris/providers/tse_sjur_jurisprudencia.py
python -m mypy src/nanojuris/providers/tse_sjur_jurisprudencia.py
```
