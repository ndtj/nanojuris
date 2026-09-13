# Design - TJMG modern API filter contract

The modern endpoint accepts one JSON body containing process identifiers,
document types, judging bodies, magistrates, classes, subjects, comarca names,
publication/judgment date ranges and free text. The adapter already translated
those fields; this change makes the capability ledger reflect that fact.

`types`, `document_type` and `decision_type` are normalized to the source's
document labels and de-duplicated before transport. `courts` maps to
`comarcas`; `legal_area` maps to `assuntos`. Phrase and all-word refinements
share the source free-text channel and are therefore marked `translated`, not
`native`. Any-word and negative-word semantics have no reproduced source
contract and are rejected rather than dropped.

The legacy `www5` form remains a separate access-controlled surface. No
CAPTCHA, token, cookie or OCR path is introduced.
