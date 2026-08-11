# State Court Route Mapping - 2026-08-07

Rodada focada nos tribunais estaduais que ainda estavam pouco mapeados:
TJES, TJMT, TJPA, TJPB, TJPE, TJPI, TJRO, TJRR e TJSE.

O objetivo foi localizar candidatos oficiais para jurisprudencia publica, testar
rotas com sessao HTTP limpa e separar entradas fortes, contratos parciais e
fontes que ainda nao devem virar provider.

## Resumo executivo

| Tribunal | Melhor rota encontrada | Resultado do probe limpo | Decisao |
| --- | --- | --- | --- |
| TJES | `https://sistemas.tjes.jus.br/portaltj/Pesquisa.aspx` | timeout em 45s; rota antiga `aplicativos.tjes.../det_jurisp.cfm` retornou HTTP 404 | manter como inconclusivo; repetir com janela maior e navegador limpo |
| TJMT | `https://jurisprudencia.tjmt.jus.br/` | HTTP 200, SPA publica; bundle revela API `https://hellsgate-preview.tjmt.jus.br/jurisprudencia` e rotas `/api/consulta`, `/api/termo`, `/VisualizaRelatorio/...`; GET direto sem header retornou 401 | candidato forte, mas depende de contrato de payload/header publico antes de provider |
| TJPA | `https://jurisprudencia.tjpa.jus.br/` | HTTP 200, portal publico; `POST /bff/api/decisoes/buscar`, catalogos e recentes retornaram JSON em sessao limpa | `candidate_ready`; falta fixture, parser e detalhe |
| TJPB | `https://pje-jurisprudencia.tjpb.jus.br/` | HTTP 200 com formulario PJe, campos juridicos e paginacao; em outro cliente PowerShell houve Cloudflare/challenge | candidato forte com risco WAF; fixture deve confirmar resultado real |
| TJPE | `https://portal.tjpe.jus.br/web/jurisprudencia/tjpe-e-turmas-recursais` | HTTP 200, pagina institucional publica apontando Consulta Jurisprudencia Web | candidato documental/entrada; falta endpoint de resultado |
| TJPE | `https://portal.tjpe.jus.br/servicos/consulta/sumulas` | HTTP 200, sumulas e PDFs publicos | bom candidato de precedentes/sumulas, nao busca geral de acordaos |
| TJPE | `https://portal.tjpe.jus.br/web/transparencia/decis%C3%B5es` | HTTP 200, pagina de decisoes com rotas DJEN/DJE/PJe/Consulta Jurisprudencia Web | rota de orientacao/documental, nao provider decisorio |
| TJPI | `https://jurisprudencia.tjpi.jus.br/jurisprudences/search?q=dano%20moral` | HTTP 200, HTML com resultados reais, CNJ, acordaos, decisoes, ementa, relator, orgao e paginacao | promover como candidato P0/P1 para fixture e parser HTML |
| TJRO | `https://liame.tjro.jus.br/` | HTTP 200, LIAME/precedentes publico; probe marcou `access_denied` por texto de UI, sem decisoes retornadas | candidato de precedentes, nao provider de acordaos ainda |
| TJRR | `GET` + `POST https://jurisprudencia.tjrr.jus.br/index.xhtml` com ViewState da sessao publica | HTTP 200, JSF/PrimeFaces com resultados reais, processo, ementa/acordao, relator e orgao; repeticao posterior sofreu timeout | `candidate_ready`; fixture e parser JSF pendentes |
| TJSE | `https://www.tjse.jus.br/portal/consultas/jurisprudencia/judicial` | HTTP 200, pagina publica especifica de jurisprudencia judicial | candidato documental/entrada; falta reproduzir busca/resultado |

## Ranking para a proxima rodada tecnica

1. **TJPI/JusPI**: melhor alvo imediato. A rota de busca ja retornou resultados
   reais, volume, paginacao e campos canonicos.
2. **TJRR/Juris JSF**: postback simples ja foi reproduzido; precisa salvar
   fixture, mapear paginacao e repetir com baixa frequencia.
3. **TJMT/Jurisprudencia API Hellsgate**: bundle expoe rotas muito claras, mas
   a API exige header/chave publica do frontend. Deve ser tratado como contrato
   a aprofundar, sem bypass.
4. **TJPA/BFF decisoes**: frontend moderno e busca textual JSON reproduzida;
   falta fixture, filtros de classe/assunto e contrato funcional de detalhe.
5. **TJPB/PJe Jurisprudencia**: pagina rica, mas comportamento WAF variou por
   cliente. Exige cautela antes de prometer provider live.
6. **TJPE/sumulas e orientacao de decisoes**: bom para catalogo/documentos,
   fraco para busca decisoria enquanto o endpoint "Consulta Jurisprudencia Web"
   nao estiver reproduzido.
7. **TJSE/judicial**: entrada oficial boa, mas ainda sem rota de resultados.
8. **TJRO/LIAME**: util para precedentes/temas, nao substitui jurisprudencia de
   acordaos.
9. **TJES**: manter inconclusivo; ha sinais externos de portal oficial, mas o
   ambiente atual nao entregou resposta limpa.

## Contratos tecnicos observados

### TJPI/JusPI

Entrada:

```text
GET https://jurisprudencia.tjpi.jus.br/
GET https://jurisprudencia.tjpi.jus.br/jurisprudences/search?q=<termo>
```

Probe validado:

```text
GET /jurisprudences/search?q=dano%20moral
```

Sinais:

- HTTP 200;
- HTML server-side com resultados;
- texto "Exibindo ... de um total de ... jurisprudencia(s)";
- numero CNJ;
- tipos `Acordao`, `Decisao Terminativa` e `Sumula`;
- publicacao, relator, orgao julgador, ementa e paginacao.

Proximo passo: salvar fixture publica representativa e criar parser offline.

### TJRR/Juris

Entrada:

```text
GET https://jurisprudencia.tjrr.jus.br/
GET https://jurisprudencia.tjrr.jus.br/index.xhtml
```

Sinais:

- HTTP 200;
- JSF/PrimeFaces;
- formulario publico com termo livre e pesquisa avancada;
- campos de relator, numero SISCOM/PROJUDI, datas, ementa/indexacao e especie;
- links publicos para informativo, jurisprudencia tematica, sumulas,
  enunciados, legislacao e precedentes obrigatorios.

Proximo passo: salvar fixture sanitizada de uma busca simples, mapear
paginacao e testar novamente com baixa frequencia. O postback ja foi
reproduzido com `javax.faces.ViewState` publico da propria sessao limpa.

### TJMT/Jurisprudencia

Entrada:

```text
GET https://jurisprudencia.tjmt.jus.br/
```

Bundle publico observado:

```text
GET /main.4fbae9a9bb684a741e57.bundle.js
```

Rotas inferidas:

```text
https://hellsgate-preview.tjmt.jus.br/jurisprudencia/api/consulta/<tipoConsulta>
https://hellsgate-preview.tjmt.jus.br/jurisprudencia/api/termo/<termo>
https://hellsgate-preview.tjmt.jus.br/jurisprudencia/api/consulta/relator?Quantidade=1000
https://hellsgate-preview.tjmt.jus.br/jurisprudencia/api/consulta/orgao-julgador?Quantidade=100
https://hellsgate-preview.tjmt.jus.br/jurisprudencia/api/consulta/classe?Quantidade=100
https://hellsgate-preview.tjmt.jus.br/jurisprudencia/VisualizaRelatorio/RetornaDocumentoAcordao
```

Probe direto em `/api/consulta/1` retornou HTTP 401 `No API key found in
request`. O bundle inclui logica de header/token publico. A proxima rodada deve
confirmar se esse header faz parte do contrato publico do frontend e quais
parametros de filtro sao necessarios.

### TJPA/Jurisprudencia

Entrada:

```text
GET https://jurisprudencia.tjpa.jus.br/
```

Bundle publico observado:

```text
GET /main-6BATNNRR.js
```

Rotas inferidas:

```text
apiBaseUrl = /bff
GET/POST /bff/api/decisoes
GET /bff/api/pje/classes
GET /bff/api/pje/assuntos
GET /bff/api/siglas
GET /bff/api/temas-acordao
```

Rotas de consulta reproduzidas:

```text
GET /bff/api/decisoes/filtros
GET /bff/api/decisoes/recentes
POST /bff/api/decisoes/buscar
POST /bff/api/decisoes/pesquisar-por-classe-assunto
```

`POST /bff/api/decisoes/buscar` com consulta textual e valores exatos de
origem/tipo obtidos de `/filtros` retornou HTTP 200 JSON com resultados,
facetas, metadados decisorios e limite tecnico de 10.000. O `GET`
`/bff/api/decisoes` continua retornando HTTP 404 porque nao e a chamada de
busca. As rotas de detalhe por id e processo foram testadas com identificadores
da propria resposta e retornaram HTTP 404; ficam pendentes de contrato correto.

### TJPB/PJe Jurisprudencia

Entrada:

```text
GET https://pje-jurisprudencia.tjpb.jus.br/
```

Sinais:

- HTTP 200 no probe `requests` com User-Agent NanoJuris;
- formulario publico "Banco de Jurisprudencia - PJe";
- campos de ementa, inteiro teor, numero do processo, classe, orgao julgador,
  relator, data e origem de documento;
- UI indica resultado, paginacao e visualizacao.

Risco: `Invoke-WebRequest`/PowerShell recebeu Cloudflare managed challenge na
mesma URL. O provider so deve avancar se uma fixture de resultado real for
obtida por fluxo publico reproduzivel sem desafio.

### TJPE

Entradas:

```text
GET https://portal.tjpe.jus.br/web/jurisprudencia/tjpe-e-turmas-recursais
GET https://portal.tjpe.jus.br/servicos/consulta/sumulas
GET https://portal.tjpe.jus.br/web/transparencia/decis%C3%B5es
```

Sinais:

- paginas institucionais publicas;
- sumulas e PDFs publicos;
- pagina de transparencia orienta o acesso via DJEN, DJE, PJe e Consulta
  Jurisprudencia Web.

Decisao: promover sumulas/informativos como catalogo documental; nao implementar
busca geral de decisoes ate descobrir a rota tecnica da Consulta Jurisprudencia
Web.

### TJSE

Entrada:

```text
GET https://www.tjse.jus.br/portal/consultas/jurisprudencia/judicial
```

Sinais:

- HTTP 200;
- pagina oficial de jurisprudencia judicial;
- portal lista tambem jurisprudencia administrativa, precedentes, IRDR, IAC,
  diario e consulta de publicacoes.

Decisao: candidato documental/entrada. Falta reproduzir a rota de resultado da
pesquisa judicial.

### TJRO

Entrada:

```text
GET https://liame.tjro.jus.br/
```

Sinais:

- HTTP 200;
- LIAME para precedentes, temas, especies, situacao e processo paradigma;
- informacoes de sincronizacao com BNP/STF/TPU.

Decisao: bom candidato de precedentes/catalogo, nao de acordaos. O probe atual
marcou `access_denied` por texto bruto de UI; antes de qualquer provider, criar
um diagnostico mais especifico para nao confundir "acesso" informativo com
bloqueio real.

### TJES

Entradas testadas:

```text
GET https://sistemas.tjes.jus.br/portaltj/Pesquisa.aspx
GET https://aplicativos.tjes.jus.br/sistemaspublicos/consulta_jurisprudencia/det_jurisp.cfm?... 
```

Resultado:

- `Pesquisa.aspx`: timeout em 45s no ambiente atual;
- `det_jurisp.cfm`: HTTP 404, apesar de haver resultados antigos indexados por
  buscadores.

Decisao: inconclusivo. Repetir em outra janela, com timeout maior e pesquisa
manual antes de classificar.

## Proximos probes recomendados

1. TJPI: criar fixture com `q=dano moral`, `q=idpj` e pagina 2.
2. TJRR: gravar HAR de busca simples e reproduzir JSF postback sem cookies
   privados.
3. TJMT: testar endpoints de metadados e busca usando apenas o header publico
   que o frontend envia automaticamente.
4. TJPA: gravar HAR e identificar metodo/payload de `/bff/api/decisoes`.
5. TJPB: testar busca real e verificar se Cloudflare aparece em sessao limpa
   repetida.
6. TJPE: localizar o destino exato do link "Consulta Jurisprudencia Web".
7. TJSE: localizar formulario/endpoint final da pagina judicial.
8. TJRO: separar LIAME como precedentes e buscar rota oficial de acordaos, se
   existir.
9. TJES: repetir `Pesquisa.aspx` com janela maior e confirmar se o portal atual
   substituiu o ColdFusion antigo.
