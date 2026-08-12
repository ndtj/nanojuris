# `tjce_cjsg`

## Identidade

- Fonte oficial: Consulta de Jurisprudencia do TJCE no e-SAJ.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `esaj_cjsg`.
- URL de consulta: `https://esaj.tjce.jus.br/cjsg/resultadoCompleta.do`.
- Status de acesso: `candidate_needs_har`.
- Status no NanoJuris: candidato, sem provider implementado.

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

## Rota observada

```text
GET https://esaj.tjce.jus.br/cjsg/resultadoCompleta.do
```

O acesso HTTP direto em sessao limpa, com `requests` e sem proxy de ambiente,
sofreu `ConnectionResetError`/reset TLS antes de receber o HTML. Esse resultado
nao prova indisponibilidade da fonte: a pagina oficial continua acessivel por
outras superficies, mas ainda falta capturar um HAR limpo do fluxo de busca.

## Contrato pendente

Ainda nao foram confirmados por chamada reproduzivel:

- metodo final de submissao;
- `action` do formulario;
- nomes dos campos e valores de checkbox/radio;
- paginacao e ordenacao reais;
- rota de detalhe e inteiro teor;
- comportamento para resposta vazia e erros;
- eventual controle de frequencia ou desafio.

Nao inferir esses valores a partir de HTML indexado ou de exemplos de busca.
O proximo HAR deve ser gravado durante uma busca pequena, em navegador comum,
sem cookies exportados, login, captcha resolvido ou qualquer contorno de
protecao.

## Decisao de produto

O TJCE e um candidato de alto valor para a familia e-SAJ/CJSG, mas nao deve
entrar no codigo enquanto o contrato de submissao nao for reproduzido e houver
fixture real de resultado. A documentacao oficial e evidencia de existencia e
escopo da fonte; nao substitui o teste do endpoint automatizavel.

## Fixtures necessarias

- [ ] HTML inicial da consulta completa.
- [ ] HAR de busca textual pequena.
- [ ] Fixture de resultado com processo, classe, orgao, data, relator e ementa.
- [ ] Fixture de vazio.
- [ ] Fixture de erro ou limite de acesso, se observado.
- [ ] Fixture de detalhe/inteiro teor, se publico.
- [ ] Parser offline e teste de encoding antes do fetcher live.

## MCP e agentes

O MCP deve pular o TJCE enquanto o contrato permanecer pendente e informar a
indisponibilidade automatica de forma explicita. Depois da validacao, a
descricao da ferramenta deve separar busca por ementa de busca no inteiro teor,
preservar o tipo de publicacao e expor a URL oficial de origem.

## Validacao live 2026-08-11

- GET da rota e-SAJ respondeu EOF TLS antes de entregar resposta neste ambiente.
- A rota oficial permanece documentada, mas nao e considerada contrato reproduzivel sem nova evidencia de transporte ou HAR publico.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Proximos passos

1. Capturar HAR de uma consulta simples por termo, com apenas uma pagina.
2. Reproduzir a chamada com headers minimos e rate limit conservador.
3. Salvar fixtures sem dados pessoais desnecessarios ao teste.
4. Reaproveitar o parser da familia e-SAJ somente depois de comparar os
   seletores e os nomes de campo do TJCE.
5. Promover para `candidate_ready` apenas quando o resultado decisorio for
   reproduzido por HTTP limpo.
## Dados Retornados E Mapeamento

A pagina institucional sugere processo, classe, assunto, orgao julgador, comarca, relator, juiz prolator, registro, recurso, datas, tipo de publicacao, ementa e inteiro teor. Nenhum desses campos foi validado em resposta de busca nesta janela; portanto devem permanecer como campos esperados, nao como dados disponiveis. Quando houver fixture, preservar o HTML e o PDF/URL original.

## Estados De Dados

Sem replay da submissao, nao e possivel distinguir vazio, captcha, sessao expirada, limite ou erro de contrato. O parser futuro deve classificar cada estado pelo texto e status HTTP, nunca converter reset TLS em zero resultados.
