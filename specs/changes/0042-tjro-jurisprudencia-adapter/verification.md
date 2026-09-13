# Verificação — TJRO jurisprudência textual

Status: verified

## Resultado da implementação

T00–T04 foram concluídas com rechecagem pública bounded, contrato HTTP,
fixtures sanitizadas, parser canônico, identidade, paginação e estados de erro
explícitos. O provider preserva `raw`, `SourceTrace`, bytes e hashes.

T05 está concluída: `NanoJurisClient()` registra `tjro_jurisprudencia` na lista
padrão e `supports_unified_search=True` o inclui na busca federada. O source ID
permanece independente de `tjro_liame`, que continua sendo precedente
qualificado. O parâmetro legado `include_candidate_providers` continua aceito,
mas não é necessário para o TJRO.

T06 está concluída para as superfícies com contrato: a busca, o download PDF ou
DOCX e a rota relacionada foram testados com chamadas live bounded. Facetas
(`POST /search/agregacoes`) seguem fora do runtime por falta de modelo canônico
e política de retenção.

T07 está concluída para o binding CJPG. A chamada live de 06/09/2026 enviou
`fields.grau_jurisdicao=[1]`, retornou exclusivamente `PJEPG`/`sentenca` com
resumo, identificador, processo e data em duas páginas sem sobreposição; uma
chamada de detalhe devolveu PDF público (36.312 bytes) com extração textual
completa. O parser preserva o `_id` da busca e usa o
`id_processo_documento` explícito para não duplicar o sufixo `PJEPG` na rota de
documento.

## Resultados

Os testes offline e a chamada federada bounded confirmam que o provider retorna
registros canônicos e permanece separado de LIAME. A matriz de cobertura e o
catálogo foram regenerados após a promoção.

## Rastreabilidade

| Requisito | Evidência | Estado |
| --- | --- | --- |
| REQ-001 | inventário oficial, rechecagens live e inventário de rotas | completo para busca/documento; limite remoto máximo pendente |
| REQ-002 | source IDs e escopos independentes; registro padrão | completo |
| REQ-003 | parser, `raw`, `CanonicalDocument` e `SourceTrace` | completo para busca e download público |
| REQ-004 | fixtures de vazio, erro, acesso, rate limit, timeout e schema drift | completo |
| REQ-005 | política de segurança e uso responsável | parcial; revisão global pendente |

| REQ-006 | binding CJPG, paginação e inteiro teor PJEPG | completo; evidência em `docs/provider-discovery/tjro-cjpg-live-20260906.json` |

## Gates externos

O escopo desta rodada autoriza a operação técnica local/federada do provider;
não há deploy, push ou alteração em produção neste ciclo. Limitações de
facetas e limites remotos continuam registradas acima.

## Evidência live

- `docs/provider-discovery/tjro-jurisprudencia-live-recheck-20260902-cycle13.json`;
- `docs/provider-discovery/tjro-jurisprudencia-live-validation-20260902-cycle13.json`;
- `docs/provider-discovery/tjro-jurisprudencia-route-inventory-20260902-cycle14.json`;
- `docs/provider-discovery/tjro-jurisprudencia-live-20260902-cycle14.json`;
- `docs/provider-discovery/tjro-jurisprudencia-live-20260902-cycle15.json`;
- `docs/provider-discovery/tjro-jurisprudencia-federated-live-20260902-cycle16.json`.
- `docs/provider-discovery/tjro-cjpg-live-20260906.json`.
