# `tjrr_juris`

## Identidade

- Fonte oficial: Jurisprudencia publica do TJRR.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `jsf_primefaces_jurisprudencia`.
- URL inicial: `https://jurisprudencia.tjrr.jus.br/index.xhtml`.
- Status de acesso: rota publica revalidada; GET, postback e paginacao observados.
- Status no NanoJuris: implementado, com parser offline e detalhe publico separado.

## Contrato HTTP

- Rotas observadas:
  - `GET /`
  - `GET /index.xhtml`
- Tecnologia observada: JSF/PrimeFaces.
- Parametros conhecidos: formulario publico com termo livre, pesquisa avancada,
  relator, numero SISCOM/PROJUDI, datas, ementa/indexacao e especie.
- Postback: reproduzido com `javax.faces.ViewState` obtido na mesma sessao.
- Limite remoto observado: `rows=10`; solicitações maiores são reduzidas pela
  própria fonte e a capacidade deve ser expressa por páginas sucessivas.
- `javax.faces.ViewState`: deve vir da propria sessao publica; nao pode ser
  reutilizado de navegador pessoal.

## Contrato de busca observado

Fluxo minimo:

```text
GET  /index.xhtml
POST /index.xhtml;jsessionid=<sessao-publica>
```

O formulario `menuinicial` envia, entre outros campos, o estado JSF e:

```text
menuinicial:j_idt28=dano moral
menuinicial:j_idt30=
```

O primeiro campo e o termo livre e `menuinicial:j_idt30` e o comando de
pesquisa. Os demais filtros publicos incluem numero SISCOM/PROJUDI, relator,
datas, tipo de procedimento e orgao. `javax.faces.ViewState` e dinamico e nao
pode ser fixado em codigo ou fixture.

Uma sessao limpa com `dano moral` retornou HTTP 200 e HTML com resultados
reais, numero de processo, ementa/decisao, relator, orgao e especie. A resposta
tambem exibiu paginacao e links de navegacao. Uma repeticao imediata posterior
sofreu timeout, portanto a disponibilidade deve ser considerada instavel e
testada com baixa frequencia.

## Dados retornados

- Campos esperados:
  - ementa;
  - acordao;
  - relator;
  - orgao;
  - numero;
  - datas;
  - especie;
  - links tematicos.
- Campos canonicos esperados: `CanonicalDecision`.
- Inteiro teor: rota publica por id observado, com texto HTML quando disponivel.

## Comportamento observado

- GET inicial: HTTP 200 com formulario rico.
- Busca com resultado: reproduzida em uma sessao limpa com `dano moral`.
- Controle de acesso/captcha: nao observado no GET inicial.
- Risco tecnico: postback JSF pode ser sensivel a campos ocultos e estado da
  sessao; a disponibilidade tambem apresentou timeout em uma repeticao.

## Fixtures

- [x] HTML inicial com `ViewState`.
- [x] fixture HTML de busca simples com `ViewState` normalizado.
- [x] fixture HTML de resultado com ementa/acordao.
- [x] parser offline de busca, pagina e detalhe.
- [ ] Busca vazia e erro de postback/estado expirado live.

## MCP e agentes

- Quando usar: para jurisprudencia publica do TJRR, com baixa frequencia.
- Quando pular: quando houver timeout, estado JSF expirado ou resultado sem
  sinais juridicos.
- Mensagem segura: "A fonte TJRR e publica, mas sua disponibilidade e o
  contrato JSF devem ser verificados na sessao atual."
- Riscos: confundir estado de sessao JSF com token reaproveitavel.

## Validacao live 2026-08-11

- GET e POST JSF com `dano moral` responderam HTTP 200, com ementa, processo, relator, orgao, resultado e paginacao.
- O `javax.faces.ViewState` e o `jsessionid` devem ser obtidos por sessao e nunca fixados em fixture de sucesso.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Implementacao Runtime

`TjrrJurisProvider` abre uma sessao publica nova, extrai o formulario e o
ViewState atuais, envia a busca e usa o postback AJAX do componente PrimeFaces
para paginas posteriores. O parser usa os titulos semanticos de cada bloco de
documento, preserva URLs de processo, impressao e inteiro teor em `raw` e
marca `SearchPage.is_complete` somente quando o `rowCount` da fonte sustenta a
janela retornada.

## Proximos passos

- [x] Reproduzir postback com `requests` em sessao publica nova.
- [x] Gravar fixtures reduzidas de formulario, resultado e detalhe.
- [x] Criar parser offline e provider runtime.
- [x] Documentar parametros obrigatorios e limites do contrato.
- [ ] Ampliar live opt-in para vazio, estado expirado e detalhe em baixa frequencia.

## Aprofundamento Do Contrato - 2026-08-12

### Filtros Publicos Confirmados

| Campo | Forma observada | Observacao |
| --- | --- | --- |
| termo livre | texto | aceita operadores `E`, `OU`, `NAO` e frase entre aspas |
| numero SISCOM/PROJUDI | texto | interface indica 13 digitos SISCOM ou 20 PROJUDI |
| relator | selecao | lista separada por segundo grau, turma recursal e aposentados/ex-convocados |
| data inicial/final | data | formato de envio ainda depende do formulario |
| procedimento | select | valores devem ser lidos do HTML |
| orgao julgador | selecao | inclui turmas, camaras, pleno, presidencia e conselho |
| ementa/indexacao | texto | campo independente do termo livre |
| especie de recurso | select | catalogo e valores precisam de fixture |

O portal tambem oferece links separados para Informativos, Jurisprudencia
Tematica, Sumulas, Enunciados, Legislacao e Precedentes Obrigatorios. Eles
devem ser tratados como superficies documentais distintas, nao como resultados
da busca geral.

### Transporte E Estado

O fluxo depende de `GET /index.xhtml`, cookies de sessao publica e um
`javax.faces.ViewState` obtido na mesma sessao, seguido de POST de formulario.
Os nomes `menuinicial:j_idt28` e `menuinicial:j_idt30` foram observados para o
termo e comando em uma versao do portal, mas sao ids de apresentacao e podem
mudar. O parser deve localizar labels/names atuais na fixture, nao fixar apenas
indices JSF.

O contrato de pagina foi testado novamente em 2026-08-16. A pagina 1 publica
retornou dez itens, mas a tentativa de pagina 2 devolveu novamente o marcador
de pagina 1. O provider levanta `ParserContractChangedError` para impedir
duplicacao silenciosa. Isso e uma alteracao/limitacao observada na fonte, nao
um resultado vazio. HTML 200 sem sinais de resultado e HTML de estado expirado
continuam sem poder ser interpretados como vazio.

### MCP E Gate De Promocao

O MCP deve informar a data da sessao, filtros efetivos, pagina e se o estado
JSF foi renovado. Deve pular a fonte em timeout, ViewState expirado ou markup
sem sinais juridicos. Exigir fixtures de formulario, sucesso, vazio, erro de
estado, pagina seguinte e detalhe antes do provider runtime.

## Revalidacao live - 2026-08-14

Uma sessao publica nova foi revalidada sem cookies pessoais ou autenticacao:

- `GET /index.xhtml` respondeu HTTP 200 com formulario `menuinicial` e
  `javax.faces.ViewState` dinamico;
- o postback com termo livre `dano moral`, ViewState e cookie da mesma sessao
  respondeu HTTP 200;
- a resposta exibiu o painel PrimeFaces de resultados, paginacao e links para
  impressao e inteiro teor;
- nao foram observados sinais de captcha, login ou estado expirado nessa
  rodada.

Esta evidencia confirma a disponibilidade da rota, mas nao fecha o contrato do
parser. A resposta nao foi versionada no repositorio para evitar armazenar
dados pessoais e markup de apresentacao. O proximo gate continua sendo uma
fixture reduzida e revisada com campos juridicos, vazio, erro de ViewState,
pagina seguinte e detalhe.

## Validacao live de capacidade - 2026-08-16

- Pagina 1: 10 resultados, 10 identificadores unicos, 10 com data, total
  remoto observado de 13.929.
- Pagina 2: a fonte retornou marcador de pagina 1; o provider recusou a pagina
  como `ParserContractChangedError` em vez de repetir registros.
- Estado: `source_pagination_not_validated`.
- Limite: a busca segue utilizavel para a primeira pagina, mas nao deve ser
  tratada como coleta paginada completa ate a fonte honrar o evento PrimeFaces.
- Em 2026-08-16, sessões limpas também reportaram `rows=10` para solicitações
  de 25, 50 e 100. A página 2 devolveu o marcador da página 1; o provider
  mantém `ParserContractChangedError` e não mascara a duplicação.

Evidencia estruturada: `docs/validation/runs/20260816T084500Z-tjpr-tjrr-capacity-20260816.json`.
