# `trf3_jurisprudencia`

## Identidade

- Fonte oficial: Tribunal Regional Federal da 3a Regiao.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `trf_jurisprudencia_web`.
- Pesquisa: `https://web.trf3.jus.br/jurisprudencia/home/index/1`.
- Consulta de acordaos: `https://web.trf3.jus.br/acordaos/Acordao`.
- Status de acesso: `candidate_needs_har`.
- Nivel de evidencia: B, interface oficial confirmada; replay HTTP pendente.
- Status no NanoJuris: candidato, sem provider implementado.

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

### Consulta de acordaos

```text
GET https://web.trf3.jus.br/acordaos/Acordao
```

A carta de servicos oficial descreve consulta por numero de processo e acesso
ao inteiro teor, incluindo relatorio, voto e ementa quando o documento existe.
Essa rota e uma consulta documental por processo, distinta da pesquisa textual
da interface de jurisprudencia.

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

## Contrato pendente

Ainda nao foram confirmados por replay HTTP:

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

## Decisao de produto

O TRF3 e candidato relevante para cobertura federal, mas ainda nao e
`candidate_ready`. A evidencia atual permite mapear amplamente a entrada e as
superficies, mas nao autoriza provider sem resposta juridica reproduzida e
fixture offline.

## Fixtures necessarias

- [ ] HTML inicial da pesquisa.
- [ ] Captura de uma busca textual pequena.
- [ ] Resultado com processo, classe, orgao, relator, data e ementa.
- [ ] Resposta vazia.
- [ ] Consulta documental por numero de processo.
- [ ] Documento/inteiro teor publico, se acessivel.
- [ ] Parser offline antes do fetcher live.

## MCP e agentes

O MCP deve manter o TRF3 fora do roteamento automatico enquanto a busca nao
estiver reproduzivel. Pode expor a fonte como indisponivel ou pendente, sem
inventar resultados e sem confundir a consulta de acordaos por processo com
uma busca geral de jurisprudencia.

## Validacao live 2026-08-11

- A pesquisa oficial sofreu timeout de leitura em 25 segundos nesta janela.
- A superficie continua documentada como UI confirmada, mas sem contrato HTTP de resultados reproduzido.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Proximos passos

1. Usar captura automatica de rede em uma consulta publica simples.
2. Extrair o contrato sem guardar cookies ou tokens privados.
3. Testar a rota documental por processo separadamente da busca textual.
4. Criar fixtures, parser e testes de contrato.
5. Promover somente apos resposta juridica reproduzida por HTTP limpo.
## Dados Canonicos E Limites

A pesquisa textual deve mapear, quando publicados, processo, classe, orgao, relator, data, ementa, tipo documental, objeto, link de detalhe e inteiro teor. A consulta de acordao por processo deve ser um caminho separado, preservando relatorio, voto e ementa como documentos distintos quando a fonte os oferecer. Nenhum schema de resposta foi reproduzido no timeout atual.

## MCP

O MCP deve manter a busca textual fora da federacao e pode listar TRF3 como superficie pendente. CJF, TNU e Sumulas devem possuir fontes separadas. O timeout nao pode ser apresentado ao usuario como zero resultados.
