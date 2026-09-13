# Contratos públicos live — 2026-09-02 (ciclo 21)

Rodada bounded sem credenciais, sem persistência de corpos e sem contornar
CAPTCHA, WAF ou controles de acesso. O JSON correspondente contém apenas
metadados e asserções sanitizadas.

## Resultado

Foram executados **11 cenários**: **9 válidos** com resposta pública real e
**2 bloqueados por controle de acesso**. Os dois bloqueios não foram tratados
como lista vazia:

| Provider | Status | Evidência |
|---|---|---|
| `bnp_pangea` | `valid` (3 cenários) | catálogo e buscas com trace |
| `tjes_cjpg` | `valid` | JSON público, `pje1g`, texto integral |
| `tjes_jurisprudencia` | `valid` | JSON público, `pje2g`, ementa |
| `tjba_graphql` | `valid` | busca e inteiro teor público extraído |
| `stj_informativo` | `valid` | parser HTML e URL documental |
| `stj_dados_abertos_jurisprudencia` | `valid` | catálogo CKAN e plano de sincronização dry-run |
| `tjsp_cjpg` | `valid` | busca pública numerada com texto integral |
| `stj_scon` | `blocked_access` | `AccessControlRequiredError` explícito |
| `tjsp_cjsg` | `blocked_access` | CAPTCHA/controle de acesso explícito |

## Reprodutibilidade

```powershell
$env:NANOJURIS_RUN_LIVE = "1"
python -m pytest -q tests/test_bnp_pangea_live.py tests/test_tjes_cjpg_live.py `
  tests/test_tjes_jurisprudencia_live.py tests/test_tjba_graphql_live.py `
  tests/test_stj_html_parsers_live.py tests/test_stj_dados_abertos_live.py

$env:NANOJURIS_RUN_TJSP_CJPG_LIVE = "1"
$env:NANOJURIS_RUN_TJSP_LIVE = "1"
python -m pytest -q tests/test_tjsp_cjpg_live.py tests/test_tjsp_cjsg_live.py
```

Resultado observado: `9 passed` e `2 passed`.

## Limites

Esses testes comprovam o contrato público no instante da execução; não
promovem providers nem substituem validação legal, fixtures versionadas ou
monitoramento periódico. O sweep nacional separado está em
[`all-provider-sweep-20260902-cycle24.json`](all-provider-sweep-20260902-cycle24.json)
e observou rotas, não dados de pesquisa.
