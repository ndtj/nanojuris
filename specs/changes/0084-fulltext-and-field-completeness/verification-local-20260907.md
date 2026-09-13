# Local verification - capability and document inventory

- `python tools/build_document_capability_inventory.py --write` passed.
- `python tools/build_provider_capability_ledger.py --write` passed.
- Current capability inventory: 64 providers, 58 runtime, 48 runtime entries
  declaring full text, and 60 declared document routes.
- The ledger contains canonical-field classification, raw preservation,
  filter terminal states, document capability, and evidence references for all
  64 catalog providers.
- `tests/test_document_capability_inventory.py`,
  `tests/test_provider_capability_ledger.py`, `tests/test_documents.py`, and
  `tests/test_qa_jurisprudence_documents.py` pass.

Differential filter proof and live document QA remain open; declarations are not
treated as proof of availability.
