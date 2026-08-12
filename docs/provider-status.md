# Status das fontes

O NanoJuris distingue três perguntas que costumam ser confundidas:

| Estado | Significado |
| --- | --- |
| **Implementado** | Existe um adapter registrado no pacote e exposto pelas interfaces suportadas. |
| **Validado** | O parser, o contrato e os cenários offline possuem testes e fixtures. |
| **Live** | Uma chamada pública respondeu em uma verificação identificada por data, rede e consulta. |

Uma fonte pode ser implementada e validada sem estar disponível live no momento
da consulta. Tribunais podem alterar rotas, aplicar limites, exigir captcha ou
responder de forma diferente conforme a rede. Por isso, o NanoJuris preserva a
limitação observada em vez de convertê-la em falso sucesso.

## Catálogo operacional

O [registry](registry/providers.json) é a fonte machine-readable de providers
implementados, candidatos e famílias. Para consultar o contrato runtime:

```bash
nanojuris fontes
nanojuris diagnostico --fonte tjdf_juris
nanojuris contratos --resumo
nanojuris contratos --fonte tjdf_juris
```

Para uma visão humana da cobertura, consulte o [mapa de cobertura](provider-coverage-map.md)
e o [auditório documental](provider-documentation-audit.md). Os relatórios de
validação registram a evidência live sem prometer disponibilidade permanente.

## Estados de acesso

Quando uma consulta é executada, os estados relevantes podem incluir:

| Estado | Interpretação operacional |
| --- | --- |
| `public` | A resposta foi obtida sem controle de acesso observado. |
| `partial` | A fonte respondeu, mas não comprovou todos os campos ou a completude. |
| `access_control_required` | A fonte apresentou captcha, WAF ou outra barreira. |
| `login_required` | A rota exigiu autenticação. |
| `rate_limited` | A fonte limitou a frequência ou o volume. |
| `source_unavailable` | A rota não respondeu ou apresentou erro transitório. |

Esses estados descrevem a aquisição, não a validade jurídica do conteúdo.

## Exemplos de leitura

```text
tjdf_juris
  implementação: registrada
  validação: fixture + contrato
  live: evidência datada; consultar diagnóstico antes de lote

stf_juris
  implementação: registrada
  validação: fixture + contrato observado
  live: condicionado à resposta da fonte e a controles externos

stj_scon
  implementação: registrada
  validação: parser offline
  live: experimental; conferir o dossiê antes de depender da fonte
```

Os exemplos acima são categorias de maturidade, não um monitoramento em tempo
real. A execução atual deve ser verificada no ambiente do usuário.

## Critério para produção

Antes de incorporar uma fonte em uma coleta importante:

1. confira o `source_id` e o dossiê específico;
2. rode `nanojuris diagnostico --fonte <source_id>`;
3. confirme busca, paginação, documentos e limites;
4. preserve `SourceTrace`, erros parciais e `run_id`;
5. registre a data da verificação no relatório do seu próprio dataset.

Para novos providers, o contrato completo está em
[provider-dossier-template.md](provider-dossier-template.md) e o processo de
descoberta está no [route-mapping-playbook.md](route-mapping-playbook.md).
