# tjmmg_jurisprudencia_api

## Identidade

- Fonte oficial: [TJMMG Jurisprudência](https://jurisprudencia.tjmmg.jus.br/).
- Autoridade: `TJMMG`.
- Ramo: `military`.
- Superfície: jurisprudência textual de segundo grau (`CJSG`).
- Estado: adapter implementado, **opt-in** e bounded; fora da federação padrão.

## Contrato oficial observado

- `GET /jurisprudencia-api/api/jurisprudencia/get`: metadados públicos de
  classes, números, relatores e referências.
- `POST /jurisprudencia-api/api/jurisprudencia/search`: recebe o payload do
  aplicativo oficial e devolve um envelope `{ "collection": [...] }`.
- `GET /jurisprudencia-api/api/jurisprudencia/file?filename=...`: entrega o
  PDF oficial associado ao campo `NomeArquivo`.

O payload preservado pelo adapter usa `searchFilter`, `materia`,
`tipo_decisao`, `numeracao_unica`, `numero_antigo`, `nome_classe`, `relator`,
`relator_acordao`, `cod_revisor`, `referencia`, intervalos de publicação e
julgamento e `sumulas`. Os registros carregam ementa, texto, identificador,
classe, relator, tipo de decisão, número e data de julgamento.

## Dados canônicos

O parser preenche `authority=TJMMG`, `branch=military`, `degree=second`,
`instance=second`, `collection=CJSG`, tipo documental, número, classe, relator,
datas, ementa, inteiro teor, URL do PDF, `raw` e `SourceTrace`. Campos ausentes
permanecem ausentes; o JSON original não é descartado.

## Limite de segurança e semântica de vazio

A fonte não possui paginação server-side: os controles 5/10/20/30 do frontend
apenas recortam a coleção no navegador. Consultas amplas podem exceder o limite
de transporte mesmo com HTTP 200. Por isso o adapter só envia uma busca quando
há número exato ou intervalo fechado de julgamento/publicação. Consultas sem
esse limite são rejeitadas antes da rede; resposta grande é erro de fonte e
nunca lista vazia.

Uma resposta com `collection: []` em consulta bounded é `authoritative_empty`.
Schema ausente, conteúdo inválido, bloqueio, timeout e limite de tamanho
permanecem estados distintos.

## Estados de acesso e extração

O provider distingue `public`, `authoritative_empty`, `source_unavailable`,
`access_control_required`, `rate_limited` e `schema_invalid`. O status HTTP 200
sem envelope válido é mudança de contrato, não vazio. A extração do JSON é
`complete`; o PDF passa por validação de MIME, magic bytes, tamanho e extração
canônica, com aviso explícito quando o arquivo não contém camada textual.

## Inteiro teor

O campo `Texto` é preservado em `full_text` quando fornecido pela busca. Quando
`NomeArquivo` estiver presente, `get_document("tjmmg-file-<arquivo>.pdf")`
busca o PDF oficial, valida o magic `%PDF` e cria `CanonicalDocument` com
`SourceTrace`, hash, MIME e validação de tamanho. O download é explícito; o
search não baixa documentos implicitamente.

## Filtros e paginação

Filtros nativos: texto, frase exata, número, classe, relator e intervalos de
publicação/julgamento. Tipo documental é traduzido para `tipo_decisao`.
`page`, `updated_from` e `updated_to` são não suportados. A paginação é
`none`; a coleção retornada é completa somente dentro do limite bounded.

## Uso responsável e federação

O provider pode ser selecionado com
`NanoJurisClient(include_candidate_providers=True)` ou por seleção explícita.
Não usa CAPTCHA, credenciais, cookies, bypass ou corpus persistente. Continua
opt-in até repetir as sondas bounded, completar fixtures e passar os gates de
qualidade; não é contado como cobertura federada padrão.

Evidência live sanitizada:
`docs/provider-discovery/tjm-mg-jurisprudencia-api-live-20260909.json`.

Revalidação bounded de 2026-09-11 confirmou o mesmo contrato por número exato:
HTTP 200, uma decisão de segundo grau/CJSG, texto integral e URL de documento.
Os metadados e o hash estão em
`docs/provider-discovery/tjm-mg-jurisprudencia-api-live-20260911.json`.

## Fixtures

O parser é coberto por fixture sanitizada de envelope com resultado:
`tests/fixtures/tjmmg_search.json`. O teste também cobre coleção vazia,
envelope inválido, resposta acima do limite, rejeição de consulta ampla,
ausência de paginação inventada e rota PDF. A evidência live registra apenas
metadados, tamanhos, campos e hashes; corpos de fonte não são persistidos.

## Uso via MCP

O contrato pode ser exposto por `source_contracts` e consultas explícitas de
diagnóstico. A integração padrão permanece desabilitada para evitar que uma
consulta textual sem intervalo fechado gere uma resposta não bounded.

## Próximos passos

1. Repetir sondas por número e janela fechada em baixa frequência.
2. Comparar campos da collection com o contrato canônico e ampliar fixtures de
   decisão monocrática quando observada.
3. Só então avaliar `federation_status=enabled`; consultas amplas continuam
   fora do contrato até existir paginação oficial server-side.
