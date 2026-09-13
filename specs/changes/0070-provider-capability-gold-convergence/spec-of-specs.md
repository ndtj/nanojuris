# Programa 0070 — convergência ouro de capacidades dos providers

Status: `proposed`
Owner: Provider Engineering, Data Engineering, Quality e Security
Data: `2026-09-06`

## Resultado final

Cada fonte catalogada deve possuir um inventário verificável de tudo que sua
superfície oficial pública oferece: filtros, opções, ordenações, paginação,
campos de resultado, detalhe, documentos e inteiro teor. O runtime deve expor
essas capacidades sem inventar equivalência entre tribunais e sem omitir dados
oficiais úteis.

O programa não exige que uma fonte implemente recursos inexistentes. Ele exige
que cada recurso esteja em um estado terminal comprovado:

```text
implemented | unsupported_by_source | access_blocked | source_unavailable
```

`unverified` nunca é estado terminal de qualidade ouro. Capacidades que
pertencem ao NanoJud, como consulta processual e timeline, recebem
`out_of_scope_nanojud` em vez de serem implementadas silenciosamente aqui.

## Decomposição

| Pacote | Escopo | Saída independente |
| --- | --- | --- |
| A — verdade única | reconciliar catálogo, runtime, discovery, live e scorecards | um ledger canônico sem contagens contraditórias |
| B — contrato de capacidades | filtros, campos, documentos e evidências tipadas | modelos aditivos e schema versionado |
| C — discovery | busca sistemática em UI, APIs, bundles, catálogos e detalhes | inventário oficial por superfície |
| D — implementação | queries, parsers, detalhes e documentos por família/provider | adapters completos e fixtures diferenciais |
| E — inteiro teor | localizar, baixar, validar, extrair e vincular documentos | `CanonicalDocument` seguro por fonte aplicável |
| F — federação | tradução, pós-filtro, diagnóstico e exposição em SDK/CLI/MCP/Studio | filtros honestos e auditáveis por fonte |
| G — certificação | gates de contrato, dados, documentos, operação e federação | selo ouro reproduzível e revalidável |

## Relação com os SDDs existentes

- 0026 continua sendo o programa nacional superior.
- 0027 define o contrato base; 0070 amplia a granularidade de filtro/campo.
- 0028 continua responsável pelo transporte compartilhado.
- 0029/0039 continuam governando reaproveitamento do Juscraper.
- 0031 mantém o score histórico; 0070 cria um gate ouro estrito e
  multidimensional, sem substituição silenciosa.
- 0032 continua sendo o pipeline documental; 0070 exige sua adoção por fonte.
- 0033 continua responsável por observabilidade live.
- 0038 continua responsável pela semântica federada.
- 0069 continua responsável pela cobertura estadual de segundo grau.

0070 não duplica adapters nem dossiês. Ele gera workpacks por provider a partir
de um ledger e só exige alteração do dossiê quando o contrato observado mudar.

## Invariantes

1. Recursos disponíveis na fonte não podem ficar ocultos no `raw` sem
   classificação.
2. Recurso ausente na fonte não pode ser simulado.
3. Um filtro só é `native` ou `translated` após teste de efeito observável.
4. Um link de documento não equivale a inteiro teor extraído.
5. `HTTP 200` não prova busca, filtro, vazio, detalhe ou documento válido.
6. Ouro de engenharia, ouro operacional e ouro federado são dimensões
   distintas; `provider_gold` exige a convergência das dimensões aplicáveis.
7. Nenhum trabalho deste programa autoriza commit, push, publicação ou deploy.
