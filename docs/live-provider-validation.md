# Live provider validation

O NanoJuris separa tres garantias diferentes:

- **offline**: fixtures e testes deterministas do parser;
- **health**: a fonte respondeu ou apresentou uma falha operacional;
- **validation**: a resposta live passou pelo contrato normalizado minimo.

## CLI

Valide uma ou mais fontes com uma consulta pequena:

```bash
nanojuris validar --fontes tjdf_juris,tst_jurisprudencia \
  --texto "responsabilidade civil" --timeout 60
```

O comando retorna JSON com `status`, `checks`, `failed_checks`, quantidade,
total informado pela fonte, paginacao, URL de origem e `source_trace`.

`valid` e `empty` sao resultados aprovados. `contract_invalid` indica que a
fonte respondeu, mas a normalizacao perdeu uma garantia minima. `blocked`,
`rate_limited`, `source_unavailable`, `source_changed` e `timeout` sao falhas
classificadas e devem orientar a investigacao, sem serem convertidas em
resultado vazio.

## MCP

Agentes podem chamar `source_validation` com `sources`, `text` e `timeout`.
Depois devem reportar ao usuario as fontes aprovadas, vazias e falhas, sem
ocultar uma fonte que nao respondeu.

## GitHub Actions

O workflow `Live provider validation` e manual (`workflow_dispatch`). Ele:

1. instala o pacote em um ambiente limpo;
2. executa uma consulta pequena nos providers escolhidos;
3. publica `provider-validation.json` como artefato;
4. falha visivelmente quando a validacao nao passa.

Chamadas live nao fazem parte do CI de pull requests porque portais publicos
podem aplicar limites, alterar contratos, exigir controles de acesso ou ficar
temporariamente indisponiveis. A validacao nunca tenta contornar CAPTCHA, WAF,
login ou geoblock.
