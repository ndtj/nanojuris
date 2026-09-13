# Design - TJAC Ementario

## Fonte e transporte

O endpoint oficial e a pagina de transparencia do TJAC. O adapter usa por
padrao o volume semestral atual publicado no WordPress. A configuracao permite
trocar o URL por outro volume oficial sem alterar o parser. Cada busca executa
uma leitura bounded do PDF; nao ha cache pesquisavel nem corpus persistido.

Limites: 8 MiB, 300 paginas, timeout compartilhado, intervalo cooperativo,
HTTPS, allowlist de host e no maximo 100 registros retornados localmente.

## Parser

`pypdf` extrai texto pagina a pagina. Um novo bloco inicia em um cabecalho
`TRIBUNAL ...` e e aceito somente quando contem um numero CNJ no padrao
brasileiro. O relator, data de julgamento, tipo processual e texto da ementa
sao extraidos por seletores textuais conservadores. O bloco completo e mantido
em `raw` para auditoria; texto insuficiente e rejeitado.

## Contrato canonico

Registros usam `authority=TJAC`, `branch=state`, `degree=second`,
`instance=second`, `collection=TJAC_EMENTARIO`, `document_type=acordao_ementa`
e `source=tjac_ementario_jurisprudencia`. O volume e uma colecao editorial do
Tribunal Pleno; `total_known=false`, ordenacao `source_order` e completude
explicitamente parcial.

## Documentos

O PDF do volume e a fonte documental primaria. Nao existe link individual
observado no volume; `document_url` aponta para o volume e `get_document` pode
reconstruir um documento textual bounded a partir do registro observado. OCR nao
sera acionado automaticamente.

## Federacao e rollback

O provider participa da federacao com peso normal de fonte parcial, sem quota de
tribunal e sem afirmar cobertura integral. Remover o provider da lista runtime
ou definir `unified_opt_in_sources` vazio e o rollback operacional. Nenhuma
alteracao de producao ou deploy faz parte deste SDD.

## Riscos

- volume pode mudar URL ou layout;
- PDF pode ser imagem-only;
- total entre volumes e desconhecido;
- ementas podem conter caracteres corrompidos por fonte PDF.

Todos os riscos sao estados observaveis e cobertos por fixtures de schema,
vazio e limite.
