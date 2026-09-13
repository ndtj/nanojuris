# Design — SDD 0112

## Reutilização

`TreSjurFirstDegreeProvider` compartilha `SharedHttpClient`, allowlist,
timeout, limites de bytes, rate limit, DSL e parser de `tse_sjur_jurisprudencia`.
O único overlay é o escopo de grau: a classe base recebe `degree_scope` e
normaliza o nome/capabilities sem duplicar transporte.

## Contrato de classificação

`_infer_tre_degree` continua tri-state (`first`, `second`, `None`). O adapter de
primeiro grau aceita apenas `first`; `second` e `None` são rejeitados. A família
fica isolada por autoridade e usa a rota oficial
`/{tre}/sjur-pesquisa-backend/rest/public/pesquisa/simples`.
When the scope is `first`, the adapter also sends the official
`descricaoTipoDecisao.keyword=["Sentença"]` filter. A serial bounded probe of
all 27 UFs found a filtered window only in TRE-MG and authoritative zero in the
other 26 TREs; local filtering remains mandatory as a defensive check.

## Paginação e completude

A fonte observada pode ignorar `pagina` e `tamanho`, retornando uma janela de até
1.000 registros. O provider aceita apenas `page=1`, preserva o total como não
conhecido após o filtro local e nunca anuncia exaustividade. A resposta pode
conter decisões de graus mistos; a filtragem local é registrada em
`completeness_reason`.

## Registro e operação

O binding é candidato/opt-in, com autoridade obrigatória. Fixtures usam somente
dados sanitizados e cobrem sentença, acórdão/ambíguo, vazio, schema inválido e
janela duplicada. Uma rota pública com HTTP 200 não é promoção: cada UF ainda
precisa de evidência independente de paginação e documento.

## Sondagem multi-UF

Uma ferramenta de descoberta bounded pode consultar uma janela pública por TRE,
em série e com intervalo mínimo de dois segundos. Ela registra somente status
HTTP, tamanho, hash, total declarado, tipos de decisão e classificação; corpos,
cookies e identificadores pessoais não são persistidos. A sondagem não promove
UF automaticamente e não repete chamadas diante de CAPTCHA, WAF, 403, 429 ou
qualquer controle de acesso.
