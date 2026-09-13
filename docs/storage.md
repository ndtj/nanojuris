# Storage

NanoJuris adota uma estrategia de storage em duas etapas:

1. SQLite como backend local padrao e sem dependencia externa.
2. PostgreSQL como backend futuro para producao, equipes e bases maiores.

## Por que SQLite primeiro

SQLite e a melhor escolha inicial para um projeto open source nacional e
acessivel porque:

- funciona sem servidor;
- usa apenas a biblioteca padrao do Python;
- roda em Windows, macOS e Linux;
- facilita testes, demos, notebooks e uso por advogados individuais;
- preserva dados localmente antes de qualquer infraestrutura corporativa;
- permite evoluir o contrato de store antes de fixar uma dependencia externa.

## Quando PostgreSQL sera melhor

PostgreSQL passa a ser superior quando o uso envolver:

- multiplos usuarios;
- jobs concorrentes;
- bases muito grandes;
- API/MCP servidos em rede;
- integrações corporativas;
- backup, replicacao e observabilidade de producao.

O contrato do store deve permanecer portavel para que `SQLiteStore` e um futuro
`PostgresStore` compartilhem a mesma semantica.

O contrato Python atual e `CanonicalStore`, implementado por `SQLiteStore` e
destinado a guiar backends futuros.

## Uso local

```python
from nanojuris import CanonicalDecision, SQLiteStore

with SQLiteStore("nanojuris.db") as store:
    store.save(
        CanonicalDecision(
            id="dec-1",
            source="tjsp_cjsg",
            court="TJSP",
            case_number="0003938-14.2017.8.26.0323",
        )
    )

    print(store.count(kind="decision"))
    print(store.get("decision", "dec-1"))
```

Buscar e salvar em uma unica chamada:

```python
from nanojuris import NanoJurisClient, SQLiteStore

client = NanoJurisClient()

with SQLiteStore("nanojuris.db") as store:
    records = client.search_and_store("ICMS", store=store)
    print(len(records))
```

Buscar, salvar e criar uma busca rastreavel:

```python
from nanojuris import NanoJurisClient, SQLiteStore

client = NanoJurisClient()

with SQLiteStore("nanojuris.db") as store:
    run = client.search_and_store_run("ICMS", store=store, label="Pesquisa ICMS")
    records = store.get_research_run_records(run.id)
```

Consultar registros com filtros estruturados:

```python
with SQLiteStore("nanojuris.db") as store:
    decisions = store.query_records(
        kind="decision",
        court="TJSP",
        subject="Homicidio Qualificado",
    )
    stats = store.stats()
```

Salvar via CLI:

```bash
nanojuris buscar "ICMS" --store nanojuris.db
```

Consultar via CLI:

```bash
nanojuris store stats nanojuris.db
nanojuris store query nanojuris.db --kind decision --tribunal TJSP
nanojuris store query nanojuris.db --fonte bnp_pangea --limite 20
nanojuris store get nanojuris.db decision dec-1
nanojuris store runs nanojuris.db
nanojuris store run nanojuris.db run-...
nanojuris store records nanojuris.db run-...
nanojuris store export nanojuris.db run-... --formato jsonl
nanojuris store export nanojuris.db run-... --formato csv
nanojuris store export nanojuris.db run-... --formato jsonl --limite 100 --offset 200
```

Os filtros de `store query` cobrem `--kind`, `--fonte`, `--tribunal`,
`--numero`, `--assunto`, `--relator`, `--tipo-decisao`, `--tipo-precedente`,
`--canonical-key`, `--publicacao-de`, `--publicacao-ate` e `--limite`.

## Schema atual

O `SQLiteStore` usa uma tabela unica `canonical_records`, preservando o JSON
canonico completo e colunas indexaveis para filtros frequentes:

- `kind`
- `id`
- `source`
- `court`
- `case_number`
- `subject`
- `rapporteur`
- `decision_type`
- `precedent_type`
- `publication_date`
- `document_type`
- `canonical_key`
- `record_json`
- `source_trace_json`
- `extraction_trace_json`
- `created_at`
- `updated_at`

Buscas salvas ficam em `research_runs`, e seus vinculos com registros canonicos
ficam em `research_run_records`. A coluna opcional `manifest_json` preserva o
manifesto versionado de uma coleta (completude, fingerprints, janela e
falhas), sem armazenar bytes brutos. Isso permite auditar e retomar uma
pesquisa por `run_id` sem duplicar os dados canonicos; bancos legados recebem a
coluna automaticamente na inicialização.

## Exportacao de buscas salvas

`nanojuris store export` transforma um `ResearchRun` em formatos objetivos:

- `markdown`: leitura humana, auditoria e compartilhamento com escritorio;
- `csv`: planilhas, BI e jurimetria;
- `jsonl`: pipelines de dados e processamento incremental;
- `json`: envelope completo com metadados do run e registros para agentes.

`records` e `export` aceitam `--limite` e `--offset`. A ordenacao e estavel por
data de publicacao, atualizacao e id, permitindo percorrer o mesmo run em paginas.

Essa abordagem evita perda de dados enquanto o schema nacional ainda evolui.

## Tombstones com prova de fonte

Remoção não é inferida pela ausência em uma busca. Quando um tribunal publica
um tombstone, manifesto de ausência explícita ou retratação, o chamador pode
registrar a evidência de forma opt-in:

```python
from nanojuris import SQLiteStore, TombstoneEvidence

with SQLiteStore("nanojuris.db") as store:
    store.record_tombstone(
        TombstoneEvidence(
            source="tjsp_cjsg",
            canonical_key="decision|tjsp_cjsg|tjsp|0003938-14.2017.8.26.0323|acordao",
            evidence_url="https://www.tjsp.jus.br/arquivo/remocao.csv",
            evidence_sha256="sha256:" + "a" * 64,
            evidence_type="official_absence_manifest",
            observed_at="2026-09-01T12:00:00Z",
            reason="manifesto oficial informa remoção explícita",
        )
    )
```

O registro exige URL HTTPS pública, SHA-256 e tipo de evidência reconhecido.
Ele preserva a decisão canônica e apenas acrescenta provenance consultável por
`list_tombstones`; não oculta, remove ou rebaixa registros automaticamente.
O contrato JSON está em `docs/schemas/tombstone-evidence-v1.schema.json`.

## Deduplicacao canonica

O store calcula uma `canonical_key` para reduzir duplicidade entre resultados que
representam o mesmo registro juridico objetivo, mesmo quando a fonte muda o id
tecnico retornado.

Regras atuais:

- decisao: `decision|source|court|case_number|decision_type`;
- precedente: `precedent|source|court|precedent_type|number`;
- documento: `document|source|document_type|sha256/url/id`.

Quando um novo registro chega com a mesma `canonical_key`, o store atualiza o
registro existente em vez de duplicar a base. O `id` canonico mais recente passa
a ser o id armazenado.

Consulta por chave canonica via CLI:

```bash
nanojuris store query nanojuris.db --canonical-key "decision|tjsp_cjsg|tjsp|0003938-14.2017.8.26.0323|acordao"
```

Consulta por chave canonica via Python:

```python
with SQLiteStore("nanojuris.db") as store:
    records = store.query_records(
        canonical_key="decision|tjsp_cjsg|tjsp|0003938-14.2017.8.26.0323|acordao"
    )
```

## Exportacoes canonicas

Pipelines de dados podem usar:

- `to_canonical_jsonl(page_or_records)` para JSONL canonico;
- `decisions_to_csv(records)` para decisoes;
- `precedents_to_csv(records)` para precedentes;
- `documents_to_csv(records)` para documentos.
