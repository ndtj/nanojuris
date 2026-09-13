# Verification — SDD 0112

## Evidência

- `docs/provider-discovery/tre-sjur-first-degree-live-20260911.json`
  registra TRE-MG HTTP 200, registros textuais e rótulo `Sentença`; corpos não
  foram persistidos.
- A mesma sonda retornou 1.000 registros tanto para página 1 quanto para
  página 2, mantendo o gate de paginação aberto.

### Sondagem multi-UF (2026-09-12)

Executado `python tools/probe_tre_sjur_first_degree.py` com 27 requisições
oficiais seriais, intervalo mínimo de dois segundos, limite de 8 MB e sem
persistência de corpos. O resultado foi: 23 respostas com apenas rótulos de
segundo grau, TRE-MG com rótulos mistos (950/1.000 de primeiro grau), TRE-SC
com vazio autoritativo e TRE-GO/TRE-PB com resposta acima do limite. A sonda
não promoveu nenhum binding e não alterou a decisão de manter a família fora da
federação padrão. Evidência: `docs/provider-discovery/tre-sjur-first-degree-multi-uf-live-20260912.json`.

### Filtro remoto de tipo (2026-09-12)

Foi enviada uma sonda bounded à rota oficial usando o filtro publicado pela
SPA `descricaoTipoDecisao.keyword=Sentença` em todas as 27 UFs. TRE-MG
retornou 10.000 no total remoto e 1.000 registros de sentença na janela; os
outros 26 TREs retornaram total zero autoritativo. Nenhum corpo foi persistido.
Evidência:
`docs/provider-discovery/tre-sjur-type-filter-live-20260912.json`.

### Contrato da SPA e codificação (2026-09-12)

A inspeção bounded do JavaScript público confirmou que a SPA envia `POST
/public/pesquisa/simples` com `termoPesquisa` serializado, `pagina` (base zero),
`tamanho` e `tribunais`; o campo de tipo é
`descricaoTipoDecisao.keyword` e usa rótulos UTF-8 normais. O registro da
inspeção não contém corpos de resposta: `docs/provider-discovery/tre-sjur-frontend-contract-live-20260912.json`.
O endpoint continua limitando a janela observada e não prova paginação
exaustiva; a decisão de manter `page > 1` rejeitado permanece válida.

## Comandos

```text
python -m pytest -q tests/test_tre_sjur_jurisprudencia.py
python -m ruff check src/nanojuris/providers/tse_sjur_jurisprudencia.py
python -m mypy src/nanojuris/providers/tse_sjur_jurisprudencia.py
python tools/validate_sdd.py
```

## Decisão

Implementação local concluída como **runtime opt-in**: o dispatcher e os
bindings explícitos por TRE estão registrados no cliente normal, mas a
capability continua `unified_search=false` e fora da federação padrão. Isso
permite uso explícito sem declarar completude nacional. Os gates de paginação e
detalhe/PDF continuam abertos; revisão humana/legal permanece necessária antes
de qualquer federação. Nenhum commit, push, release, deploy ou alteração de
produção foi feito.

## Resultados

Os testes focados validam o isolamento de primeiro grau, a rejeição de
acórdãos e tipos desconhecidos, a autoridade TRE explícita e a permanência
fora da federação padrão. A sonda live confirmou uma janela textual pública no
TRE-MG, mas a repetição entre páginas impede declarar completude. O runtime
opt-in não aumenta a cobertura federada nem a contagem de superfícies completas.

## Rastreabilidade

- Implementação: `src/nanojuris/providers/tse_sjur_jurisprudencia.py`.
- Exports: `src/nanojuris/providers/__init__.py` e
  `src/nanojuris/providers/tre_sjur_jurisprudencia.py`.
- Fixture/teste: `tests/fixtures/tre_sjur_first_degree_success.json` e
  `tests/test_tre_sjur_jurisprudencia.py`.
- Contrato: `docs/providers/tre_sjur_first_degree/README.md` e
  `docs/source-contracts/tre_sjur_first_degree.md`.
- Sondagem multi-UF: `docs/provider-discovery/tre-sjur-first-degree-multi-uf-live-20260912.json`
  e `docs/provider-discovery/tre-sjur-first-degree-multi-uf-live-20260912.md`.
- Filtro remoto: `docs/provider-discovery/tre-sjur-type-filter-live-20260912.json`.

### Filtros textuais e temporais

O adapter agora traduz, somente para bindings TRE, os campos comprovados pela
SPA: `case_class` (`siglaClasse.keyword`), `rapporteur` (`relatores.nome`),
`party_name` (`partes.nomeParte`), `judgment_date_from/to`
(`dataDecisao`) e `published_from/to` (`publicacoes.dataPublicacao`). Datas
são serializadas no formato `dd/MM/yyyy` usado pela interface. Filtros sem
contrato continuam rejeitados antes da rede; nenhum refinamento é descartado
silenciosamente.

A sonda bounded `docs/provider-discovery/tre-sjur-filter-live-20260912.json`
usou TRE-SP, tipo `acordao`, classe `RC` e intervalo de julgamento de dois
dias. A fonte respondeu vazio autoritativo em 542,92 ms com 61 bytes e os
filtros remotos foram registrados no `SearchPage`; nenhum corpo bruto foi
persistentemente armazenado. O vazio é válido apenas para a combinação
restrita da sonda e não altera o diagnóstico de paginação não comprovada para
consultas temáticas.

### Janela grande com tipo explícito (2026-09-12)

TRE-GO e TRE-PB excederam o limite anterior de 8 MB quando consultados com a
lista completa de tipos de segundo grau. O limite do transporte SJUR foi
elevado para 16 MB, ainda com leitura bounded em memória e sem persistência de
corpo. Uma sonda serial com `document_type=acordao` retornou um registro válido
em cada UF (5.444.253 e 4.188.662 bytes, respectivamente); ambos permanecem
`total_known=false` e `is_complete=false`, pois a fonte continua ignorando a
paginação remota. Evidência: `docs/provider-discovery/tre-sjur-large-window-live-20260912.json`.
### Gate de documento do primeiro grau (2026-09-12)

Uma chamada pública limitada ao TRE-MG, com `document_type=sentenca`, retornou
dois registros HTTP 200 com rótulo explícito `Sentença`, grau `first` e texto
integral inline (2.490 e 2.579 caracteres). Ambos informaram
`temInteiroTeorPDF=false` e não forneceram URL de PDF. Os corpos foram
descartados; apenas comprimentos e fingerprints SHA-256 foram registrados em
`docs/provider-discovery/tre-mg-first-degree-document-gate-live-20260912.json`.
Isso confirma a capacidade de texto da janela observada, mas não fecha o gate
de detalhe/PDF (`T007`) nem o de paginação (`T006`). A família permanece
runtime opt-in e fora da federação padrão.
Uma tentativa bounded adicional no endpoint oficial de download para o código
observado (`3455387`) respondeu HTTP 200 com `Content-Type` declarado como PDF,
mas 67 bytes de texto de erro do provedor (``Falha ao recuperar arquivo do
SitDoc``), não um PDF válido. O adapter não deve tratar esse `200` como
inteiro teor disponível; o gate `T007` permanece aberto.
### Alinhamento do limite da sonda (2026-09-12)

A ferramenta `tools/probe_tre_sjur_first_degree.py` passou a usar limite de
16 MB, igual ao transporte do adapter. Isso permite analisar bounded windows
maiores de TRE-GO/TRE-PB sem classificá-las prematuramente como resposta
indisponível. O limite continua em memória, serial e sem persistência de corpo;
o teste `tests/test_tre_sjur_first_degree_probe.py` fixa esse contrato.
