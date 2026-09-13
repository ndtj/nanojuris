# Matriz de compatibilidade v1/v2

| Superficie v1 | Superficie v2 | Compatibilidade | Politica |
| --- | --- | --- | --- |
| `supported_filters` | `filter_semantics[name] = native` | aditiva | lista legada permanece |
| `unsupported_filters` | `filter_semantics[name] = unsupported` | aditiva | ausencia continua `unverified` |
| `SearchPage.results` | `ProviderOutcome.returned` | derivada | registros nao sao copiados |
| `SearchPage.total` | `ProviderOutcome.reported_total` | derivada | total desconhecido permanece nulo |
| `SearchPage.is_complete` | `ProviderOutcome.complete` e `partial` | derivada | falso nunca vira vazio |
| excecao do provider | `ProviderOutcome.status` | adapter opt-in | classe original vira `error_type` |
| `SourceTrace` | `ProviderOutcome.trace` | preservada | credenciais sao redigidas |

Os campos v2 sao opcionais nos modelos de pagina e nao mudam a assinatura dos
providers. A tabela descreve o contrato de transicao, nao uma declaracao de
que todos os providers ja o implementam.
