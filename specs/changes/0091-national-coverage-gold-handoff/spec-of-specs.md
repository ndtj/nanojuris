# 0091 — handoff de cobertura nacional ouro

Status: `proposed`  
Owner: Provider Engineering, Data Quality, Search, Security and Release  
Data: `2026-09-08`

## Propósito

Este pacote é o ponto de entrada para um novo modelo concluir a cobertura
nacional de jurisprudência sem depender do histórico da conversa. Ele não
substitui os contratos 0070 (capacidades ouro), 0077 (busca live inteligente),
0078 (acesso público legítimo) ou 0089 (execução nacional); ele os compõe,
define a ordem de execução e fornece artefatos operacionais que faltavam.

## Pacotes normativos relacionados

| Pacote | Responsabilidade | Relação |
| --- | --- | --- |
| 0070 | filtros, campos, documentos e certificação ouro | fonte de critérios de capacidade |
| 0077 | intenção, planejamento, ranking e UX da busca web | consumidor dos contratos federados |
| 0078 | acesso público, desafios e limites | autoridade para qualquer chamada live |
| 0081 | primeiro grau estadual | workpacks CJPG |
| 0082 | trabalho e eleitoral | famílias fora dos TJs estaduais |
| 0083 | federal, superior e militar | famílias institucionais |
| 0084 | inteiro teor e completude | pipeline de documentos |
| 0089 | execução, fixtures e promoção | runbook base |
| 0090 | TJ/RJ Banco de Sentenças | exemplo de provider link-only |

## Decomposição das ondas

1. **G0 — baseline:** regenerar todos os inventários e congelar contagens.
2. **G1 — registro:** reconciliar cada `authority + degree + collection`.
3. **G2 — contrato:** fechar filtros, campos, paginação, datas e documentos.
4. **G3 — fontes:** executar descoberta pública bounded e equivalência técnica
   com Juscraper, sem copiar código.
5. **G4 — adapters:** implementar somente fontes com contrato reproduzível.
6. **G5 — qualidade:** fixtures, parser, identidade, documentos e semântica de
   vazio/erro.
7. **G6 — federação:** smoke opt-in, ranking e promoção automática técnica.
8. **G7 — operação:** TTL, drift, métricas, shadow mode e rollback.
9. **G8 — revisão:** decisões humanas de legalidade, retenção, relevância e
   release; nenhum agente pode simulá-las.

Cada onda possui gate próprio. A existência de um adapter ou resposta HTTP 200
não fecha nenhum gate posterior.
