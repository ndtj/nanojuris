<p align="center">
  <strong>NanoJuris</strong>
</p>

<h1 align="center">Jurisprudencia publica brasileira para Python e agentes de IA</h1>

<p align="center">
  Busque, normalize e audite precedentes e jurisprudencia publica com rastreabilidade.
</p>

<p align="center">
  <a href="https://ndtj.com.br/">Projeto desenvolvido no contexto do NDTJ</a>
  ·
  <a href="https://github.com/lucmolero">Principal mantenedor: Luciano Molero</a>
</p>

<p align="center">
  <a href="https://github.com/ndtj/nanojuris/actions/workflows/ci.yml">
    <img src="https://github.com/ndtj/nanojuris/actions/workflows/ci.yml/badge.svg" alt="CI" />
  </a>
  <a href="https://github.com/ndtj/nanojuris/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT" />
  </a>
  <a href="https://github.com/ndtj/nanojuris">
    <img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+" />
  </a>
</p>

<p align="center">
  <a href="https://github.com/ndtj/nanojuris/actions">Actions</a>
  |
  <a href="docs/quickstart.md">Quickstart</a>
  |
  <a href="docs/architecture.md">Arquitetura</a>
  |
  <a href="docs/responsible-use.md">Uso responsavel</a>
  |
  <a href="docs/source-capabilities.md">Fontes</a>
  |
  <a href="docs/providers/README.md">Dossies por provider</a>
  |
  <a href="docs/provider-documentation-audit.md">Auditoria documental</a>
  |
  <a href="docs/registry/providers.json">Catalogo para IA</a>
  |
  <a href="docs/provider-coverage-map.md">Cobertura</a>
  |
  <a href="docs/extraction-pipeline.md">Pipeline</a>
  |
  <a href="docs/storage.md">Storage</a>
  |
  <a href="docs/provider-development.md">Providers</a>
  |
  <a href="docs/case-studies.md">Casos de uso</a>
  |
  <a href="docs/audience-ux.md">UX por publico</a>
  |
  <a href="docs/use-case-validation-matrix.md">Matriz de validacao</a>
  |
  <a href="docs/release-checklist.md">Release</a>
  |
  <a href="docs/mcp.md">MCP</a>
  |
  <a href="docs/elite-extraction-blueprint.md">Blueprint de extracao</a>
</p>

## O que e

NanoJuris e uma biblioteca Python open source para consulta, normalizacao e
auditoria de jurisprudencia publica brasileira.

## Autoria E Contexto Institucional

O NanoJuris e criado e mantido principalmente por
[Luciano Molero](https://github.com/lucmolero), responsavel pela arquitetura,
implementacao, releases e manutencao tecnica do projeto.

O desenvolvimento esta vinculado ao contexto academico do
[Nucleo de Direito, Tecnologia e Jurimetria (NDTJ)](https://ndtj.com.br/),
centro de formacao que relaciona direito, tecnologia, inteligencia artificial e
jurimetria. A organizacao institucional do repositorio e o contexto de
colaboracao nao alteram a autoria dos commits, da arquitetura ou do software.

Consulte [MAINTAINERS.md](MAINTAINERS.md) e [GOVERNANCE.md](GOVERNANCE.md)
para a estrutura de manutencao e tomada de decisoes.

O registry atual separa 34 fontes implementadas, 22 candidatas e uma familia de
implementacao. Ele e a referencia completa para descobrir cada provider e seu
status: [catalogo de providers](docs/registry/providers.json). `bnp_pangea` consulta a API publica usada pelo
frontend do Banco Nacional de Precedentes/Pangea. `comunica_pje` consulta a API
publica do Comunica PJe/DJEN para comunicacoes judiciais. `tjdf_juris` consulta
a jurisprudencia publica do TJDFT/SISTJ. `tjac_cjsg`, `tjal_cjsg`, `tjam_cjsg` e
`tjms_cjsg` consultam a jurisprudencia publica CJSG/e-SAJ de TJAC, TJAL, TJAM e TJMS. `tjsp_cjsg` consulta a
pesquisa publica de jurisprudencia do TJSP/CJSG quando a fonte nao exige
controle de acesso. `tjsp_eproc_jurisprudencia` consulta a jurisprudencia
publica do eproc/TJSP. `tjsp_nugepnac` cobre IRDR/IAC oficiais do TJSP.
`tce_sp_jurisprudencia` cobre sumulas e boletins publicos do TCE-SP.
`tre_sp_temas` cobre temas selecionados publicos do TRE-SP.
`trf4_eproc_jurisprudencia` consulta a jurisprudencia
publica do eproc/TRF4 e suporta inteiro teor publico. `tjsp_esaj_cpopg` consulta processo publico de primeiro grau
por numero CNJ, nome da parte e OAB no e-SAJ/TJSP. `tjac_esaj_cpopg` consulta
processo publico de primeiro grau por numero CNJ no e-SAJ/TJAC. `stm_jurisprudencia` consulta
a jurisprudencia publica do STM/JMU e preserva a URL publica de inteiro teor.
`stf_informativo` consulta a planilha publica oficial do Informativo STF, com
teses, resumos, materias, relator, orgao julgador e processo em dados
estruturados. `stj_informativo` consulta o HTML publico do Informativo de
Jurisprudencia do STJ para notas oficiais e julgados referenciados. `stf_juris`
cobre a API JSON observada no frontend oficial do STF quando a fonte responde
sem WAF. `stj_scon` inicia a cobertura STJ/SCON por acordaos
com parser offline, capabilities declaradas e ficha publica em
[docs/stj-source-profile.md](docs/stj-source-profile.md). `tst_jurisprudencia`
consulta a API REST publica do TST, com filtros textuais, metadados de acordaos
e inteiro teor HTML sob demanda.

## Por que existe

Advogados, pesquisadores e times de tecnologia juridica precisam de dados de
jurisprudencia em formato confiavel, rastreavel e facil de integrar com
automacoes e agentes de IA.

NanoJuris entrega:

- modelos tipados;
- provider BNP/Pangea funcional;
- provider Comunica PJe/DJEN para comunicacoes judiciais publicas;
- provider TJDFT/SISTJ para jurisprudencia publica;
- provider TJMS/CJSG para jurisprudencia publica;
- provider STM/JMU para jurisprudencia publica e inteiro teor;
- provider TJSP/CJSG parcial para jurisprudencia publica e inteiro teor;
- provider TJSP/eproc para jurisprudencia publica;
- provider TJSP/e-SAJ CPOPg para consulta processual publica por numero CNJ,
  nome da parte e OAB;
- provider TJAC/e-SAJ CPOPg para consulta processual publica por numero CNJ;
- provider TJSP/NugepNac para IRDR/IAC oficiais;
- provider TCE-SP para sumulas e boletins de jurisprudencia;
- provider TRE-SP para temas selecionados de jurisprudencia eleitoral;
- provider TRF4/eproc para jurisprudencia publica e inteiro teor;
- provider STF Informativo para teses e resumos oficiais estruturados;
- provider STJ Informativo para notas oficiais de jurisprudencia;
- provider STJ/SCON inicial com parser offline de acordaos;
- cliente Python simples;
- CLI;
- exportacao JSON, JSONL, CSV e Markdown;
- rastreabilidade de fonte;
- governanca de uso responsavel.

O plano de evolucao extraction-first, com arquitetura alvo, modelos canonicos,
MCP e fontes nacionais prioritarias, esta em
[docs/elite-extraction-blueprint.md](docs/elite-extraction-blueprint.md).

As capacidades declaradas por fonte estao documentadas em
[docs/source-capabilities.md](docs/source-capabilities.md).
O mapa de cobertura e oportunidades de providers brasileiros esta em
[docs/provider-coverage-map.md](docs/provider-coverage-map.md).
O estado de maturidade de cada dossie, incluindo lacunas de contrato e fixtures
pendentes, esta em [docs/provider-documentation-audit.md](docs/provider-documentation-audit.md).

A auditoria estado a estado esta em
[docs/national-coverage-matrix.md](docs/national-coverage-matrix.md); ela
separa cobertura mapeada de providers efetivamente implementados.
O playbook para mapear rotas publicas viaveis com score tecnico esta em
[docs/route-mapping-playbook.md](docs/route-mapping-playbook.md).
Os contratos reutilizaveis de aquisicao e parsing estao em
[docs/extraction-pipeline.md](docs/extraction-pipeline.md).
A estrategia SQLite-first com caminho futuro para PostgreSQL esta em
[docs/storage.md](docs/storage.md).
O guia para novas fontes e providers esta em
[docs/provider-development.md](docs/provider-development.md).
O padrao completo de cada dossie e a matriz de prontidao estao em
[docs/provider-dossier-template.md](docs/provider-dossier-template.md) e
[docs/provider-documentation-audit.md](docs/provider-documentation-audit.md).
As simulacoes de uso real por advogados, pesquisadores e desenvolvedores estao
em [docs/case-studies.md](docs/case-studies.md).
Os principios de UX direta para advogados, desenvolvedores, jurimetristas,
analistas de dados e agentes de IA estao em
[docs/audience-ux.md](docs/audience-ux.md).
A matriz pratica para testar pontos implementados, parciais e planejados esta em
[docs/use-case-validation-matrix.md](docs/use-case-validation-matrix.md).
O relatorio mais recente de validacao por areas tecnicas e casos de uso esta em
[docs/validation-report-2026-08-02.md](docs/validation-report-2026-08-02.md).
O checklist de release publica esta em
[docs/release-checklist.md](docs/release-checklist.md).

## Instalacao local

```bash
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

## Primeiro uso em Python

```python
from nanojuris import NanoJurisClient

client = NanoJurisClient()

page = client.search(
    "ICMS consumidor final",
    courts=["STF", "STJ"],
    types=["RG", "RR"],
    page_size=5,
)

for result in page.results:
    print(result.court, result.type, result.number)
    print(result.thesis)
```

## Primeiro uso via CLI

```bash
nanojuris buscar "ICMS consumidor final" --orgaos STF,STJ --tipos RG,RR --limite 5
```

Markdown:

```bash
nanojuris buscar "ICMS consumidor final" --orgaos STF,STJ --formato markdown
```

JSONL:

```bash
nanojuris buscar "ICMS consumidor final" --formato jsonl
```

JSONL canonico para pipelines de dados:

```bash
nanojuris buscar "ICMS consumidor final" --formato canonical-jsonl
```

CSV com campos objetivos de extracao:

```bash
nanojuris buscar "ICMS consumidor final" --formato csv
```

Fontes e capacidades:

```bash
nanojuris fontes
nanojuris diagnostico --fonte tjsp_cjsg
nanojuris probe-rota "https://tribunal.exemplo.jus.br/jurisprudencia?q=idpj" --expect "Ementa"
nanojuris buscar "infanticidio" --fonte comunica_pje --orgaos TJSP --limite 5
nanojuris buscar "infanticidio" --fonte comunica_pje --publicacao-de 2026-07-31 --publicacao-ate 2026-07-31
nanojuris buscar "infanticidio" --fonte tjdf_juris --limite 5
nanojuris buscar "infanticidio" --fonte tjac_cjsg --limite 5
nanojuris buscar "" --fonte tjac_esaj_cpopg --numero "0001970-91.2024.8.01.0001"
nanojuris buscar "infanticidio" --fonte tjal_cjsg --limite 5
nanojuris buscar "infanticidio" --fonte tjam_cjsg --limite 5
nanojuris buscar "infanticidio" --fonte tjms_cjsg --limite 5
nanojuris buscar "desercao" --fonte stm_jurisprudencia --limite 5
nanojuris buscar "infanticidio" --fonte tjsp_eproc_jurisprudencia --limite 5
nanojuris buscar "garantia" --fonte tjsp_nugepnac --tipos irdr --limite 5
nanojuris buscar "subvencao" --fonte tce_sp_jurisprudencia --tipos sumula --limite 5
nanojuris buscar "abuso de poder" --fonte tre_sp_temas --limite 5
nanojuris buscar "desercao" --fonte trf4_eproc_jurisprudencia --limite 5
nanojuris buscar "" --fonte tjsp_esaj_cpopg --parte "ANDERSON DE AZEVEDO GONCALVES" --limite 4
nanojuris buscar "" --fonte tjsp_esaj_cpopg --oab "123456" --limite 2
nanojuris buscar "" --fonte tjsp_esaj_cpopg --numero "0003938-14.2017.8.26.0323" --detalhar
nanojuris tribunais --uf SP --implementados
```

Salvar resultados canonicos em SQLite:

```bash
nanojuris buscar "ICMS consumidor final" --store nanojuris.db
```

Consultar o store local:

```bash
nanojuris store stats nanojuris.db
nanojuris store query nanojuris.db --kind decision --tribunal TJSP
nanojuris store get nanojuris.db decision dec-1
nanojuris store runs nanojuris.db
nanojuris store records nanojuris.db run-...
nanojuris store export nanojuris.db run-... --formato csv
nanojuris store export nanojuris.db run-... --formato jsonl --limite 100 --offset 100
nanojuris documento tjsp-cjsg-20787558-0 --fonte tjsp_cjsg
```

Use `--formato markdown` para leitura humana e auditoria, `csv` para planilhas e
jurimetria, `jsonl` para pipelines de dados e `json` para agentes e integracoes.
Use `--offset` para paginar runs grandes sem perder o `run_id` auditavel.
Use `documento` apenas para inteiro teor que a fonte publica entrega sem login,
captcha ou outro controle de acesso.
Use `tribunais` para descobrir o mapa brasileiro de tribunais conhecido pela lib,
mesmo antes de todos os providers estarem implementados.

## MCP local

Instale o extra MCP e rode o servidor local:

```bash
pip install "nanojuris[mcp]"
nanojuris-mcp
```

As tools MCP iniciais expoem fontes, diagnostico, busca, exportacao de
resultados e consulta a stores SQLite locais. Detalhes em
[docs/mcp.md](docs/mcp.md).

## Provider inicial

### `bnp_pangea`

Fonte: Banco Nacional de Precedentes/Pangea.

Recursos:

- parametros publicos de orgaos e especies;
- catalogo normalizado de tribunais e especies;
- sugestoes publicas de pesquisa;
- busca textual de precedentes;
- agregacoes por tribunal e especie;
- detalhes de decisoes vinculadas quando disponiveis;
- rastreabilidade de endpoint, filtro e data de coleta.

Catalogo normalizado:

```bash
nanojuris parametros --catalogo
```

Sugestoes, quando o endpoint publico estiver disponivel:

```bash
nanojuris sugestoes "icms"
```

Teste live opcional:

```bash
$env:NANOJURIS_RUN_LIVE = "1"
python -m pytest -m live
```

### `tjsp_cjsg`

Fonte: Consulta de Jurisprudencia do TJSP/CJSG.

Recursos:

- busca completa via formulario publico;
- parser HTML de resultados;
- paginacao segura quando a busca principal publica ja criou sessao valida;
- extracao de numero do processo/recurso, relator, comarca, orgao julgador,
  classe, assunto e ementa;
- identificadores `cdAcordao` e `cdForo`;
- URL publica de inteiro teor quando disponivel e status honesto quando
  `getArquivo.do` redireciona para login;
- deteccao de captcha/controle de acesso sem bypass.

Exemplo:

```bash
nanojuris buscar "infanticidio" --fonte tjsp_cjsg --tipos acordao --limite 5
```

Se o TJSP exigir captcha, sessao ausente ou login, o provider interrompe a busca
com erro claro ou marca o documento como `login_required`.

## Filosofia tecnica

NanoJuris nao tenta burlar fontes publicas. O projeto deve:

- preferir APIs publicas e oficiais;
- detectar controles de acesso e parar;
- aplicar timeout e limites;
- separar extracao de interpretacao juridica;
- preservar fonte, endpoint e query usada;
- manter fixtures sem dados sensiveis.

## Roadmap

O pacote atual e `v0.2.0`. A lista historica completa, incluindo itens que ja
foram entregues depois da numeracao original, esta em
[`docs/roadmap.md`](docs/roadmap.md). O estado operacional deve ser conferido
pelos providers registrados, seus contratos e o CI, nao apenas pelo numero da
versao.

## Projeto independente

NanoJuris nao e produto oficial do CNJ, TJSP, STJ, STF ou qualquer tribunal. A
biblioteca organiza consultas a fontes publicas ou legitimamente acessiveis ao
usuario.
