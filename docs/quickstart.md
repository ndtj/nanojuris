# Quickstart

Este guia leva da instalação à primeira pesquisa em poucos minutos. Para
entender as garantias e limitações de cada fonte, leia também
[Capacidades por fonte](source-capabilities.md).

## Pré-requisitos

- Python 3.10 ou superior;
- acesso à internet para consultar fontes públicas;
- respeito aos limites e termos de uso de cada tribunal.

## Instale

Para usar a biblioteca publicada:

```bash
python -m pip install nanojuris
```

Para trabalhar no código-fonte:

```bash
git clone https://github.com/ndtj/nanojuris.git
cd nanojuris
python -m venv .venv
python -m pip install -e ".[dev]"
```

## Faça uma busca com Python

```python
from nanojuris import NanoJurisClient

client = NanoJurisClient()
page = client.search(
    "ICMS consumidor final",
    courts=["STF", "STJ"],
    page_size=5,
)

print(f"Resultados: {page.total}")
for decision in page.results:
    print(decision.court, decision.number)
    print(decision.thesis or decision.summary)
```

O objeto retornado contém registros normalizados e rastreabilidade da fonte.
Uma busca pode retornar resultados, vazios, limitações ou erros parciais; o
cliente mantém essas diferenças observáveis para evitar falso sucesso.

## Use a CLI

```bash
nanojuris buscar "ICMS consumidor final" --orgaos STF,STJ --limite 5
```

Formatos de saída:

```bash
# Revisão humana
nanojuris buscar "ICMS consumidor final" --formato markdown

# Planilhas e jurimetria
nanojuris buscar "ICMS consumidor final" --formato csv

# Pipelines e agentes de IA
nanojuris buscar "ICMS consumidor final" --formato jsonl

# Envelope canônico com metadados de execução
nanojuris buscar "ICMS consumidor final" --formato canonical-jsonl
```

## Descubra fontes antes de pesquisar

```bash
nanojuris fontes
nanojuris diagnostico --fonte tjdf_juris
nanojuris tribunais --implementados
nanojuris tribunais --ramo state --uf SP
```

No SDK:

```python
from nanojuris import NanoJurisClient, list_courts

client = NanoJurisClient()
for source in client.list_sources():
    print(source.source, source.document_types)

print([court.code for court in list_courts(branch="state", state="SP")])
```

## Persista uma pesquisa auditável

```bash
nanojuris buscar "ICMS consumidor final" \
  --store nanojuris.db \
  --label "Pesquisa ICMS"

nanojuris store stats nanojuris.db
nanojuris store runs nanojuris.db
nanojuris store query nanojuris.db --kind decision --tribunal TJSP
nanojuris store export nanojuris.db run-... --formato csv
```

O `run_id` identifica a execução e permite exportar ou paginar o mesmo
conjunto depois:

```bash
nanojuris store export nanojuris.db run-... \
  --formato jsonl \
  --limite 100 \
  --offset 100
```

Para uso no SDK:

```python
from nanojuris import NanoJurisClient, SQLiteStore

client = NanoJurisClient()
with SQLiteStore("nanojuris.db") as store:
    records = client.search_and_store("ICMS", store=store)
    print(f"Registros salvos: {len(records)}")
```

Veja [Armazenamento](storage.md) para o modelo de runs, exportadores e o
caminho de evolução para PostgreSQL.

## Inteiro teor público

Quando a fonte disponibiliza o documento sem login, captcha ou outro controle
de acesso, o SDK pode obter o conteúdo e preservar seu hash:

```python
document = client.get_document(
    "tjsp-cjsg-20787558-0",
    source="tjsp_cjsg",
)

print(document.sha256)
print(document.byte_size)
print(document.text[:1000])
```

O hash, o tamanho, a URL e a trace permitem verificar qual conteúdo foi
recuperado. O NanoJuris não tenta contornar bloqueios da fonte.

## MCP para agentes de IA

```bash
python -m pip install "nanojuris[mcp]"
nanojuris-mcp
```

Configure o cliente de IA para iniciar `nanojuris-mcp` localmente. O
[guia de MCP](mcp.md) explica configuração, ferramentas, store permitido e
boas práticas de segurança.

## Fluxos prontos

```bash
# Demonstração de jurimetria
python examples/idpj_jurimetry_demo.py

# Consulta de jurisprudência do TJSP/CJSG
nanojuris buscar "infanticídio" --fonte tjsp_cjsg --limite 5

# Consulta de precedente público do TJDFT
nanojuris buscar "responsabilidade civil" --fonte tjdf_juris --limite 5
```

## Próximos passos

- [Arquitetura](architecture.md) para entender as camadas;
- [Contratos de fonte](source-contracts/README.md) para conhecer as rotas;
- [Dossiês por provider](providers/README.md) para escolher uma fonte;
- [Desenvolvimento de providers](provider-development.md) para contribuir;
- [Uso responsável](responsible-use.md) antes de automatizar decisões.
