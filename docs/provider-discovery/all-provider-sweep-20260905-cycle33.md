# Provider sweep live bounded — ciclo 33 (2026-09-05)

Execução: `discover_all_providers.py --live --include-catalog-candidates
--max-pages 1 --max-depth 0 --timeout 6 --delay 0.25`.

## Resultado

- 50/50 providers runtime observados.
- 8/8 candidates do catálogo observados.
- 1.912 rotas observadas e 269 filtros declarados.
- 10 observações com controle de acesso.
- Nenhum POST foi inferido ou submetido; nenhum CAPTCHA, WAF ou login foi
  contornado; corpos de resposta não foram promovidos a fixtures.

## Candidatos relevantes

| Fonte | Observação | Decisão |
|---|---|---|
| `tjap_tucujuris` | HTTP 200, shell HTML sem sinais jurídicos | permanece candidate; contrato de busca pendente |
| `tjmg_jurisprudencia` | HTTP 200, formulário com controle de acesso | permanece blocked/inconclusive |
| `tjrn_jurisprudencia` | HTTP 200, portal público; adapter opt-in existente | não promover padrão sem revisão de reuso |
| `trf3_jurisprudencia` | HTTP 200, interface e filtros; sem resposta decisória | permanece candidate; fixture e replay pendentes |
| `falcao_jt` | robots disallowed | não inferir disponibilidade |
| `tjrj_ejuris` | robots disallowed | não inferir disponibilidade |
| `tjse_jurisprudencia` | robots disallowed | não inferir disponibilidade |
| `trt2_pje_jurisprudencia` | robots disallowed | não inferir disponibilidade |

O JSON completo, com hashes, traces e classificações por rota, está em
[`all-provider-sweep-20260905-cycle33.json`](./all-provider-sweep-20260905-cycle33.json).

Esta evidência atualiza o diagnóstico live, mas não substitui contrato,
fixture sanitizada, qualidade, autorização de reuso ou promoção legal.
