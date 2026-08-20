# TJRJ eJURIS - Jurisprudencia Legada

## Identidade

- Fonte oficial: eJURIS do Tribunal de Justiça do Estado do Rio de Janeiro.
- Categoria: `court_jurisprudence`.
- Família técnica: `webforms_jurisprudence`.
- Entrada institucional: `https://www.tjrj.jus.br/web/portal-conhecimento/consulta-a-jurisprudencia`.
- Superfície observada: `https://www3.tjrj.jus.br/EJURIS/ConsultarJurisprudencia.aspx`.
- Status: `candidate_needs_har`; sem provider runtime.

## Contrato observado

A superfície legada responde como WebForms público e expõe campos jurídicos de
pesquisa, estado de formulário (`__VIEWSTATE`/`__EVENTVALIDATION`) e scripts
de reCAPTCHA. O snapshot local não contém uma submissão pública reproduzível,
um schema de resultados, paginação ou rota de detalhe sem essa proteção.

Rotas e superfícies separadas:

- portal institucional de jurisprudência;
- `GET /EJURIS/ConsultarJurisprudencia.aspx` para o formulário;
- resultados, detalhe e inteiro teor ainda não promovidos.

O eJURIS não é fallback do provider `tjrj_eproc_jurisprudencia`: as bases têm
contratos e acervos distintos.

## Dados e filtros

Os labels do formulário indicam pesquisa jurídica, mas não comprovam campos
canônicos retornados. Não classificar o HTML do formulário como decisão,
ementa ou inteiro teor. Permanecem desconhecidos o payload final, o formato de
resultado, a ordenação, a paginação, o identificador estável e o download.

## Estados e limites

- formulário institucional: superfície pública observada;
- busca decisória: `access_controlled`/inconclusiva no snapshot local;
- reCAPTCHA: presente na superfície observada;
- resultado vazio: não distinguido de bloqueio;
- mudança de contrato: deve ser reportada como diagnóstico, nunca como zero.

Não versionar cookies, tokens, credenciais ou dados de desafio. Não criar
automação de busca enquanto o contrato público não puder ser reproduzido sem
validação humana.

## Fixtures e promoção

Não há fixture decisória válida para este candidato. Para promoção serão
necessárias, no mínimo, fixtures públicas de sucesso, vazio, erro de acesso,
paginação, detalhe e inteiro teor, além de parser canônico e teste offline.

## MCP

Expor somente diagnóstico e estado de descoberta, se necessário. Não incluir
na busca unificada nem prometer decisões do eJURIS.

## Próximos passos

- [ ] obter contrato público reproduzível de busca sem reCAPTCHA;
- [ ] confirmar payload WebForms e estados de resultado;
- [ ] capturar fixtures públicas de sucesso, vazio e erro;
- [ ] decidir se o acervo é complementar ao eproc ou apenas histórico.
