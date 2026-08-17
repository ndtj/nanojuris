# NanoJuris Studio HAR Audit - 2026-08-07

> Registro histórico da interface anterior. As referências a `studio.css` e
> `studio.js` descrevem a captura de 2026-08-07 e não o bundle oficial atual.

## Escopo

Auditoria do HAR `127.0.0.1 completo.har`, capturado contra o Studio local em
`http://127.0.0.1:8765`, e reauditoria do HAR
`127.0.0.1 completo final.har`.

## Evidencias do HAR

- Entradas capturadas: 5.
- Recursos estaticos carregados: `/`, `/assets/studio.css`, `/assets/studio.js`.
- API de fontes: `GET /api/sources` retornou 25 providers.
- Busca unificada: `POST /api/search` retornou HTTP 200.
- Tempo da busca unificada: 93,5s.
- Payload da busca: termo `incidente`, `page_size=10`, 25 fontes selecionadas.
- Resultado: 130 registros normalizados.

## Diagnosticos Encontrados

### Busca ampla demais por padrao operacional

O HAR mostra que todas as fontes foram acionadas de uma vez. Isso e valido para
auditoria, mas ruim como experiencia inicial: mistura fontes maduras, fontes
contextuais, fontes de alto risco e fontes que podem exigir validacao externa.

Acao aplicada:

- O Studio agora usa um preset inicial conservador com fontes `stable`.
- Foram adicionados presets explicitos: `maduras`, `jurisprudencia`, `todas` e
  `limpar`.
- Fontes com risco alto exibem aviso antes da busca.

### Filtros poderiam ser perdidos pelo ciclo de renderizacao

O frontend recriava os inputs antes de montar o payload de busca. Isso podia
zerar `date_from`, `date_to`, `number` e `page_size` quando a busca era
submetida.

Acao aplicada:

- Os filtros passaram a morar no estado do Studio.
- O payload agora e montado a partir do estado atualizado antes do novo render.

### Diagnostico de provider pouco visivel

O HAR continha falhas importantes, mas a UI mostrava isso somente em chips
compactos. Para pesquisa juridica, a diferenca entre erro, bloqueio, fonte fora
do escopo e zero resultado precisa ficar clara.

Acao aplicada:

- Criado painel `Diagnostico das fontes`.
- Cada fonte com `failed`, `skipped` ou `unknown` exibe motivo e mensagem tecnica.
- O payload de `/api/sources` agora inclui `contract_level`, `contract_label`,
  `risk_level`, `jurimetry_fit` e `studio_tier`.

### Ruido de navegador

O Studio nao declarava favicon. Isso podia gerar 404 discreto em capturas HAR
dependendo do navegador.

Acao aplicada:

- Adicionado favicon SVG.
- Adicionada rota `/favicon.ico`.
- Atualizado `MANIFEST.in` para incluir SVG no sdist.

## Falhas de Provider Observadas no HAR

- `bnp_pangea`: timeout.
- `stf_informativo`: falha SSL no ambiente.
- `stf_juris`: falha SSL no ambiente.
- `stj_informativo`: conexao encerrada sem resposta.
- `stj_scon`: validacao de acesso requerida.
- `tjac_cjsg`: timeout.
- `tjsp_cjsg`: captcha ou controle de acesso.
- `tre_sp_temas`: contrato de parser alterado ou conteudo esperado ausente.

Essas falhas foram tratadas como diagnostico operacional, nao como falha global
do Studio, porque `/api/search` respondeu HTTP 200 e preservou os resultados das
fontes que conseguiram responder.

## Validacao Pos-Correcao

- `pytest tests/test_studio.py`: 10 passed.
- `ruff check src tests`: passed.
- `ruff format --check src tests`: passed.
- `mypy src`: passed.
- `GET /`: HTTP 200.
- `GET /assets/studio.js`: HTTP 200.
- `GET /favicon.ico`: HTTP 200.
- `GET /api/sources`: 25 providers, defaults agora em fontes `stable`.

## Riscos Remanescentes

- Rotas externas dependem de rede, SSL, WAF, captcha, disponibilidade e politicas
  publicas dos tribunais.
- Busca em muitas fontes pode continuar lenta quando o usuario escolhe o preset
  `todas`.
- O ambiente local validado apresentou `ProxyError` para chamadas externas por
  proxy em `127.0.0.1:9`; isso deve ser investigado fora do Studio se persistir.

## Reauditoria do HAR Final

O HAR `127.0.0.1 completo final.har` apresentou uma unica chamada relevante:

- `POST /api/search`: HTTP 200 em aproximadamente 45s.
- Termo pesquisado: `incidente`.
- Fontes selecionadas: 25.
- Fontes pesquisadas pelo roteador: 22.
- Fontes puladas corretamente: 3.
- Total retornado: 0.

As tres fontes puladas estavam semanticamente corretas:

- `comunica_pje`: comunicacoes judiciais, nao jurisprudencia.
- `tjac_esaj_cpopg`: consulta processual exige identificador.
- `tjsp_esaj_cpopg`: consulta processual exige identificador.

As 22 falhas restantes tiveram a mesma causa tecnica:

- `ProxyError`.
- Tentativa de conexao com proxy local `127.0.0.1:9`.
- Conexao recusada pelo Windows (`WinError 10061`).

Conclusao: a busca nao retornou resultados porque o ambiente local impediu as
chamadas HTTP externas. O HAR final nao evidencia 22 bugs independentes de
provider nem ausencia de jurisprudencia para o termo `incidente`; evidencia um
problema de configuracao de rede/proxy herdado pelo processo do Studio.

Acao aplicada:

- `NanoJurisConfig` passou a declarar `trust_env`.
- Todos os providers baseados em `requests.Session` passam a respeitar
  `trust_env`.
- O Studio ganhou a flag `--ignore-env-proxy`.
- Erros agregados agora classificam proxy local invalido como
  `NetworkConfigurationError`, com mensagem e hint especificos.

Uso recomendado quando o ambiente injetar proxy invalido:

```powershell
nanojuris studio --ignore-env-proxy
```

Ou, por codigo:

```python
from nanojuris import NanoJurisClient, NanoJurisConfig

client = NanoJurisClient(NanoJurisConfig(trust_env=False))
```

Validacao local apos reiniciar o Studio com `--ignore-env-proxy`:

- Consulta `incidente` no preset estavel: 25 resultados.
- Consulta `incidente` nas 25 fontes, `page_size=2`: 30 resultados.
- Fontes pesquisadas: 22.
- Fontes puladas por roteamento semantico: 3.
- Fontes com erro remanescente: 6.

Erros remanescentes observados apos a correcao de proxy:

- `stf_informativo`: `SslVerificationError` no ambiente local.
- `stf_juris`: `SslVerificationError` no ambiente local.
- `bnp_pangea`: fonte retornou indisponibilidade/rejeicao operacional.
- `stj_scon`: controle de acesso requerido.
- `tjsp_cjsg`: controle de acesso requerido.
- `tre_sp_temas`: contrato de parser divergente do conteudo atual.

Esses erros devem ser tratados em ciclos especificos de provider. Eles nao
explicam mais uma busca global vazia, porque o Studio ja retorna resultados das
fontes acessiveis.
