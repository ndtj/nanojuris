# Scorecard de qualidade premium

O scorecard mede qualidade por provider e por release. Nenhum indicador isolado
declara maturidade.

| Dimensão | Indicador | Evidência | Meta inicial |
| --- | --- | --- | --- |
| autoridade | fonte oficial confirmada | dossier/source contract | 100% |
| contrato | rotas, filtros e falhas documentados | `spec.md`/contract | 100% dos providers ativos |
| identidade | registros estáveis e deduplicáveis | fixtures/testes | sem regressão conhecida |
| conteúdo | texto e campos essenciais presentes | golden fixtures | conforme contrato |
| temporalidade | datas normalizadas ou preservadas brutas | extraction trace | 100% quando disponíveis |
| provenance | source/extraction trace completo | testes de contrato | 100% |
| parser | regressão coberta por fixtures | pytest | 100% de cenários críticos |
| completude | cobertura declarada e observada | validação bounded | explícita |
| operação | latência, erro, disponibilidade e recuperação | SLO/runbook | definido por tier |
| documentação | catálogo, dossier e contract sincronizados | auditoria de docs | 0 pendências críticas |
| manutenção | risco e custo de mudança | review checklist | aceito pelo owner |

## Tiers de maturidade

- `bronze`: fonte identificada e evidência inicial;
- `silver`: contrato, parser, fixtures, traces e estados operacionais;
- `gold`: identidade estável, texto, datas, cobertura validada, regressão e
  operação documentada;
- `premium`: gold com revisão independente, scorecard acompanhado, runbook,
  recuperação testada e baixo risco residual.

## Regra de promoção

Promoção de tier exige evidência preenchida e aprovação do Domain Owner, Data
Quality e QA. Em tiers gold/premium, Architecture, Security e SRE participam
conforme o nível de revisão.
