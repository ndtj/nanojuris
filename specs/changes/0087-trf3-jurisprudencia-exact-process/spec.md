# SDD 0087 — TRF3 acórdãos por processo exato

Status: `in_progress`
Owner: Provider Engineering e Data Quality
Data: `2026-09-07`

## Problema

O portal oficial do TRF3 oferece uma rota pública que lista acórdãos por
número de processo e abre o inteiro teor HTML. A pesquisa textual geral possui
uma interface pública, mas seu contrato de submissão ainda não foi reproduzido
por HTTP limpo. Misturar as duas superfícies criaria uma falsa promessa de
busca nacional.

## Escopo

Implementar `trf3_jurisprudencia` para a consulta exata por número CNJ,
retornando um registro por acórdão, com grau/instância de segundo grau,
links oficiais, parser de documento HTML e preservação dos bytes. O provider
será executável e opt-in, sem federação padrão enquanto a validação live direta
estiver indisponível.

## Critérios de aceitação

**AC-001:** O adapter aceita somente número CNJ exato (20 dígitos após
normalização) e rejeita texto livre ou filtros não suportados.

**AC-002:** Cada resultado aceito declara `authority=TRF3`, `branch=federal`,
`degree=second`, `instance=second`, `collection=TRF3_JURISPRUDENCIA` e
`document_type=acordao`.

**AC-003:** A lista de datas e a rota de detalhe são parseadas sem confundir
consulta processual comum com jurisprudência.

**AC-004:** Timeout, HTTP 403/429, TLS, HTML de controle de acesso e mudança de
schema permanecem estados diagnósticos; nenhum vira vazio.

**AC-005:** O documento preserva HTML original, hash, tamanho, URL final,
`SourceTrace` e texto visível canônico.

**AC-006:** O provider fica fora da federação padrão até chamada live bounded
reproduzível e aprovação dos gates de qualidade.
