# Descoberta De Providers - 2026-08-12

Este registro consolida a pesquisa tecnica de novas superficies oficiais de
jurisprudencia e a profundizacao de candidatos ja documentados. A classificacao
separa evidencia institucional, rota observada, resposta juridica reproduzida
e provider pronto para runtime. Uma pagina oficial, por si so, nao e contrato
de adapter.

## Resumo Executivo

- Novo candidato registrado: `tjce_sjuris`.
- Nenhum provider runtime novo foi criado nesta rodada.
- A fila prioritaria permanece `TJBA`, `TJPR`, `TJRR`, `TJPE`, `CNJ` e o
  fechamento do contrato do `TJCE SJURIS`.
- O gateway do TJCE foi observado apenas como recurso preliminar do frontend;
  metodo, payload e resposta de resultados continuam sem confirmacao.
- Nenhum cookie pessoal, token privado, captcha ou bypass de controle de acesso
  foi usado como evidencia.

## Matriz Da Rodada

| Fonte | Evidencia observada | Status | Proximo gate |
| --- | --- | --- | --- |
| TJCE SJURIS | Portal oficial de busca PJe/SAJ; frontend revela gateway de catalogo | `candidate_needs_har` | HAR publico com busca, vazio, pagina, detalhe e inteiro teor |
| TJPR Jurisprudencia | Busca HTML publica com total, filtros, metadados de resultado e links de detalhe | `candidate_ready` | fixture de sucesso/vazio/pagina e parser offline |
| TJRR Juris | Formulario publico JSF com termo, operadores, processo, relator, datas, orgao e especies | `candidate_ready` | fixture de postback e confirmacao de paginacao |
| TJPE Jurisprudencia | Portal institucional confirma pesquisa textual e base de jurisprudencia; contrato REST ja esta no dossie | `candidate_ready` | fixture REST em ambiente TLS normal e classificacao de erros |
| CNJ Informativos | Pagina oficial filtravel e PDFs oficiais com itens de informativo | `candidate_ready` documental | fixture HTML/PDF e parser de itens curados |
| TJCE Informativos | Pagina institucional e links oficiais de acervo curado | `candidate_ready` documental | fixture HTML e links PDF |

## TJCE SJURIS

O [portal oficial do SJURIS](https://sjuris.tjce.jus.br/) apresenta uma busca
por palavras-chave com operadores booleanos e de proximidade, filtros por base,
orgao julgador, relator, data e ordenacao. O TJCE informa que o sistema cobre
acordaos, decisoes monocraticas e sumulas, e registra a integracao progressiva
de dados do SAJ. Consulte a [noticia oficial sobre a integracao do SAJ]
(https://www.tjce.jus.br/noticias/sistema-de-buscas-de-jurisprudencias-passa-a-disponibilizar-dados-do-saj/)
e o registro de [melhorias no SJURIS]
(https://www.tjce.jus.br/noticias/tjce-implementa-melhorias-em-novo-sistema-de-busca-de-jurisprudencias/).

Durante a carga do frontend foi exibido o recurso:

```text
GET https://gateway.tjce.jus.br/sjuris/api/v1/jurisprudencia/buscaListaCampos/4
```

Esta observacao nao prova que o recurso seja a busca de decisoes. Ainda faltam
metodo, headers, payload, resposta, ids dos catalogos, paginacao, detalhe e
inteiro teor. Por isso o dossie [tjce_sjuris]
(providers/tjce_sjuris/README.md) exige HAR publico antes de qualquer codigo.

## TJPR

A [pesquisa publica de jurisprudencia do TJPR]
(https://portal.tjpr.jus.br/jurisprudencia/publico/pesquisa.do?actionType=pesquisarRefinado&filtro=true)
retorna total, faixa de resultados e filtros de classe, relator, comarca, orgao
julgador, assunto e ano. Os resultados observados exibem processo, especie,
relator, orgao, comarca, data de julgamento, ementa e link de detalhe. E um
candidato forte para o proximo parser HTML, mas o provider ainda deve ser
protegido por fixtures e por uma classificacao explicita de falhas HTTP.

## TJRR

O [portal oficial de jurisprudencia do TJRR]
(https://jurisprudencia.tjrr.jus.br/index.xhtml) oferece termo livre, operadores
`E`, `OU` e `NAO`, frase exata, numero de processo SISCOM/PROJUDI, relator,
periodo, procedimento, orgao julgador, ementa/indexacao e especie. Tambem
disponibiliza superficies relacionadas a informativos, tematica, sumulas,
enunciados e precedentes obrigatorios. A tecnologia JSF/PrimeFaces requer
fixture de postback e teste de estado para que a implementacao nao dependa de
indices ou ViewState instaveis.

## CNJ E Conteudo Curado

A [pagina oficial de jurisprudencia do CNJ]
(https://atos.cnj.jus.br/jurisprudencia) permite filtrar numero, ano, argumento
e intervalo de datas, apresentando tipo, numero, data, ementa e links para
documentos oficiais. O [Informativo oficial em PDF]
(https://atos.cnj.jus.br/files/original150034202607076a4d1492dc1d8.pdf) deixa
claro que o informativo resume julgados e que a conformidade deve ser conferida
no acordao publicado. Portanto este e um provider documental/curado, nao um
substituto de uma base geral de acordaos.

## Decisao Tecnica

1. Promover primeiro os candidatos `candidate_ready` que ja possuem resposta
   juridica observada: TJPR, TJRR e TJPE.
2. Implementar CNJ e TJCE Informativos como catalogos curados, preservando o
   link do documento oficial e a limitacao epistemica do resumo.
3. Manter TJCE SJURIS como `candidate_needs_har` ate que exista resposta de
   busca reproduzida com sessao publica limpa.
4. Para cada promocao, exigir fixture de sucesso, vazio, paginacao, erro e
   detalhe quando a fonte o oferecer, alem de ids estaveis e mapeamento dos
   campos canonicos.

## Limites Da Evidencia

Esta pesquisa nao afirma disponibilidade permanente. Portais judiciais podem
alterar frontend, WAF, limites e contratos sem aviso. O NanoJuris deve registrar
`searched_sources`, `skipped_sources`, erros e `SourceTrace`, mantendo a
diferenca entre rota observada, resposta juridica reproduzida e provider
executavel.

## Fechamento Documental Da Rodada

Depois do aprofundamento, os 22 candidatos do registry possuem dossie com
secoes explicitas de identidade, contrato, dados, estados, fixtures, MCP e
proximos passos. A auditoria gerada em `docs/provider-documentation-audit.md`
registra:

- 57 dossies no total: 34 implementados, 22 candidatos e 1 familia;
- 45 de 57 dossies com todas as secoes estruturais;
- paridade 57 de 57 entre dossie canonico e copia legada;
- 22 de 22 candidatos em `research_ready` documental.

`research_ready` nao significa provider implementado nem contrato live fechado.
Nos candidatos bloqueados, a documentacao completa registra filtros e escopo
institucional, mas conserva metodo, payload, paginacao, detalhe ou inteiro teor
como pendentes quando nao foram reproduzidos por HTTP limpo.

## Novas Superficies Confirmadas - 2026-08-12

O aprofundamento desta rodada nao criou registros duplicados. Ele consolidou
rotas adicionais nos dossies dos providers/familias que ja representam essas
fontes:

| Superficie | O que foi fechado | O que permanece pendente |
| --- | --- | --- |
| BNP/Pangea | catalogo, busca POST, sugestoes, decisoes vinculadas, operadores e filtros de orgao/especie/data | busca geral de acordaos e contrato de agregacoes |
| SJUR TSE/TRE | catalogos de classes, relatores, eleicoes e normas, com payload e amostras live | payload decisorio, paginacao, detalhe e inteiro teor; antirrobo observado |
| TRF5 | filtros de processo, relatoria, decisao, publicacao, texto, legislacao e tipos documentais | ordenacao/paginacao estavel, detalhe e estados de inteiro teor |
| STJ Dados Abertos | CKAN `package_search`, `package_show`, recursos, formatos, licenca e estados de sincronizacao | filtros juridicos remotos, que dependem de ingestao/indexacao local |

As referencias institucionais usadas na consolidacao sao a [pagina de
jurisprudencia eleitoral do TSE](https://www.tse.jus.br/jurisprudencia/jurisprudencia-da-justica-eleitoral),
o [Pangea/BNP](https://pangeabnp.pdpj.jus.br/), a [pesquisa de jurisprudencia
do TRF5](https://jurisprudencia.trf5.jus.br/jurisprudencia/pesquisa.wsp) e o
[catalogo de dados abertos do STJ](https://dadosabertos.web.stj.jus.br/dataset/?license_id=cc-by&res_format=JSON&tags=integras&tags=jurisprudencia).

### Regra De Desenvolvimento

Rotas de catalogo e metadados podem ser implementadas com fixtures e testes
offline. Rotas de resultados juridicos somente devem entrar no registry como
runtime quando houver resposta reproduzida, contrato de entrada/saida,
classificacao de acesso, pagina vazia, erro controlado, identidade estavel e
evidencia de detalhe ou inteiro teor. Isso evita transformar uma tela, um
bundle JavaScript ou um endpoint de catalogo em uma promessa de busca juridica
completa.
