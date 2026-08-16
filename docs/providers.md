# Providers

O indice tecnico completo por provider esta em
[docs/providers/](providers/README.md). O catalogo machine-readable para
humanos, CI e agentes esta em
[docs/registry/providers.json](registry/providers.json).

Esta pagina e um ponto de entrada curto. Os detalhes de contrato, campos,
filtros, limitacoes, fixtures e criterios de maturidade ficam nos dossies
individuais e em [source-contracts.md](source-contracts.md).

## Escopo

NanoJuris cobre jurisprudencia textual, precedentes, decisoes, ementas,
documentos decisorios publicos e inteiro teor quando a fonte o entrega sem
controle de acesso.

Consulta processual, DataJud/CNJ, DJEN, comunicacoes judiciais, partes,
movimentacoes e linhas do tempo pertencem ao NanoJud. O mapa de migracao esta
em [migration-to-nanojud.md](migration-to-nanojud.md).

## Descoberta

```bash
nanojuris fontes
nanojuris diagnostico --fonte tjdf_juris
nanojuris contratos --fonte tjdf_juris
```

## Desenvolvimento De Providers

Novos providers devem:

- declarar `ProviderCapabilities` com opt-in explicito para CLI, MCP, Studio e
  busca unificada;
- possuir dossie canonico em `docs/providers/<id>/README.md`;
- possuir contrato legado em `docs/source-contracts/<id>.md` quando promovidos;
- preservar evidencias de origem, parametros, status de acesso e limitacoes;
- falhar explicitamente diante de captcha, login, WAF, segredo de justica ou
  mudanca de contrato;
- retornar modelos canonicos apenas quando o conteudo for jurisprudencial ou
  decisorio.

Use [provider-development.md](provider-development.md),
[source-discovery.md](source-discovery.md) e
[extraction-pipeline.md](extraction-pipeline.md) como guias de implementacao.
