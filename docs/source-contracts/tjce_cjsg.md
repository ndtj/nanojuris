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

- [x] Fixture de resultado da familia para validar parser, identidade e trace.
- [x] Testes offline de busca, pagina, documento, hash e bloqueio.
- [ ] HTML inicial da consulta completa do TJCE.
- [ ] HAR de busca textual pequena do TJCE.
- [ ] Fixture de resultado do TJCE com processo, classe, orgao, data, relator e ementa.
- [ ] Fixture de vazio.
- [ ] Fixture de erro ou limite de acesso, se observado.
- [ ] Fixture de detalhe/inteiro teor, se publico.
- [ ] Parser offline e teste de encoding antes do fetcher live.

## MCP e agentes

O MCP e o Studio podem listar o TJCE como provider implementado, mas devem
expor o estado live como pendente/indisponivel e nao como resultado vazio. A
descricao deve separar busca no inteiro teor, ementa e documento carregado.

## Validacao live 2026-08-16

- GET da rota e-SAJ respondeu EOF TLS antes de entregar resposta neste ambiente.
- O acesso HTTP local voltou a encerrar a conexao antes do payload. Isso nao
  valida nem invalida o contrato do tribunal; apenas impede a promocao live.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

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
