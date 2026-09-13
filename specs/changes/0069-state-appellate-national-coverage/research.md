# Pesquisa

Fontes locais de verdade:

- `src/nanojuris/brazil.py` - catalogo de autoridades;
- `src/nanojuris/coverage_matrix.py` - superficies e estados;
- `docs/registry/provider-catalog.full.json` - lifecycle/capacidades;
- `docs/coverage/surface-state-registry-20260902.json` - reconciliacao;
- `specs/changes/0029-juscraper-provider-intake/` - snapshot upstream;
- dossies e contratos em `docs/providers/` e `docs/source-contracts/`.

O baseline atual e estrito: cinco bindings CJSG possuem contrato especifico e
evidencia valida. Providers gerais podem ser operacionais sem provar a
collection CJSG; esses casos entram em `contract_hardening`, nao em 27/27.
