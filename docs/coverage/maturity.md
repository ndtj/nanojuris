# Maturity

Gerado por `python tools/build_provider_coverage.py --write`. Nao edite manualmente os dados tabulares.

## Taxonomia

| Nivel | Uso recomendado | Criterio operacional |
| --- | --- | --- |
| `gold` | referencia para Studio, MCP, demos e jurimetria inicial | contrato forte, baixo/medio risco, busca unificada e documentacao sem pendencia critica |
| `silver` | uso produtivo com cautela | contrato bom, mas ainda com lacunas de live, inteiro teor, filtros ou docs |
| `bronze` | pesquisa tecnica e amadurecimento | provider existe, mas ainda precisa de fixtures, erros ou contrato mais profundo |
| `context` | fonte complementar | precedentes, informativos, catalogos ou datasets que ajudam a pesquisa, mas nao sao busca textual ampla |
| `mapped` | backlog de desenvolvimento | fonte documentada sem provider runtime |
| `blocked` | nao rotear automaticamente | WAF, captcha, login, timeout recorrente ou contrato instavel |
| `family` | especificacao reutilizavel | familia tecnica compartilhada, nao fonte executavel isolada |

## Contagem Atual

| Nivel | Quantidade |
| --- | ---: |
| `bronze` | 21 |
| `context` | 6 |
| `family` | 1 |
| `gold` | 1 |
| `mapped` | 16 |
| `silver` | 9 |

## Principio De Qualidade

Uma fonte so deve virar referencia para jurimetria quando a biblioteca consegue
distinguir resultado vazio, falha de rede, controle de acesso, mudanca de
contrato, coleta parcial e resposta completa.
