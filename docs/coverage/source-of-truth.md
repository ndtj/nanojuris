# Fontes De Verdade

Esta pagina define qual artefato deve ser consultado para cada pergunta do
NanoJuris. Ela evita que humanos e agentes confundam inventario documental,
capacidade de runtime, evidencia live e cobertura operacional.

## Hierarquia

```text
providers.json
  inventario de ciclo de vida e escopo documental
        |
        +--> ProviderCapabilities / source contracts
        |      contrato declarado pelo runtime e dossie tecnico
        |
        +--> provider-catalog.full.json
               catalogo operacional gerado para Studio, MCP e IA
                         |
                         +--> coverage/*.md
                         +--> interfaces de produto
```

## Artefato Certo Para Cada Pergunta

| Pergunta | Fonte de verdade | Observacao |
| --- | --- | --- |
| A fonte existe no projeto? | `docs/registry/providers.json` | Separa `implemented`, `candidate` e `family`. |
| O provider esta registrado no runtime? | `NanoJurisClient().list_sources()` | Nao confundir dossie com implementacao. |
| Quais capacidades o runtime declara? | `ProviderCapabilities` e `source_contracts` | Inclui busca, documentos, interfaces e limites declarados. |
| Qual e o estado operacional consolidado? | `docs/registry/provider-catalog.full.json` | Arquivo gerado; nao editar manualmente. |
| O que foi observado em uma chamada real? | `docs/validation/runs/*.json` | Evidencia datada, nao garantia permanente. |
| Quais estados offline sao cobertos? | `tests/fixtures/provider_contracts.json` | Manifesto de sucesso, vazio e indisponibilidade por provider. |
| Como interpretar a fonte? | `docs/providers/<source_id>/README.md` | Dossie canonico para humanos. |
| Qual caminho legado ainda funciona? | `docs/source-contracts/<source_id>.md` | Copia de compatibilidade durante a migracao. |
| Qual e a matriz nacional resumida? | `docs/coverage/*.md` | Views geradas do catalogo operacional. |

## Escopos Nao Equivalentes

O catalogo deve ser lido com estas distincoes:

- `documented_sources`: fontes com dossie ou especificacao;
- `runtime_providers`: adapters carregados pelo pacote;
- `unified_search_sources`: runtime com opt-in para federacao;
- `studio_sources`: fontes expostas pelo Studio;
- `mcp_sources`: fontes expostas ao MCP;
- `textual_jurisprudence_sources`: fontes adequadas ao objetivo principal;
- `context_sources`: precedentes, informativos, temas ou datasets auxiliares;
- `out_of_scope_sources`: consulta processual e comunicacoes, pertencentes ao
  NanoJud.

Esses conjuntos podem ter tamanhos diferentes. Nenhum numero isolado deve ser
apresentado como cobertura nacional completa.

## Regras De Atualizacao

1. Atualize o runtime ou o registro legado quando a fonte ou sua capacidade
   mudar.
2. Rode `python tools/audit_provider_docs.py --write` para regenerar o
   relatorio documental.
3. Rode `python tools/build_provider_coverage.py --write` para regenerar o
   catalogo distribuido e as visoes de cobertura.
4. Registre validacoes reais em `docs/validation/runs/` antes de promover um
   provider.
5. Mantenha `tests/fixtures/provider_contracts.json` sincronizado com os
   providers que possuem evidencias de estado offline.
6. Nunca edite manualmente `provider-catalog.full.json` ou as tabelas geradas.

O plano de maturidade em [maturity-waves.md](maturity-waves.md) e uma diretriz
manual. Ele orienta prioridades, mas nao substitui os estados calculados pelo
catalogo ou as evidencias live.
