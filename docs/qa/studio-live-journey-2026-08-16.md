# Auditoria live do NanoJuris Studio - 2026-08-16

## Objetivo

Executar buscas reais pelo Studio com perfis de uso proximos dos fluxos de um
advogado, pesquisador e jurimetrista, observando:

- amplitude efetiva da pesquisa federada;
- diferenca entre resultado, vazio, falha e coleta parcial;
- qualidade dos campos exibidos;
- disponibilidade de ementa, texto integral e documento;
- comportamento visual desktop/mobile;
- ausencia de erros silenciosos ou falso resultado vazio.

Esta rodada foi executada contra o Studio real em `127.0.0.1:8766`, com
Chromium, sem bypass de CAPTCHA, WAF, login, TLS ou qualquer controle de
acesso. O processo usou `NANOJURIS_TRUST_ENV=0` no servidor para evitar que um
proxy ambiental alterasse a observacao das fontes.

## Estado observado

- 37 fontes carregadas no catalogo runtime;
- 34 recomendadas para jurisprudencia;
- 7 selecionadas no preset estavel;
- nenhuma mensagem JavaScript de erro nas cinco jornadas;
- nenhum overflow horizontal em desktop ou mobile;
- cada busca manteve `collection_complete=false` quando consultou somente uma
  janela de resultados;
- falhas externas permaneceram visiveis e nao foram convertidas em vazio.

## Prints

### Jornadas de pesquisa

- [Responsabilidade civil - desktop](../../artifacts/studio/live-responsabilidade-civil-desktop.png)
- [Responsabilidade civil - mobile](../../artifacts/studio/live-responsabilidade-civil-mobile.png)
- [Infanticidio - desktop](../../artifacts/studio/live-infanticidio-desktop.png)
- [Improbidade administrativa - desktop](../../artifacts/studio/live-improbidade-administrativa-desktop.png)
- [Acesso controlado e contrato - desktop](../../artifacts/studio/live-acesso-controlado-e-contrato-desktop.png)

### Artefatos estruturados

- [Relatorio das jornadas do Studio](../../artifacts/studio/qa-studio-live-2026-08-16.json)
- [Documentos - infanticidio](../../artifacts/studio/qa-jurisprudence-documents-2026-08-16.json)
- [Documentos - responsabilidade civil](../../artifacts/studio/qa-jurisprudence-documents-responsabilidade-civil-2026-08-16.json)

## Jornadas reais

| Jornada | Fontes | Retornados na pagina | Fontes com resultados | Estado observado |
| --- | --- | ---: | ---: | --- |
| `responsabilidade civil` | TJDFT, TST | 5 | 2 | 2 janelas parciais, sem falha |
| `infanticidio` | STJ, TJRS, TJBA, TRF5 | 5 | 2 | 2 parciais, 1 vazio, 1 parcial sem itens |
| `improbidade administrativa` | TJPA, TJPB, TJPR, TJPI | 5 | 3 | 3 parciais, 1 falha de fonte |
| `responsabilidade civil` | STF, CJF, TJSP/CJSG, TJSC/eproc | 0 | 0 | 4 falhas classificadas, nenhuma tratada como vazio |

### Leitura dos resultados

Na primeira jornada, TJDFT informou 131.875 registros e TST 841.970. A tela
exibiu 5 registros da pagina federada e informou 10 disponiveis na janela
consultada, com 2 fontes parciais. O indicador `fontes com resultados` foi
corrigido durante esta auditoria para contar fontes que retornaram itens mesmo
quando a janela e parcial.

Na jornada de infanticidio, o STJ/SCON retornou acordaos com ementas e links de
inteiro teor; o TJRS retornou ementas; o TJBA informou total zero para esse
termo; e o TRF5 respondeu com uma janela HTML ainda sem contrato de paginacao
promovido. O Studio mostrou esses estados separadamente.

Na jornada de improbidade, o TJPA trouxe texto extenso no resultado canonico,
enquanto TJPR e TJPI trouxeram metadados/ementas. O TJPB falhou por
indisponibilidade na rodada, sem ser apresentado como fonte vazia.

Na jornada de controle, foram observados:

- STF: erro de verificacao SSL;
- CJF/TRF1: HTML com controle de acesso;
- TJSP/CJSG: CAPTCHA ou controle de acesso;
- TJSC/eproc: mudanca de contrato detectada pelo parser.

## Inteiro teor e documentos

O teste documental foi executado com uma amostra por provider, primeiro com
`infanticidio` e depois com `responsabilidade civil`. `document_available`
significa que existe URL ou referencia documental; nao significa que o Studio
ja baixou o documento. `provider_document.loaded` significa que o metodo
documental do provider retornou texto.

| Provider | Busca | Texto na busca | Provider carregou documento | URL publica observada | Leitura QA |
| --- | --- | --- | --- | --- | --- |
| `tjdf_juris` | retornou | nao | sim, 12.970-17.783 chars | HTTP 200 HTML | Inteiro teor funciona sob demanda; URL exibida no resultado e a entrada SISTJ. |
| `tst_jurisprudencia` | retornou | nao | sim, 17.518-20.328 chars | HTTP 200 HTML | Rota `/rest/documentos/{id}` funciona; Studio ainda mostra link. |
| `stj_scon` | retornou | nao | sim, PDF de 270.212 bytes e 21.327 chars | HTTP 200, PDF publico | `get_document` preserva bytes, SHA-256, tamanho e texto extraido sob demanda. |
| `tjrs_solr` | retornou | nao | nao | URL invalida: `4296905` ou `5225133` | Defeito P1: `document_url` nao e URL publica consumivel. |
| `tjba_graphql` | retornou | sim, 29.749 chars | sim, 21.830 chars | rota relativa `/inteiroTeor/{id}` | Texto integral e o melhor caso da rodada; URL precisa de resolucao oficial no Studio. |
| `trf5_jurisprudencia` | retornou | nao | sim, 9.939 chars | HTTP 200 HTML | Documento existe; resultado de busca ainda tem resumo vazio. |
| `tjpa_jurisprudencia_bff` | retornou | sim no canonico | nao necessario para a amostra | endpoint de busca devolve HTTP 405 em GET | O payload bruto contem texto integral; a URL exibida nao e rota de detalhe. |
| `tjpb_pje_jurisprudencia` | retornou | nao | sim, 641 chars | HTTP 200 HTML | Documento acessivel, mas tamanho pequeno exige validacao de completude. |
| `tjpr_jurisprudencia` | retornou | nao | nao | HTTP 200 HTML | Conteudo parcial/pending release deve permanecer explicitamente parcial. |
| `tjpi_juspi` | retornou | nao | sim, 5.622-35.073 chars | HTTP 200 HTML | Documento publico carregavel pelo provider. |

Resumo das duas rodadas documentais:

- `infanticidio`: 7/10 providers retornaram busca; 3 carregaram documento pelo
  provider; 5 URLs responderam;
- `responsabilidade civil`: 10/10 providers retornaram busca; 6 carregaram
  documento pelo provider; 7 URLs responderam; 1 provider trouxe texto integral
  diretamente na busca.

Os numeros sao amostras de uma consulta e nao representam a cobertura total de
cada tribunal.

## Achados de qualidade

### Corrigido nesta auditoria

1. O Studio contava uma fonte parcial como se nao tivesse resultados. A metrica
   agora usa `count > 0` e conserva o status `partial` separadamente.
2. Foi criado um runner reproducivel para jornadas reais, screenshots e
   metadados de completude.
3. Foi criado um runner especifico para distinguir texto integral no resultado,
   documento carregado pelo provider e URL publica alcancavel.

### P1 - proxima onda

1. **TJRS/SOLR.** Corrigir a montagem de `document_url` e criar fixture para
   impedir que identificador numerico seja exposto como link.
2. **TJPA/BFF.** Normalizar `classe` e `orgao julgador` para texto legivel; hoje
   aparecem como representacao de dicionario Python. Manter o payload bruto e
   o texto integral canonico.
3. **TJBA/BFF e TJPA/BFF.** Resolver URLs relativas ou rotas de detalhe de forma
   explicita, sem apresentar endpoint de busca POST como se fosse documento.
4. **TJPB, TJPR e TRF5.** Promover testes de completude documental, porque
   resposta HTTP 200 nao prova que o inteiro teor esteja completo.
5. **Proveniencia documental.** Preencher no Studio `content_type`, bytes, hash,
   endpoint e data da carga quando o documento for aberto.

### P2 - experiencia profissional

1. Mostrar progresso por provider durante uma busca ampla.
2. Exibir um filtro "texto integral carregado" separado de "documento disponivel".
3. Permitir abrir o resultado em uma vista de leitura, sem perder o JSON bruto.
4. Exibir explicitamente quando a pagina federada tem 5 registros visiveis,
   embora cada fonte tenha retornado uma janela propria de 5 itens.
5. Adicionar um modo de amostra rapida para advogados e um modo de coleta
   paginada para jurimetristas.

## Verificacoes

- `ruff check src tests tools`: aprovado;
- `ruff format --check src tests tools`: 132 arquivos formatados;
- testes E2E do Studio: `10 passed`;
- suite offline: `563 passed, 5 skipped, 1 warning`;
- browser errors: nenhum nas jornadas reais;
- overflow horizontal: `false` em desktop e mobile.

## Conclusao QA

O Studio ja e adequado para demonstrar uma busca federada real com estados
explicitos e rastreabilidade inicial. Ele ja captura ementas e, dependendo da
fonte, texto integral diretamente ou por uma rota documental do provider.

Ainda nao deve ser apresentado como leitor unificado de inteiro teor nacional.
Hoje a busca e forte como descoberta e coleta inicial; o Studio ja carrega
documentos sob demanda para providers que declaram suporte, com contrato de
bytes, tipo, hash e completude. A proxima onda deve fechar TJRS, aprofundar a
completude de TJPB/TJPR/TRF5 e ampliar a mesma garantia para os demais
providers, sem transformar links ou respostas parciais em inteiro teor.
