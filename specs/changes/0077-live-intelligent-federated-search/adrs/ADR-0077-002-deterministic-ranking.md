# ADR — ranking jurídico determinístico e CPU-only

ID: `ADR-0077-002`
Status: `accepted`
Data: `2026-09-07`

## Contexto

Scores de providers não são comparáveis. O contador lexical atual não entende
frases, campos, filtros ou conceitos e produz falsos positivos.

## Decisão

Usar fórmula versionada baseada em cobertura ponderada, frase, proximidade,
conceitos curados, consistência jurídica, qualidade e RRF fraco da posição
nativa. Não usar LLM, embeddings ou serviço externo.

## Alternativas consideradas

- comparar scores nativos: semanticamente inválido;
- usar somente RRF: preserva ranks, mas não corrige resultado nativo fraco;
- reranker neural/LLM: rejeitado por custo e decisão do produto;
- regras sem benchmark: rejeitadas por risco de ranking enganoso.

## Consequências

### Positivas

- score comum, auditável, barato e reproduzível;
- explicações derivadas dos mesmos sinais;
- rollback por versão.

### Negativas

- léxico exige curadoria;
- semântica fica limitada aos conceitos modelados;
- pesos podem superajustar e precisam de holdout.

## Evidência e revisão

- Só ativar v1 após AC-017–AC-020.
- Toda mudança de peso ou léxico incrementa versão e repete benchmark.
