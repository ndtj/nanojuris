# Programa SDD — excelência nacional de providers de jurisprudência

ID: 0026-jurisprudence-provider-excellence
Status: proposed
Owner: NanoJuris engineering
Data: 2026-09-01

## Intenção

Coordenar a evolução da NanoJuris para uma biblioteca de referência na coleta,
normalização e rastreabilidade de jurisprudência brasileira pública. Este
programa não implementa providers diretamente: ele define a arquitetura, os
pacotes filhos, os gates e a ordem de promoção.

## Limite do programa

O programa cobre jurisprudência textual, precedentes, decisões, informativos e
inteiro teor público quando disponível. Consulta processual, partes,
movimentações, comunicações, DJEN e DataJud pertencem à NanoJud.

## Pacotes filhos

| Ordem | Pacote | Resultado independente | Gate de saída |
| --- | --- | --- | --- |
| 1 | 0027-provider-contract-v2 | contrato comum de capacidade, erro, paginação, provenance e compatibilidade | contrato e testes normativos aceitos |
| 2 | 0028-shared-provider-runtime | transporte, políticas de rede, retry, limites, cache e circuit breaker reutilizáveis | testes determinísticos de falha e política |
| 3 | 0029-juscraper-provider-intake | processo seguro de adoção de rotas, parsers e fixtures do Juscraper | licença, equivalência e atribuição comprovadas |
| 4 | 0030-state-jurisprudence-coverage | cobertura estadual priorizada por ondas e semântica de fonte | adapters promovidos individualmente |
| 5 | 0031-provider-quality-evaluation | scorecard, golden set, invariantes e gate gold/premium | avaliação reproduzível e sem falso positivo |
| 6 | 0032-fulltext-document-pipeline | descoberta, download, hash, parsing e vínculo de inteiro teor | cadeia documental auditável |
| 7 | 0033-live-contract-observability | canários bounded, freshness, schema drift, SLI e diagnóstico | monitoramento seguro e acionável |
| 8 | 0034-provider-release-governance | compatibilidade, documentação, depreciação, rollout e rollback | release candidate revisado e autorizado |
| 9 | 0035-provider-completion-autopilot | fila retomável, work packs e checkpoints de todas as fontes | todas as fontes em estado terminal comprovado |
| 10 | 0036-national-jurisprudence-topology | denominador nacional por ramo, instituição, coleção e período | mapa nacional versionado e sem dupla contagem |
| 11 | 0037-canonical-legal-identity | identidade, taxonomia, versionamento e deduplicação jurídica | invariantes de identidade e corpus de colisão aceitos |
| 12 | 0038-federated-search-semantics | equivalência de query, filtros, ranking, paginação global e explicabilidade | busca federada honesta e determinística |
| 13 | 0039-juscraper-adapter-waves | adaptação por ondas das superfícies úteis do Juscraper | cada superfície adotada, endurecida, bloqueada ou rejeitada com evidência |
| 14 | 0040-reproducible-collection-freshness | coleta resumível, manifests, checkpoints, versões e freshness | pesquisa reproduzível sem prometer espelho nacional integral |

## Dependências

    0036 -> 0037 -> 0027 -> 0028
      |       |       |       |
      |       +------>0031<---+
      |               |
      +----->0038<-----+
      |
      +----->0029 -> 0039 -> 0030
                    |       |
                    +->0032-+
                         |
                         +->0040 -> 0033 -> 0034

    0027..0040 -> 0035 coordena, invalida evidência obsoleta e acompanha a execução

0036 define o denominador antes de qualquer claim nacional. 0037 e 0027 fecham
identidade e contrato; 0028 e 0031 formam a fundação operacional e de qualidade.
0029 nunca promove código automaticamente. 0039 prepara adaptações do Juscraper
e 0030 promove providers em lotes pequenos. 0032 e 0040 tratam documentos e
coleta reprodutível. 0033 observa contratos; 0034 encerra a cadeia de release.

## Regra de decomposição

Cada provider promovido por 0030 deve possuir uma mudança SDD L2 ou L3 própria,
mesmo quando reutiliza uma família de parser. Uma onda pode coordenar vários
providers, mas não pode esconder falha ou bloqueio por fonte.

## Gates do programa

1. Topologia: universo nacional versionado por instituição e coleção; o
   catálogo atual é baseline, não denominador definitivo.
2. Catálogo: 100% das fontes conhecidas classificadas e sincronizadas, sem
   teste que impeça crescimento legítimo.
3. Contrato: 100% dos providers ativos com capacidades e estados de erro
   explícitos.
4. Evidência: nenhum provider promovido sem fixture, parser, teste canônico e
   dossiê.
5. Dados: identidade, versão, provenance, completude e motivo de ausência
   preservados.
6. Federação: query, filtros, ranking e paginação declaram equivalência e
   limitações por fonte.
7. Operação: chamadas live apenas opt-in, bounded e de baixa frequência.
8. Segurança: nenhum bypass de CAPTCHA, WAF, login ou rate limit; OCR nunca
   resolve desafio de acesso.
9. Compatibilidade: API, CLI, MCP, Studio, exports e store avaliados.
10. Release: publicação e produção dependem de autorização humana explícita.

## Critério de encerramento

O programa só pode ser aceito quando todos os pacotes filhos estiverem
verified ou accepted, as lacunas restantes estiverem classificadas e o
relatório final não afirmar cobertura que não tenha evidência reproduzível.
