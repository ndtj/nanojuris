# Maturity

Gerado por `python tools/build_provider_coverage.py --write`. Nao edite manualmente os dados tabulares.

## Taxonomia

| Nivel | Uso recomendado | Criterio operacional |
| --- | --- | --- |
| `gold` | referencia para Studio, MCP, demos e jurimetria inicial | contrato forte, baixo/medio risco, busca unificada, offline completo e documentacao estrutural completa |
| `silver` | uso produtivo com cautela | contrato nivel 4+, busca unificada e evidencia offline; lacunas avancadas permanecem visiveis |
| `bronze` | pesquisa tecnica e amadurecimento | provider existe, mas ainda precisa de fixtures, erros ou contrato mais profundo |
| `context` | fonte complementar | precedentes, informativos, catalogos ou datasets que ajudam a pesquisa, mas nao sao busca textual ampla |
| `mapped` | backlog de desenvolvimento | fonte documentada sem provider runtime |
| `blocked` | nao rotear automaticamente | WAF, captcha, login, timeout recorrente ou contrato instavel |
| `family` | especificacao reutilizavel | familia tecnica compartilhada, nao fonte executavel isolada |

## Contagem Atual

| Nivel | Quantidade |
| --- | ---: |
| `blocked` | 3 |
| `bronze` | 1 |
| `context` | 9 |
| `family` | 1 |
| `gold` | 15 |
| `mapped` | 9 |
| `silver` | 17 |

## Como Ler O Gate Prata

Itens de checklist ainda abertos aparecem no dossie e no score, mas nao bloqueiam automaticamente a camada `silver` quando nao representam uma omissao estrutural. Isso separa backlog de aprofundamento da ausencia de contrato minimo.
Risco operacional alto, WAF, TLS, CAPTCHA, timeout e mudanca de contrato nunca viram resultado vazio e podem manter a fonte em `blocked`.

## Principio De Qualidade

Uma fonte so deve virar referencia para jurimetria quando a biblioteca consegue
distinguir resultado vazio, falha de rede, controle de acesso, mudanca de
contrato, coleta parcial e resposta completa.
