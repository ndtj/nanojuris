# Verificacao - TJAC Ementario

Estado do lote: `locally_verified_partial` (2026-09-08). O provider foi
implementado, testado e incluido na federacao como fonte parcial. Isso nao
declara que o volume seja acervo integral nem substitui revisao humana de uso.

## Resultados

- Fonte oficial confirmada: pagina institucional e PDF HTTPS do TJAC.
- Provider runtime registrado em `NanoJurisClient`, `config.py` e
  `providers/__init__.py`.
- Parser recompone cabecalho e ementa que aparecem em paginas consecutivas do
  PDF; registra 19 decisoes com texto observavel no volume sem criar indice.
- Filtros locais por termo, frase, numero e exclusao; grau, ramo, instancia,
  autoridade e colecao sao validados antes da chamada.
- Fixture completeness: 65/65 providers runtime completos apos a inclusao das
  fixtures TJAC e do envelope compartilhado.
- Evidencia live: `docs/provider-discovery/tjac-ementario-live-20260908.json`.
  HTTP 200, `application/pdf`, 593570 bytes, hash
  `7d46f40422d10a9bd80e73a51e7fde8ad0b81c312244e1708d915c21c1e1915c`,
  7 registros para `constitucional`, `total_known=false` e
  `pagination_mode=local_pdf_window`.
- Catalogo: 70 fontes, 65 runtime e 49 declaradas na busca unificada. A
  superficie TJAC foi reconciliada como `TJAC/state/second/second/TJAC_EMENTARIO`.
- A federacao tecnica esta habilitada por padrao como fonte parcial; a resposta
  preserva `is_complete=false` e total desconhecido.

## Comandos e resultados

```powershell
$env:PYTHONPATH='src'
python -m pytest -q tests/test_tjac_ementario_jurisprudencia.py  # 5 passed
python -m ruff format src/nanojuris/providers/tjac_ementario_jurisprudencia.py
python -m ruff check src/nanojuris/providers/tjac_ementario_jurisprudencia.py tests/test_tjac_ementario_jurisprudencia.py
python tools/audit_provider_docs.py --write
python tools/audit_provider_discovery_offline.py
python tools/build_provider_coverage.py --write
python tools/build_provider_quality.py --write
python tools/build_provider_capability_ledger.py --write
python tools/build_fixture_completeness.py --write  # 65 complete
python tools/build_degree_coverage.py
python tools/build_surface_state_registry.py
python tools/build_state_appellate_program.py --write
python tools/build_promotion_manifest.py --write
python tools/validate_sdd.py
python -m pytest -q  # 1572 passed, 26 skipped
```

## Rastreabilidade

| Criterio | Evidencia |
|---|---|
| AC-001 | `tests/fixtures/tjac_ementario_success.txt` e parser com registros distintos |
| AC-002 | testes de termo, numero e `without_words` em `tests/test_tjac_ementario_jurisprudencia.py` |
| AC-003 | rejeicao de primeiro grau/colecao, PDF invalido e schema explicito |
| AC-004 | `tjac-ementario-live-20260908.json`, HTTP 200 e 7 resultados observados |
| AC-005 | catalogo gerado, registro runtime e superficie `second/second` |
| AC-006 | testes focados, validacao SDD, fixture completeness e gates locais |

## Limites e decisao

O ementario publica ementas, nao voto integral. O volume corrente nao fornece
total autoritativo entre edicoes; portanto a fonte e parcial e nao deve ser
usada para afirmar ausencia nacional. PDF vazio/invalido, bloqueio, timeout,
429, WAF, CAPTCHA, TLS ou schema inesperado continuam estados de erro explicitos.
Nenhum bypass, proxy rotation, stealth ou autenticacao foi usado. Nao houve
commit, push, tag, release, deploy, `terraform apply` ou alteracao de producao.
