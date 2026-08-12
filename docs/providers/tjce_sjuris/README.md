# TJCE - SJURIS

Status atual: `candidate_needs_har`. A superficie oficial existe e o frontend
revela um gateway de dados, mas a rota de resultados ainda nao foi reproduzida
em uma chamada HTTP limpa e repetivel.

## Identidade

- Tribunal: Tribunal de Justica do Estado do Ceara.
- Sistema: SJURIS - Sistema de Busca de Jurisprudencia.
- Portal oficial: `https://sjuris.tjce.jus.br/`.
- Categoria: `court_jurisprudence`.
- Familia tecnica provavel: SPA Angular com gateway REST.
- Este provider e separado de `tjce_cjsg`: o SJURIS integra dados do PJe e,
  progressivamente, do SAJ, enquanto o CJSG e a superficie e-SAJ legada.

## Evidencia oficial

O portal institucional do TJCE publica o SJURIS como a pesquisa de acordaos
PJe e informa que a busca cobre acordaos, decisoes monocraticas e sumulas. O
projeto oficial tambem registra a integracao progressiva dos dados do SAJ com
o SJURIS.

Fontes oficiais:

- [Pesquisa de Acórdao - PJe - SJURIS](https://sjuris.tjce.jus.br/)
- [Sistema de buscas de jurisprudencias passa a disponibilizar dados do SAJ](https://www.tjce.jus.br/noticias/sistema-de-buscas-de-jurisprudencias-passa-a-disponibilizar-dados-do-saj/)
- [TJCE implementa melhorias no SJURIS](https://www.tjce.jus.br/noticias/tjce-implementa-melhorias-em-novo-sistema-de-busca-de-jurisprudencias/)

## Rotas observadas

### Portal

```text
GET https://sjuris.tjce.jus.br/
```

A resposta publica e uma casca de aplicacao SPA. A interface exibe pesquisa por
palavras-chave, operadores (`e`, `ou`, `nao`, frase exata e operadores de
proximidade), base, filtros avancados, orgao julgador, relator, data de
julgamento e ordenacao.

### Gateway preliminar

Durante a carga do frontend foi observado no proprio portal o seguinte recurso:

```text
GET https://gateway.tjce.jus.br/sjuris/api/v1/jurisprudencia/buscaListaCampos/4
```

O recurso aparenta fornecer campos/catalogos da busca. A janela automatizada
retornou erro de conexao no navegador, portanto metodo, headers obrigatorios,
versao `4` e formato de resposta ainda sao pendentes. Nenhum endpoint de busca
de resultados foi inferido a partir desse sinal.

## Contrato ainda nao confirmado

Faltam evidencias para afirmar:

- metodo e payload da rota de resultados;
- identificador estavel de cada decisao;
- paginacao, ordenacao e total;
- filtros e ids aceitos pelo gateway;
- rotas de detalhe e inteiro teor;
- separacao entre dados PJe, SAJ, sumulas e documentos normativos;
- comportamento de vazio, erro, rate limit e controle de acesso.

## Dados esperados da interface

O modelo de pesquisa sugere os seguintes campos, que devem ser confirmados na
resposta real e nunca criados por heuristica:

- termo livre e operadores;
- base documental;
- orgao julgador;
- relator ou magistrado;
- data de julgamento;
- tipo documental, incluindo acordao, decisao monocratica e sumula;
- ementa, numero do processo, classe e URL oficial;
- texto do documento, somente quando a fonte o devolver explicitamente.

## Decisao de implementacao

Ainda nao criar `src/nanojuris/providers/tjce_sjuris.py`. O proximo passo e
capturar um HAR publico com uma busca curta, um vazio, pagina seguinte e
abertura de um resultado. Depois reproduzir a chamada com sessao limpa,
headers minimos e verificacao TLS normal.

Nao usar cookies pessoais, captcha, bypass de WAF ou endpoints de perfis
restritos. Se o gateway continuar indisponivel, o status permanece
`candidate_needs_har`.

## MCP

Enquanto nao houver resposta decisoria reproduzida, o MCP deve omitir esta
fonte da busca executavel e informa-la somente como candidato documental. A
fonte nao deve ser apresentada ao agente como provider disponivel, nem deve
receber chamadas por uma rota de gateway ainda nao confirmada.

## Proximos passos

1. Capturar um HAR sem cookies pessoais contendo uma busca curta, um resultado
   vazio, uma pagina seguinte e a abertura de um resultado.
2. Reproduzir cada chamada com sessao HTTP limpa, headers minimos e verificacao
   TLS normal.
3. Preservar fixtures pequenas de sucesso, vazio, erro e detalhe, removendo
   somente segredos e dados de sessao, sem alterar o conteudo juridico publico.
4. Atualizar este dossie com o contrato confirmado antes de criar o provider.

## Promocao

Para `candidate_ready`, exigir:

1. resposta JSON ou HTML decisoria real;
2. payload de busca e resposta de vazio preservados em fixtures;
3. ids, campos, paginacao e limites documentados;
4. teste de parser offline e classificacao de erros;
5. dossie atualizado antes de qualquer provider runtime.
