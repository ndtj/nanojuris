# Verificacao

Status tecnico: `technical_gates_passed`; a revisao humana de retencao segue
pendente.

## Evidencia live

Busca publica bounded em 2026-09-08: HTTP 200, JSON DSpace, dois itens
reportados e dois retornados na janela de tamanho 2. O item
`tjmg/8566` teve PDF oficial HTTP 200, `application/pdf`, 405979 bytes e hash
SHA-256 registrado no artefato live.

## Gates

- [x] fonte oficial e contrato de colecao;
- [x] adapter e runtime;
- [x] fixtures sanitizadas;
- [x] testes focados;
- [x] smoke federado bounded de fonte unica;
- [ ] decisao humana de retencao e atualizacao.

O smoke federado foi executado com uma janela de uma pagina e dois candidatos:
`docs/provider-discovery/tjmg-ejef-boletim-federated-live-20260908.json`.
Retornou `source_access_status=public`, total conhecido 2, dois registros
validos e nenhum erro. Nenhum corpo foi persistido.

## Resultados

- Adapter, contrato de grau, fixtures, smoke live e smoke federado bounded:
  aprovados.
- Erros de acesso, transporte, schema e bitstream ausente permanecem estados
  distintos de vazio autoritativo.
- A colecao e curada e nao representa o acervo integral do TJMG; isso fica
  registrado no contrato e impede uma alegacao de cobertura total.

## Rastreabilidade

| Aceitacao | Evidencia |
|---|---|
| AC-001 | `tests/test_tjmg_ejef_boletim_jurisprudencia.py` e fixture de sucesso |
| AC-002 | fixture `tjmg_ejef_boletim_empty.json` |
| AC-003 | fixture `tjmg_ejef_boletim_invalid.json` |
| AC-004 | `docs/provider-discovery/tjmg-ejef-boletim-live-20260908.json` |
| AC-005 | suite focada e gates locais registrados no handoff |

Nenhum commit, push, deploy ou alteracao de producao foi realizado.
