# `tjce_cjsg`

## Identidade

- Fonte oficial: Consulta de Jurisprudencia do TJCE no e-SAJ.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `esaj_cjsg`.
- URL de consulta: `https://esaj.tjce.jus.br/cjsg/resultadoCompleta.do`.
- Status de acesso: `source_unavailable` nesta validacao local; contrato live pendente.
- Status no NanoJuris: provider implementado com contrato offline da familia CJSG.

O portal oficial documenta uma base progressiva de jurisprudencia com ementas,
acordaos e acesso ao inteiro teor. A pagina de consulta completa publica
campos de pesquisa livre, ementa, classe, assunto, orgao julgador, comarca,
relator, juiz prolator, numero de registro, numero de recurso e periodos de
julgamento/publicacao/registro.

## Evidencia publica

A pagina oficial foi localizada e aberta em 2026-08-11. Ela respondeu como
interface HTML de consulta e apresentou os seguintes grupos de filtros:

- pesquisa livre no inteiro teor;
- pesquisa na ementa;
- classe e assunto;
- orgao julgador, comarca e relator;
- numero de recurso e numero de registro;
- data de julgamento e data de publicacao;
- origem de segundo grau ou colegios recursais;
- tipo de publicacao: acordaos ou decisoes monocraticas;
- ordenacao por data de publicacao ou relevancia.

A documentacao oficial tambem afirma que a consulta permite acesso aos dados
do processo e a integra do documento de acordao.

## Rota e contrato de implementacao

```text
POST https://esaj.tjce.jus.br/cjsg/resultadoCompleta.do
GET  https://esaj.tjce.jus.br/cjsg/trocaDePagina.do?tipoDeDecisao=<tipo>&pagina=<n>
GET  https://esaj.tjce.jus.br/cjsg/getArquivo.do?cdAcordao=<id>&cdForo=<foro>
```

O provider usa o contrato comum da familia e-SAJ/CJSG: a primeira chamada
estabelece a sessao publica, paginas posteriores usam `trocaDePagina.do` e o
inteiro teor usa `getArquivo.do`. Os nomes e valores do formulario TJCE ainda
precisam de replay live especifico; por isso a implementacao offline nao e
evidencia de que o TJCE aceite exatamente o mesmo payload do TJAC/TJMS.

## Contrato pendente

Ainda nao foram confirmados por chamada reproduzivel no TJCE:

- nomes finais dos campos e valores de checkbox/radio;
- paginacao e ordenacao reais;
- rota de detalhe e inteiro teor;
- comportamento para resposta vazia e erros;
- eventual controle de frequencia ou desafio.

Nao inferir esses valores a partir de HTML indexado ou de exemplos de busca.
O proximo HAR deve ser gravado durante uma busca pequena, em navegador comum,
sem cookies exportados, login, captcha resolvido ou qualquer contorno de
protecao.

## Decisao de produto

O TJCE entrou no codigo como adaptador offline da familia e-SAJ/CJSG, com
parser, testes e classificacao de barreiras. Ele nao deve ser promovido para
validado live ou Gold enquanto o formulario, a pagina de resultados e o
inteiro teor nao forem reproduzidos no proprio host.

## Fixtures necessarias

- [x] Fixture de resultado sintetica dedicada ao TJCE para validar parser,
  identidade e trace (`tests/fixtures/tjce_cjsg_result.html`).
- [x] Testes offline de busca, pagina, documento, hash e bloqueio.
- [x] Fluxo HTTP inicial e pagina de resultados confirmados em smoke bounded de
  2026-09-06 (`docs/provider-discovery/cjsg-live-recheck-20260906.json`).
- [x] Fixture de resultado do TJCE com identidade, ementa e inteiro teor
  (`tests/fixtures/tjce_cjsg_result.html`).
- [x] Fixture de acesso controlado e teste de erro (`tests/test_tjce_cjsg.py`).
- [x] Fixture de detalhe/inteiro teor e hash (`tests/test_tjce_cjsg.py`).
- [x] Parser offline e teste de encoding antes do fetcher live.
- [x] Vazio tratado explicitamente pelo parser comum; o smoke não o confunde
  com bloqueio.

## MCP e agentes

O MCP e o Studio podem listar o TJCE como provider implementado, mas devem
expor o estado live como pendente/indisponivel e nao como resultado vazio. A
descricao deve separar busca no inteiro teor, ementa e documento carregado.

## Validacao live 2026-08-16

- GET da rota e-SAJ respondeu EOF TLS antes de entregar resposta neste ambiente.
- O acesso HTTP local voltou a encerrar a conexao antes do payload. Isso nao
  valida nem invalida o contrato do tribunal; apenas impede a promocao live.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Rechecagem pública (2026-09-13)

Uma consulta bounded por `divorcio` (`page_size=1`, `degree=second`) retornou
HTTP 200, um registro textual de segundo grau e total reportado de 2.996. O
inteiro teor do registro `tjce-cjsg-3845056-0` foi obtido publicamente por
`GET /getArquivo.do`: PDF válido, 33 páginas, 530.551 bytes e 73.244
caracteres extraídos. Nenhum CAPTCHA, credencial ou bypass foi utilizado.

Evidências redigidas: `docs/provider-discovery/tjce-cjsg-live-20260913.json` e
`docs/provider-discovery/tjce-cjsg-detail-live-20260913.json`.

O estado técnico passa a ser `live_validated` para busca e inteiro teor; a
federação continua condicionada aos gates e ao manifesto gerado.

## Proximos passos

1. Capturar HAR de uma consulta simples por termo, com apenas uma pagina.
2. Reproduzir a chamada com headers minimos e rate limit conservador.
3. Salvar fixtures sem dados pessoais desnecessarios ao teste.
4. Reaproveitar o parser da familia e-SAJ somente depois de comparar os
   seletores e os nomes de campo do TJCE.
5. Promover para `runtime_validated` apenas quando o resultado decisorio for
   reproduzido por HTTP limpo no host TJCE.
## Dados Retornados E Mapeamento

A pagina institucional sugere processo, classe, assunto, orgao julgador, comarca, relator, juiz prolator, registro, recurso, datas, tipo de publicacao, ementa e inteiro teor. Nenhum desses campos foi validado em resposta de busca nesta janela; portanto devem permanecer como campos esperados, nao como dados disponiveis. Quando houver fixture, preservar o HTML e o PDF/URL original.

## Estados De Dados

Sem replay da submissao, nao e possivel distinguir vazio, captcha, sessao expirada, limite ou erro de contrato. O parser futuro deve classificar cada estado pelo texto e status HTTP, nunca converter reset TLS em zero resultados.

### Alinhamento Juscraper (2026-09-01, ciclo 12)

O adapter agora implementa o fluxo reproduzivel POST de submissao, GET da
pagina 1 e GET da pagina solicitada em `trocaDePagina.do`, preservando a sessao.
Falhas TLS, captcha e WAF continuam bloqueios explicitos.

### Revalidação pública (2026-09-06)

O fluxo público foi revalidado com uma sessão bounded: HTTP 200, ementa textual
de segundo grau, total reportado de 107086 registros e detalhe público válido.
Evidência redigida: `docs/provider-discovery/cjsg-live-legitimate-recheck-20260906.json`.
