# `trf3_jurisprudencia`

## Identidade

- Fonte oficial: Tribunal Regional Federal da 3a Regiao.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `trf_jurisprudencia_web`.
- Pesquisa: `https://web.trf3.jus.br/jurisprudencia/home/index/1`.
- Consulta de acordaos: `https://web.trf3.jus.br/acordaos/Acordao`.
- Status de acesso: `transport_unconfirmed` para o host de busca; rota
  documental implementada, mas ainda não promovida.
- Nível de evidência: B, interface e documento oficiais confirmados; replay
  HTTP direto desta rede permanece sujeito a timeout.
- Status no NanoJuris: provider executável opt-in, fora da federação padrão.

## Superficies oficiais encontradas

### Pesquisa de jurisprudencia

```text
GET https://web.trf3.jus.br/jurisprudencia/home/index/1
```

A interface publica apresenta pesquisa de jurisprudencia para monocraticas e
Turmas Recursais dos JEFs, com campos e controles para:

- operadores de pesquisa textual;
- numero do processo;
- relator;
- data;
- classe;
- orgao julgador;
- ementa;
- objeto do processo;
- lista resumida de resultados.

Tambem ha referencias para Jurisprudencia Unificada do CJF, Jurisprudencia
Unificada da TNU e Sumulas do TRF3. Essas entradas devem ser tratadas como
superficies relacionadas, mas nao misturadas no provider do TRF3.

### Consulta de acórdãos por processo (contrato implementado)

```text
GET https://web.trf3.jus.br/acordaos/Acordao/PesquisarDocumento?processo=<20 dígitos CNJ>
GET https://web.trf3.jus.br/acordaos/Acordao/BuscarDocumentoPje/<id>
```

A resposta pública lista cada data de acórdão para o processo e os links de
documento abrem HTML com cabeçalho, relator, relatório, voto, ementa e
dispositivo quando publicados. Essa rota é uma consulta documental por
processo, distinta da pesquisa textual da interface de jurisprudência.

## Evidencia e tentativa registrada

Evidencia oficial da interface: nivel B. A pagina de pesquisa foi confirmada
por superficie web publica e apresentou os campos juridicos descritos acima.

Tentativa HTTP limpa ja executada:

```text
GET https://web.trf3.jus.br/jurisprudencia/home/index/1
Perfil: requests limpo, sem proxy de ambiente
Resultado: timeout de leitura em 45 segundos
Estado: blocked_transport
```

Essa tentativa nao deve ser repetida com a mesma chave sem uma mudanca
observavel. O timeout nao prova ausencia da fonte nem valida o contrato de
busca; ele limita a evidencia disponivel neste ambiente.

## Contrato de busca textual ainda pendente

Ainda não foram confirmados por replay HTTP da interface textual:

- action e metodo final do formulario;
- nomes e valores de todos os campos;
- chamada AJAX ou endpoint JSON de resultados;
- paginacao e ordenacao;
- resposta vazia e mensagens de validacao;
- rota de detalhe a partir de resultado textual;
- formato de documentos e links de inteiro teor;
- catalogos de relatores, classes e orgaos.

Nao inferir esses elementos apenas dos controles visuais. A proxima evidencia
deve vir de captura automatica de rede em consulta publica normal ou de uma
rota oficial alternativa reproduzivel.

## Matriz de cobertura atual

| Superficie | Estado | Evidencia | Proximo teste |
| --- | --- | --- | --- |
| entrada oficial | `ui_confirmed` | portal de pesquisa publico | revalidar sem repetir timeout |
| pesquisa textual | `ui_confirmed` | campos e operadores visiveis | capturar submissao normal |
| filtros/catalogos | `partial` | campos de relator, classe e orgao | identificar opcoes e payload |
| recentes | `unknown` | nao identificado | procurar menu ou endpoint |
| detalhe por processo | `ui_confirmed` | rota oficial de acordaos | testar com numero publico controlado |
| inteiro teor | `ui_confirmed` | carta de servicos descreve voto, relatorio e ementa | validar link/documento |
| CJF/TNU/Sumulas | `discovered` | links na propria interface | criar fichas separadas |
| erros/limites | `unknown` | replay pendente | registrar resposta do formulario |

## Decisão de produto

O TRF3 continua candidato para busca textual geral. A rota por processo já
possui parser, fixture e testes offline, mas permanece opt-in porque a chamada
HTTP direta ao host expirou nesta rede. Isso não é tratado como resultado vazio
nem como validação live.

## Fixtures necessarias

- [ ] HTML inicial e replay da pesquisa textual.
- [ ] Captura de uma busca textual pequena.
- [x] Resultado documental por processo com datas e links.
- [x] Resposta vazia do lookup por processo.
- [x] Parser offline antes do fetcher live.
- [x] Documento HTML de inteiro teor e preservação de bytes.

## MCP e agentes

O MCP deve manter o TRF3 fora do roteamento automatico enquanto a busca nao
estiver reproduzivel. Pode expor a fonte como indisponivel ou pendente, sem
inventar resultados e sem confundir a consulta de acordaos por processo com
uma busca geral de jurisprudencia.

## Validação live 2026-09-07

- A pesquisa textual oficial e as rotas de lookup foram tentadas com requests
  HTTPS bounded, sem proxy, credenciais ou contorno de proteção; o host
  expirou antes de fornecer uma resposta HTTP nesta rede.
- A documentação oficial e a leitura pública do portal confirmam a rota de
  processo e o documento textual; essa evidência não substitui uma validação
  live direta do adapter.
- Evidência estruturada: `docs/provider-discovery/trf3-jurisprudencia-live-20260907.json`.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Proximos passos

1. Revalidar a rota por processo quando o host responder em uma janela bounded.
2. Usar captura automática de rede somente para descobrir o contrato textual,
   sem guardar cookies ou tokens privados.
3. Promover somente após resposta jurídica reproduzida pelo adapter e gate de
   qualidade; até lá, manter `supports_unified_search=false`.

## Rechecagem de transporte - ciclo 3 (2026-09-01)

Para testar uma rota oficial alternativa sem repetir a mesma chave de timeout,
foram feitas tres chamadas GET bounded, sem credenciais: `/acordaos/Acordao`,
`/jurisprudencia/Home/ResultadoTotais` e
`/jurisprudencia/Home/BuscarSugestao?term=dano`. As tres expiraram por
`ReadTimeout` de 6 segundos nesta rede. O estado permanece `candidate` com
`blocked_transport`; isso nao e zero resultados nem prova indisponibilidade
permanente. Metadados: [trf3-live-recheck-20260901-cycle3.json](../../provider-discovery/trf3-live-recheck-20260901-cycle3.json).
## Transporte compartilhado e limites (2026-09-08)

O lookup exato por processo e a busca do inteiro teor agora usam o
`SharedHttpClient` com allowlist do host oficial, HTTP/1.1, timeout configurado,
limite de 8 MB por resposta, retry apenas para falhas idempotentes transitórias,
rate limit e circuit breaker. Redirecionamentos fora da allowlist, respostas
excessivas, timeout, TLS e HTTP 403/429 permanecem estados explícitos; nenhum é
convertido em resultado vazio. A migração melhora a segurança do transporte,
mas não altera o estado de promoção: a pesquisa textual geral continua sem
contrato HTTP reproduzível e o provider permanece opt-in/candidato.

## Dados Canonicos E Limites

A pesquisa textual deve mapear, quando publicados, processo, classe, orgao, relator, data, ementa, tipo documental, objeto, link de detalhe e inteiro teor. A consulta de acordao por processo deve ser um caminho separado, preservando relatorio, voto e ementa como documentos distintos quando a fonte os oferecer. Nenhum schema de resposta foi reproduzido no timeout atual.

## Rechecagem bounded - 2026-09-09

Foi repetida uma única chamada controlada ao lookup oficial por número de
processo, usando o adapter NanoJuris e o transporte compartilhado, com timeout
de 8 segundos, limite de uma página, sem credenciais, proxy ou contorno de
proteções. A tentativa expirou em transporte antes de uma resposta HTTP
completa. O resultado foi classificado como `transport_error` /
`source_unavailable`, não como vazio autoritativo. Evidência redigida:
`docs/provider-discovery/trf3-jurisprudencia-live-20260909.json`.

O provider permanece `opt_in_pending_live`; não há base para promoção nem para
repetir a mesma rota nesta rede sem mudança observável de disponibilidade.

## MCP

O MCP deve manter a busca textual fora da federacao e pode listar TRF3 como superficie pendente. CJF, TNU e Sumulas devem possuir fontes separadas. O timeout nao pode ser apresentado ao usuario como zero resultados.
