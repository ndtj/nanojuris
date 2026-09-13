# 0076 - TJPR native refinement filters

Status: verified

## Intent

Close the gap between the public TJPR jurisprudence form and the NanoJuris
adapter. The form exposes native identifiers for comarca, relator, judging
body, procedural class and decision type, but the adapter previously dropped
the canonical refinements or treated judgment dates as source-update dates.

## Scope

- Translate numeric source identifiers supplied through the canonical query.
- Map `judgment_date_from/to` to TJPR's judgment date fields.
- Preserve explicit rejection when a source identifier is required but a label
  is supplied; never silently broaden a query.
- Keep first/second-degree scope validation and all existing document behavior.

## Acceptance criteria

- `case_class`, `judging_body`, `rapporteur` and numeric `courts` are sent to
  the corresponding TJPR hidden fields.
- Numeric `types` are sent to `idsTipoDecisaoSelecionadosString`.
- Non-numeric values for those ID-backed filters raise `QueryRejectedError`.
- `judgment_date_from/to` are sent as `dataJulgamentoInicio/Fim`.
- Existing published-date, text, number, pagination and detail behavior stays
  unchanged and is covered by tests.

## AC-001 — filtros nativos preservam semântica

Para valores numéricos válidos, o adapter envia os identificadores aos campos
oficiais correspondentes; para valores textuais não resolvidos, rejeita a
consulta explicitamente. Datas de julgamento são separadas das datas de
publicação e nenhum filtro é ampliado silenciosamente.
