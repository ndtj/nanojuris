# justica_eleitoral_sjur

## Identidade
- Fonte oficial: SJUR/TSE e agregador SJUR/TREs.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `justica_eleitoral_sjur`.
- URL inicial TSE: `https://jurisprudencia.tse.jus.br/`.
- URL inicial TREs: `https://jurisprudencia-tres.tse.jus.br/`.
- Status de acesso: paginas e metadados publicos validados; busca decisoria
  ainda nao promovida por falta de resposta limpa reproduzivel no probe de
  2026-08-11.

## Contrato HTTP
- Host API observado: `https://sjur-pesquisa-api.tse.jus.br/{tribunal}/sjur-pesquisa-backend/rest/public/pesquisa`.
- Valores observados de `{tribunal}`:
  - `tse`;
  - `tres`.
- Rotas auxiliares observadas:
  - `POST /classes`
  - `POST /relatorias`
  - `POST /eleicoes`
  - `POST /normas`
  - `POST /download/`
  - `POST /pesquisaTokenValidado`
  - `POST /livre`
  - `POST /simples`
  - `POST /rede`
- A nova SPA 4.0 tambem publica no bundle oficial o backend
  `https://sjur-pesquisa-api.tse.jus.br/{tribunal}/sjur-pesquisa-backend/rest/`.
- Rotas de metadados reproduzidas em 2026-08-11:
  - `POST /public/pesquisa/classes`
  - `POST /public/pesquisa/relatorias`
  - `POST /public/pesquisa/eleicoes`
  - `POST /public/pesquisa/normas`
- Payload de metadados TSE:

```json
["TSE"]
```

- Payload de metadados TRE-SP:

```json
["TRE-SP"]
```

## Dados retornados
- `POST /classes`: classes processuais eleitorais, como `RESPE`, `AI`, `REspEl` e `AREspEl`.
- `POST /relatorias`: lista de relatores.
- `POST /eleicoes`: anos eleitorais.
- `POST /normas`: objetos normativos com sigla, numero, ano e tipo.
- Campos canonicos possiveis: catalogo auxiliar de filtros, nao `CanonicalDecision` nesta fase.
- Busca de decisoes: pendente; `POST /public/pesquisa` retornou mensagem de falha antirrobo com lista vazia.

## Comportamento observado
- Metadados TSE: HTTP 200, JSON publico.
- Metadados TRE-SP: HTTP 200, JSON publico.
- As quatro rotas de metadados acima retornaram HTTP 200 em sessao limpa com
  JSON real.
- Busca principal com payload minimalista: HTTP 200, JSON com `mensagem` de falha antirrobo, `content=[]`, `totalRegistros=0`.
- As novas paginas beta `https://jurisprudencia.tse.jus.br/` e
  `https://jurisprudencia-tres.tse.jus.br/` responderam HTTP 200 com shell SPA
  publico. A pagina institucional aponta para essas ferramentas e informa que
  a versao beta concentra inicialmente a base do TSE.
- A rota direta `https://www.tse.jus.br/jurisprudencia/decisoes/` foi rejeitada
  pelo portal no probe limpo, sem conteudo decisorio.
- O bundle referencia `/livre`, `/simples`, `/pesquisaTokenValidado`,
  `/download/` e `/rede`, mas os testes sem o fluxo normal da aplicacao nao
  fecharam um contrato de resultados reproduzivel. Nao tratar isso como bypass.

## Decisao
- Promover apenas como contrato parcial P1.
- Nao implementar provider de decisoes enquanto a rota exigir antirrobo, token ou validacao humana.
- Usar o contrato atual para descoberta de filtros eleitorais e para orientar pesquisa futura com HAR/DevTools.

## MCP e agentes
- Quando usar: explicar quais filtros/classes eleitorais a fonte declara publicamente.
- Quando pular: perguntas que exigem acordaos, ementas ou inteiro teor do TSE/TREs.
- Mensagem segura para o usuario: "A API publica expõe metadados eleitorais, mas a busca de decisoes retornou controle antirrobo em sessao limpa."

## Validacao live 2026-08-11

- `POST /tse/sjur-pesquisa-backend/rest/public/pesquisa/classes` com `["TSE"]` respondeu HTTP 200 JSON com 136 classes.
- A busca decisoria continua retornando controle antirrobo; catalogo valido nao equivale a provider de decisoes.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/lucmolero/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Proximos passos
- [ ] Coletar HAR revisado sem cookies, tokens ou dados locais de navegador de uma busca manual autorizada para entender payload exato.
- [ ] Verificar se existe endpoint documentado de busca sem token.
- [ ] Criar fixture de `classes` e `relatorias`.
- [ ] Adicionar testes de diagnostico para `anti_robot`.
- [ ] Capturar HAR limpo da nova SPA beta e confirmar endpoint de resultados,
  payload, paginacao e detalhe sem token privado.
