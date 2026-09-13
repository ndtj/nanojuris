# TRT2 Ementário de Jurisprudência

## Identidade

- Autoridade: Tribunal Regional do Trabalho da 2ª Região (`TRT2`).
- Ramo: Justiça do Trabalho (`branch=labor`).
- Grau/instância: segundo grau (`degree=second`, `instance=second`).
- Coleção: `TRT2_EMENTARIO`.
- Tipo documental: ementa de acórdão (`acordao_ementa`).
- Fonte oficial: páginas estáticas do TRT2 em `https://trt2.jus.br`.
- Provider: `trt2_ementario_jurisprudencia`.

## Contrato observado

As páginas de índice são:

- `GET /geral/tribunal2/Ementario/Tribunal_Pleno.html`;
- `GET /geral/tribunal2/Ementario/Corregedoria.html`.

Cada tópico contém uma página HTML própria e pode conter um link PDF oficial
em `.../Ementario/{coleção}/Acordaos/{arquivo}.pdf`. O adapter só segue links
HTTPS cujo host é `trt2.jus.br`; não adivinha rotas nem usa a busca PJe.

## Dados canônicos

O parser preserva `authority`, `branch`, `degree`, `instance`, `collection`,
`document_type`, ementa em `summary`/`full_text`, número/citação quando
publicado, data `DOE` quando publicada, URL do tópico, URL do PDF, hash e
`SourceTrace`. Campos não publicados permanecem ausentes.

## Busca e limites

O índice estático não oferece total nacional nem endpoint de busca textual. Uma
consulta seleciona deterministicamente até 32 tópicos por chamada, priorizando
labels que contêm os termos e aplicando o restante localmente. A resposta é
`pagination_mode=local_window`, `total_known=false` e `is_complete=false`.
Isso é uma janela live bounded, não um corpus local e não uma alegação de
exaustividade.

Filtros suportados: `text`, `exact_phrase`, `number`, `degree`, `instance`,
`branch`, `authority`, `collection`, `document_type` e `page`. Classe,
relator, órgão, datas, partes e `fetch_details` são explicitamente
`unsupported`.

## Documentos

`get_document` só aceita PDF observado no resultado da mesma sessão e valida
host, HTTPS, MIME/magic bytes, tamanho e hash pelo pipeline compartilhado. A
ementa continua disponível quando não há PDF. Não há OCR nem acesso a área
autenticada.

## Estado de disponibilidade

O índice raiz e um tópico foram observados publicamente com HTTP 200 em
2026-09-07. A rechecagem bounded de 2026-09-08 confirmou as raízes de Tribunal
Pleno e Corregedoria com ementas de segundo grau e um PDF oficial; a evidência
está em `docs/provider-discovery/trt2-ementario-live-20260908.json`. O provider
agora participa da federação padrão como fonte parcial: `total_known=false` e
`is_complete=false` continuam obrigatórios. Eventual 403 CloudFront futuro
 permanece bloqueio explícito, não vazio.

## Estados de execução

O provider expõe `success_with_results` quando a janela pública retorna tópicos
e `authoritative_empty` somente quando a própria página confirma ausência. Uma
resposta sem total é `total_known=false`, nunca zero. Timeout, 403, 429,
CloudFront, WAF, TLS ou schema inesperado permanecem `access_blocked`,
`rate_limited`, `transport_error` ou `schema_invalid`. A resposta federada
marca `is_complete=false` e preserva o trace da fonte.

## MCP e diagnóstico

O provider pode ser exposto no MCP e no Studio com a mesma janela bounded. O
diagnóstico deve exibir coleção, total desconhecido, filtros locais e a URL do
documento oficial; não deve sugerir que o ementário seja a busca PJe completa.

## Próximos passos

1. manter smoke live de baixa frequência para as duas raízes;
2. adicionar uma fixture de drift caso o TRT2 altere o HTML;
3. revalidar o PDF oficial quando o parser de documentos oferecer extração
   segura para PDFs imagem-only, sem OCR de CAPTCHA;
4. monitorar 403 CloudFront sem repetir chamadas contra a proteção;
5. manter a fonte como parcial enquanto o TRT2 não publicar total pesquisável.

## Fixtures e promoção

Fixtures: `tests/fixtures/trt2_ementario_index.html`,
`trt2_ementario_topic.html` e `trt2_ementario_topic_no_pdf.html`.
Testes: `tests/test_trt2_ementario_jurisprudencia.py`.

Antes de promover, exigir sucesso live repetível, vazio comprovado, erro,
limite de bytes, bloqueio, drift, paginação/duplicidade e validação de PDF.
HTTP 403/429, timeout ou CloudFront nunca são convertidos em vazio.

## Uso responsável

Usar somente a publicação oficial, com baixa frequência e janela limitada.
Não contornar CloudFront, CAPTCHA, WAF ou qualquer desafio; não usar rotação
de IP/proxy, stealth, token ou cookie de outra sessão.
## Transporte compartilhado (2026-09-08)

Os índices e tópicos públicos do ementário TRT2 usam `SharedHttpClient` com
allowlist oficial (`trt2.jus.br` e `www.trt2.jus.br`), TLS verificado, limite de
1,5 MB, timeout, intervalo por host e sem retry automático. O limite menor por
tópico continua validado no adapter. Desafios, 401/403/407/451, 429, timeout,
TLS, redirecionamento fora da allowlist e schema inválido permanecem estados
explícitos; nenhum é convertido em vazio. PDFs observados continuam passando
pelo pipeline documental compartilhado.
