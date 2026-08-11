# Source Contracts

NanoJuris trata cada provider como um contrato tecnico auditavel. O objetivo nao
e apenas "fazer a busca funcionar", mas saber com clareza:

- quais rotas publicas sustentam a extracao;
- quais parametros sao aceitos;
- quais campos sao estaveis;
- quais respostas representam sucesso, vazio, bloqueio ou erro;
- quais fontes sao adequadas para agentes de IA;
- quais lacunas ainda impedem uso profissional em escala.

## Uso rapido

Indice humano por provider: [docs/providers/](providers/README.md). O catalogo
machine-readable para humanos, CI e agentes esta em
[docs/registry/providers.json](registry/providers.json).

Via CLI:

```bash
nanojuris contratos
nanojuris contratos --fonte tjdf_juris
nanojuris contratos --resumo
```

Via Python:

```python
from nanojuris import NanoJurisClient

client = NanoJurisClient()

for contract in client.list_source_contracts():
    print(contract.source, contract.contract_level, contract.risk_level)
    print(contract.gaps)
```

Via MCP, use a tool `source_contracts` para agentes inspecionarem maturidade,
lacunas e proximos passos antes de consultar fontes reais.

## Niveis de maturidade

| Nivel | Label | Criterio pratico |
| --- | --- | --- |
| 1 | `busca_basica` | Provider inicial ou contrato ainda pouco conhecido. |
| 2 | `parser_com_fixtures` | Parser coberto por fixtures representativas. |
| 3 | `contrato_http_documentado` | Rotas, parametros, erros e limites com dossie tecnico. |
| 4 | `campos_canonicos_estaveis` | Campos canonicos, traces e documentos testados. |
| 5 | `erros_e_vazios_mapeados` | Sucesso, vazio, bloqueio e falhas sao separados. |
| 6 | `pronto_para_agentes` | Fonte pronta para fluxos MCP/IA com roteamento e limites claros. |

## Metodo de aprofundamento

Para cada provider superficial, siga este fluxo:

1. Abra a fonte oficial em navegador limpo.
2. Grave um HAR com uma busca publica simples.
3. Identifique rotas, metodos, parametros e payloads.
4. Reproduza a chamada com `requests` usando headers minimos.
5. Salve fixtures publicas para sucesso, vazio e erro esperado.
6. Documente campos obrigatorios, opcionais e ausentes.
7. Adicione testes de parser, erro, vazio e acesso restrito.
8. Atualize `ProviderCapabilities`.
9. Atualize ou crie o dossie canonico em `docs/providers/<provider>/README.md`.
10. Atualize a copia de compatibilidade em `docs/source-contracts/` e o registro
    central em `docs/registry/providers.json`.
11. Rode `nanojuris contratos --fonte <provider>` e ataque as lacunas restantes.

## Regra de documentacao

O repositorio segue duas camadas:

1. **Provider implementado**: deve ter README proprio em
   `docs/providers/<provider>/`, copia de compatibilidade em
   `docs/source-contracts/<provider>.md`, entrada em
   `docs/registry/providers.json`, secao em `docs/providers.md`,
   `ProviderCapabilities`, fixtures e testes.
2. **Fonte candidata**: deve ter dossie marcado como candidato antes de virar
   codigo, seguindo a mesma estrutura por provider. O dossie deve explicar o
   que foi testado, o que falta e por que a fonte ainda nao deve ser prometida
   como provider pronto.

Durante a migracao, os dossies antigos nao sao apagados nem substituidos por
redirecionamentos. A copia canonica e a copia legada permanecem equivalentes e
o teste de documentacao verifica essa paridade. Isso preserva links, contexto
historico, contratos, limites, fixtures e alertas ja publicados.

A fila viva de novos providers esta em
[provider-development-queue.md](provider-development-queue.md).

A matriz nacional de cobertura, com os 27 tribunais estaduais e os ramos
especializados, esta em
[national-coverage-matrix.md](national-coverage-matrix.md).

## O que nao fazer

- Nao contornar captcha, login, segredo de justica ou controle de acesso.
- Nao usar cookies pessoais ou sessoes autenticadas como contrato publico.
- Nao misturar comunicacoes judiciais, consulta processual e jurisprudencia
  decisoria como se fossem a mesma coisa.
- Nao tratar zero resultado como erro sem evidencias.
- Nao tratar controle de acesso esperado como quebra de parser.

## Template de dossie

A especificacao normativa completa esta em
[provider-dossier-template.md](provider-dossier-template.md). O modelo abaixo
continua como referencia rapida para compatibilidade com os dossies antigos.
As ultimas chamadas reais dos providers estao em
[live-validation-2026-08-11.md](live-validation-2026-08-11.md).

Cada dossie especifico deve seguir esta estrutura:

```text
# <provider>

## Identidade
- Fonte oficial:
- Categoria:
- Familia tecnica:
- URL inicial:
- Status de acesso:

## Contrato HTTP
- Rotas:
- Metodos:
- Parametros obrigatorios:
- Parametros opcionais:
- Paginacao:
- Ordenacao:
- Filtros:

## Dados retornados
- Campos extraidos:
- Campos canonicos:
- Campos opcionais:
- Campos instaveis:
- Inteiro teor:
- Documentos vinculados:

## Comportamento observado
- Busca com resultado:
- Busca sem resultado:
- Erro HTTP esperado:
- Controle de acesso/captcha:
- Mudanca de layout:

## Fixtures
- Sucesso:
- Vazio:
- Erro:
- Documento:

## MCP e agentes
- Quando usar:
- Quando pular:
- Mensagem segura para o usuario:
- Riscos:

## Proximos passos
- [ ] ...
```

## Prioridade atual

Use `needs_deepening` do resumo como fila tecnica. Em geral, priorize:

1. Fontes superiores com conteudo curado e valido, como `stf_informativo` e
   `stj_informativo`.
2. Fontes com alto valor juridico e risco alto, como `tjsp_cjsg` e `stj_scon`.
3. Familias reutilizaveis com rota limpa, como `eproc_jurisprudencia_federal`
   ja promovida para TNU/TRF2/TRF6 e CJSG/e-SAJ para TJAC/TJSP/TJMS.
4. Fontes boas para demonstracao e jurimetria, como `tjdf_juris`,
   `tjgo_projudi_jurisprudencia`, `tjrs_solr`, `tjba_graphql` e
   `trf4_eproc_jurisprudencia`.
5. Novos candidatos estaduais mapeados em
   [state-court-route-mapping-2026-08-07.md](state-court-route-mapping-2026-08-07.md),
   com prioridade para TJRR/Juris, TJPA BFF, TJMT API e TJPB/PJe; TJPI/JusPI e
   TJGO/Projudi ja foram promovidos para providers implementados.
6. Contratos parciais relevantes, como `justica_eleitoral_sjur`,
   `trt2_pje_jurisprudencia` e `tjma_jurisconsult`, mantendo bloqueios de
   captcha/antirrobo/desafio claramente documentados.

## Cobertura atual de dossies

Todos os providers atualmente registrados pelo `NanoJurisClient` possuem dossie
proprio em `docs/providers/<provider>/README.md` e copia legada em
`docs/source-contracts/`. Os proximos candidatos prioritarios tambem possuem
diretorio e fichas iniciais:

- `tjrr_juris`;
- `tjmt_jurisprudencia_api`;
- `tjpa_jurisprudencia_bff`;
- `tjpb_pje_jurisprudencia`.
