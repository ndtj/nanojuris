# Uso Com Agentes De IA

NanoJuris pode ser usado por agentes locais compativeis com MCP para consultar
jurisprudencia publica brasileira com rastreabilidade. O servidor MCP roda no
ambiente do usuario e nao contorna captcha, login, segredo de justica ou
controle de acesso.

## Instalacao recomendada

Para uso local com pacote publicado:

```bash
uvx --from "nanojuris[mcp]" nanojuris-mcp
```

Para desenvolvimento a partir do repositorio:

```bash
pip install -e ".[mcp]"
nanojuris-mcp
```

Para validar a biblioteca sem MCP:

```bash
nanojuris fontes
nanojuris contratos --resumo
nanojuris contratos --fonte tjdf_juris
```

## Catalogo De Providers Para IA

O ponto de descoberta documental e
[`docs/registry/providers.json`](registry/providers.json). Ele lista todos os
providers implementados e todas as fontes candidatas, com os caminhos dos
dossies canonicos por convencao. Para ler o contrato humano completo de uma
fonte, abra `docs/providers/<source-id>/README.md`.

O catalogo nao substitui o contrato vivo: para providers implementados, sempre
confirme capacidades, maturidade, lacunas e limites com `list_sources`,
`source_contracts` ou os comandos `nanojuris fontes` e `nanojuris contratos`.
Para candidatos, o dossie e evidencia de pesquisa e nao autorizacao para
executar um provider inexistente.

## Configuracao MCP local

Use o comando do servidor como transporte `stdio` no cliente MCP:

```json
{
  "mcpServers": {
    "nanojuris": {
      "command": "uvx",
      "args": ["--from", "nanojuris[mcp]", "nanojuris-mcp"]
    }
  }
}
```

Em ambiente de desenvolvimento local:

```json
{
  "mcpServers": {
    "nanojuris": {
      "command": "nanojuris-mcp"
    }
  }
}
```

## Ordem recomendada para o agente

Antes de consultar fontes reais, o agente deve:

1. Ler o registro documental quando precisar descobrir escopo e limitações.
2. Chamar `list_sources`.
3. Chamar `source_contracts`.
4. Escolher fontes com maturidade adequada para a pergunta.
5. Preferir `search_unified` com um grupo explicito de fontes adequadas; usar
   `search_jurisprudence` quando a pergunta exigir uma fonte especifica.
6. Interpretar separadamente `searched_sources`, `skipped_sources` e `errors`.
7. Usar `get_document` ou `get_decisions` apenas quando a fonte suportar
   documento publico sem bypass.

## Perguntas naturais recomendadas

Exemplos seguros:

```text
Liste as fontes de jurisprudencia maduras para agentes.
```

```text
Busque jurisprudencia sobre IDPJ e explique quais fontes foram consultadas,
puladas ou falharam.
```

```text
Consulte source_contracts para stf_juris e stj_scon e diga se as fontes estao
prontas para pesquisa ampla.
```

```text
Pesquise "incidente de desconsideracao da personalidade juridica" nas fontes
mais adequadas e traga os metadados principais.
```

```text
Rode uma demo de juridimetria sobre IDPJ. Use search_unified com tjdf_juris,
trf4_eproc_jurisprudencia, tjsp_cjsg, stf_juris e stj_scon, page_size 3. Liste
fontes consultadas, puladas, com erro e os primeiros campos objetivos
retornados.
```

## Como interpretar a busca unificada

`search_unified` retorna tres grupos importantes:

| Campo | Significado |
| --- | --- |
| `searched_sources` | Fontes realmente chamadas. |
| `skipped_sources` | Fontes puladas porque nao se aplicavam a pergunta. |
| `routing_summary` | Explicacao pronta para o usuario sobre consultar, pular ou falhar. |
| `errors` | Fontes chamadas que falharam por erro real, acesso ou contrato. |

Isso evita falso diagnostico. Uma consulta textual como `idpj` nao deve chamar
fontes `case_lookup` sem numero CNJ, parte, OAB ou documento. Do mesmo modo,
uma fonte de comunicacoes judiciais nao deve ser usada como jurisprudencia
decisoria.

Se a pergunta trouxer numero CNJ, parte, OAB ou outro identificador, confira
tambem `skipped_sources`. Uma fonte que nao declara o filtro em
`supported_filters` pode ser pulada para evitar falso positivo por texto
parecido. Isso e diferente de uma fonte que foi chamada e falhou: a primeira
decisao e semantica, a segunda e um erro operacional ou de contrato.

## Fontes boas para demonstracao

Segundo a matriz atual de contratos, as fontes mais maduras para agentes sao:

- `tjdf_juris`;
- `trf4_eproc_jurisprudencia`.

Fontes estrategicas, mas que exigem mais cuidado:

- `stf_juris`;
- `stj_scon`;
- `tjsp_cjsg`.

## Troubleshooting

| Sinal | Interpretacao |
| --- | --- |
| `AccessControlRequiredError` | A fonte exigiu captcha/login/validacao; nao tentar bypass. |
| `ParserContractChangedError` | O HTML mudou ou a fixture nao cobre aquele formato. |
| `SourceUnavailableError` | A fonte retornou erro HTTP ou falha de rede. |
| fonte em `skipped_sources` | A fonte nao era adequada para a pergunta. |
| `total_returned=0` sem erro | A busca executou, mas nao encontrou resultados. |

## Inteiro Teor Para Agentes

Quando uma fonte expuser documento publico sem bypass, use `get_document`.
O `tjsp_cjsg`, por exemplo, transforma o HTML publico de `getArquivo.do` em
texto limpo para leitura pelo agente e preserva hash, tamanho, URL, trace e
metadados tecnicos no payload.

Se a fonte devolver PDF puro, captcha, login ou conteudo muito curto, o agente
deve reportar o warning/status e nao tentar contornar a fonte.

## Prompt unico para instalacao assistida

Um usuario pode pedir ao agente:

```text
Instale e configure o NanoJuris MCP localmente usando uvx. Depois rode
list_sources, source_contracts --resumo e uma busca de teste por "idpj".
Nao contorne captcha, login ou controle de acesso; apenas reporte o status das
fontes.
```

## Responsabilidade

NanoJuris extrai dados publicos e auditaveis. Ele nao substitui revisao juridica
profissional, nao interpreta merito automaticamente e nao deve ser usado para
acessar conteudo restrito.
