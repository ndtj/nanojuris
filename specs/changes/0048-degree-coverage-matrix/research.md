# Pesquisa

## Fontes internas

- `src/nanojuris/brazil.py`: registro institucional local com 94 autoridades,
  incluindo 27 TJs, TSE/TREs, STM/TJMs e TST/TRTs.
- `src/nanojuris/topology.py`: topologia atual ainda usa `degree="unknown"`
  para as coleções derivadas do catálogo.
- `docs/registry/providers.json` e
  `docs/registry/provider-catalog.full.json`: registro runtime/candidatos e
  contratos gerados.
- Dossiês individuais em `docs/providers/`: fonte para distinguir decisão,
  precedente, informativo e catálogo.

## Decisões derivadas

1. A matriz não pode usar somente `provider_status` de `CourtInfo`, pois o
   catálogo de authorities e o registro runtime podem estar em épocas de
   sincronização diferentes.
2. A presença de sentença ou decisão em uma resposta mista não prova que a
   fonte tenha contrato CJPG; por isso a linha é `pending_contract`.
3. `SJUR` eleitoral, `EPROC` e `PJE` devem manter suas identidades próprias.
4. A existência de um método upstream ou endpoint no JavaScript não é evidência
   de resposta pública reproduzível.
