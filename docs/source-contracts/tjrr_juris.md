# `tjrr_juris`

## Identidade

- Fonte oficial: Jurisprudencia publica do TJRR.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `jsf_primefaces_jurisprudencia`.
- URL inicial: `https://jurisprudencia.tjrr.jus.br/index.xhtml`.
- Status de acesso: candidato pronto; GET e postback publico reproduzidos uma vez.
- Status no NanoJuris: candidato, ainda sem provider implementado.

## Contrato HTTP

- Rotas observadas:
  - `GET /`
  - `GET /index.xhtml`
- Tecnologia observada: JSF/PrimeFaces.
- Parametros conhecidos: formulario publico com termo livre, pesquisa avancada,
  relator, numero SISCOM/PROJUDI, datas, ementa/indexacao e especie.
- Postback: reproduzido com `javax.faces.ViewState` obtido na mesma sessao.
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
- Inteiro teor: pendente.

## Comportamento observado

- GET inicial: HTTP 200 com formulario rico.
- Busca com resultado: reproduzida em uma sessao limpa com `dano moral`.
- Controle de acesso/captcha: nao observado no GET inicial.
- Risco tecnico: postback JSF pode ser sensivel a campos ocultos e estado da
  sessao; a disponibilidade tambem apresentou timeout em uma repeticao.

## Fixtures

- [ ] HTML inicial com `ViewState`.
- [ ] fixture HTML de busca simples com `ViewState` normalizado.
- [ ] fixture HTML de resultado com ementa/acordao.
- [ ] Busca vazia.
- [ ] Erro de postback/estado expirado.

## MCP e agentes

- Quando usar: depois de provider e parser offline, com baixa frequencia.
- Quando pular: quando houver timeout, estado JSF expirado ou resultado sem
  sinais juridicos.
- Mensagem segura: "A fonte TJRR e publica e o postback foi reproduzido, mas
  a disponibilidade pode oscilar e o contrato ainda aguarda fixture."
- Riscos: confundir estado de sessao JSF com token reaproveitavel.

## Validacao live 2026-08-11

- GET e POST JSF com `dano moral` responderam HTTP 200, com ementa, processo, relator, orgao, resultado e paginacao.
- O `javax.faces.ViewState` e o `jsessionid` devem ser obtidos por sessao e nunca fixados em fixture de sucesso.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/lucmolero/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Proximos passos

- [x] Reproduzir postback com `requests` em sessao publica nova.
- [ ] Gravar fixture sanitizada de busca simples em navegador ou requests limpo.
- [ ] Criar parser offline.
- [ ] Documentar parametros obrigatorios.

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

Paginacao, total, links de detalhe e rota de inteiro teor ainda nao possuem
contrato fechado. HTML 200 sem sinais de resultado e HTML de estado expirado
nao devem ser interpretados como vazio sem verificar a mensagem da fonte.

### MCP E Gate De Promocao

O MCP deve informar a data da sessao, filtros efetivos, pagina e se o estado
JSF foi renovado. Deve pular a fonte em timeout, ViewState expirado ou markup
sem sinais juridicos. Exigir fixtures de formulario, sucesso, vazio, erro de
estado, pagina seguinte e detalhe antes do provider runtime.
