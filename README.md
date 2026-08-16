# NanoJuris

<p align="center">
  <strong>Jurisprudência brasileira unificada em Python.</strong>
</p>

<p align="center">
  Uma interface única para consultar, normalizar e rastrear dados públicos de tribunais brasileiros.
</p>

<p align="center">
  <a href="https://github.com/ndtj/nanojuris/actions/workflows/ci.yml"><img src="https://github.com/ndtj/nanojuris/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://github.com/ndtj/nanojuris/security/code-scanning"><img src="https://img.shields.io/badge/CodeQL-analisado-2ea44f.svg" alt="CodeQL" /></a>
  <a href="https://pypi.org/project/nanojuris/"><img src="https://img.shields.io/pypi/v/nanojuris.svg" alt="PyPI" /></a>
  <a href="https://pypi.org/project/nanojuris/"><img src="https://img.shields.io/pypi/pyversions/nanojuris.svg" alt="Python 3.10+" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/licença-MIT-1f6feb.svg" alt="Licença MIT" /></a>
</p>

<p align="center">
  <a href="https://ndtj.com.br/">Contexto institucional: NDTJ</a> ·
  <a href="https://github.com/lucmolero">Mantenedor principal: Luciano Molero</a>
</p>

## O que é o NanoJuris

NanoJuris é uma biblioteca Python open source que conecta diferentes fontes
oficiais de jurisprudência por uma interface unificada. Ela transforma respostas
heterogêneas em dados estruturados, normalizados e rastreáveis para
desenvolvedores, profissionais do Direito, pesquisadores, analistas de dados e
agentes de IA.

<p align="center"><strong>Uma API. Múltiplas fontes. Um modelo de dados comum.</strong></p>

```text
Tribunais e fontes públicas
            │
            ▼
        NanoJuris
  acesso · aquisição · normalização
            │
            ▼
 Python · dados · jurimetria · agentes de IA
```

O projeto está evoluindo continuamente sua cobertura. “Implementado”, “validado”
e “disponível em consulta live” são estados diferentes; a documentação de cada
provider explicita essa distinção.

## Comece pelo seu objetivo

| Você quer... | Comece por... |
| --- | --- |
| Fazer uma busca em Python | [Quickstart](docs/quickstart.md) |
| Consultar pelo terminal | [CLI e exemplos](docs/quickstart.md#use-a-cli) |
| Conectar Claude, Codex ou outro agente | [MCP local](docs/mcp.md) |
| Entender o modelo de dados | [Arquitetura](docs/architecture.md) |
| Escolher uma fonte | [Capacidades por fonte](docs/source-capabilities.md) |
| Ver o estado real das fontes | [Status das fontes](docs/provider-status.md) |
| Criar ou corrigir um provider | [Guia de providers](docs/provider-development.md) |
| Auditar uma coleta | [Pipeline de extração](docs/extraction-pipeline.md) |

## Instalação

Para usar a biblioteca:

```bash
python -m pip install nanojuris
```

Para desenvolvimento local:

```bash
git clone https://github.com/ndtj/nanojuris.git
cd nanojuris
python -m venv .venv
python -m pip install -e ".[dev]"
```

O pacote requer Python 3.10 ou superior.

## Primeira consulta

```python
from nanojuris import NanoJurisClient

client = NanoJurisClient()
page = client.search(
    "responsabilidade civil",
    source="tjdf_juris",
    page_size=5,
)

for decision in page.results:
    print(decision.court, decision.number)
    print(decision.summary or decision.thesis)
```

Forma de resposta, usando uma fixture pública representativa do TJDFT:

```json
{
  "source": "tjdf_juris",
  "court": "TJDFT",
  "type": "acordao",
  "number": "0722671-67.2024.8.07.0000",
  "rapporteur": "SANDRA REVES",
  "judgment_date": "2024-09-04"
}
```

O bloco ilustra o formato canônico de uma resposta testada offline. A
disponibilidade live e os campos presentes devem ser confirmados no dossiê da
fonte em cada execução.

A resposta preserva os metadados normalizados e a trilha da fonte. A biblioteca
não transforma uma fonte instável em uma certeza: indisponibilidade, controle de
acesso, resultado vazio e limitação de cobertura permanecem observáveis.

## CLI para uso diário

```bash
nanojuris buscar "ICMS consumidor final" --orgaos STF,STJ --limite 5
```

Escolha o formato conforme o destino:

```bash
# Leitura e revisão humana
nanojuris buscar "ICMS consumidor final" --formato markdown

# Planilhas e jurimetria
nanojuris buscar "ICMS consumidor final" --formato csv

# Pipelines e agentes
nanojuris buscar "ICMS consumidor final" --formato jsonl
```

Descubra fontes, capacidades e diagnósticos antes de pesquisar:

```bash
nanojuris fontes
nanojuris diagnostico --fonte tjdf_juris
nanojuris tribunais --implementados
```

## MCP local para agentes de IA

O MCP é distribuído como um extra do mesmo pacote e roda localmente, próximo
ao ambiente do usuário:

```bash
python -m pip install "nanojuris[mcp]"
nanojuris-mcp
```

Depois, configure o cliente de IA para iniciar `nanojuris-mcp` como servidor
local. As ferramentas expõem descoberta de fontes, busca, diagnósticos,
exportação e consulta ao store SQLite. O [guia de MCP](docs/mcp.md) contém os
blocos de configuração para clientes compatíveis e as regras de segurança.

## O que o NanoJuris entrega

- **Consulta:** busca textual, filtros e paginação conforme o contrato de cada fonte.
- **Normalização:** modelos comuns para decisões, precedentes e documentos decisórios.
- **Rastreabilidade:** fonte, endpoint, parâmetros, horário, status de acesso e evidências.
- **Extração:** texto e metadados públicos, incluindo inteiro teor quando a fonte o entrega.
- **Persistência:** pesquisa reprodutível em SQLite, com runs e exportação.
- **Integração:** SDK Python, CLI, MCP local e formatos JSON, JSONL, CSV e Markdown.
- **Governança:** documentação por provider, uso responsável e limites explícitos.

## Cobertura atual

O catálogo separa o que está implementado do que foi apenas mapeado para
desenvolvimento:

| Estado | Quantidade | Significado |
| --- | ---: | --- |
| Providers implementados | 37 | Há adapter registrado no pacote |
| Fontes candidatas | 16 | Há evidência ou pesquisa, mas não são runtime |
| Especificações de família | 1 | Contrato compartilhado aguardando adapters |

Consulte o [catálogo machine-readable](docs/registry/providers.json), a
[matriz de cobertura](docs/provider-coverage-map.md) e os
[dossiês individuais](docs/providers/README.md). Cada dossiê distingue rota
observada, resposta reproduzida e provider pronto para uso.

No Studio, a selecao **maduras** inicia com 7 fontes estaveis; **jurisprudencia**
inclui as fontes recomendadas para busca textual; e **todas** expande para os providers
registrados. Esses modos sao conveniencias de selecao, nao garantias de
disponibilidade live: falhas, bloqueios externos e resultados vazios permanecem
visiveis na resposta.

Consulta processual, DataJud/CNJ, DJEN, comunicacoes judiciais, partes,
movimentacoes e linhas do tempo pertencem ao NanoJud. Veja
[migration-to-nanojud.md](docs/migration-to-nanojud.md).

## Arquitetura em camadas

```text
Fonte pública
    │  resposta original + evidência
    ▼
Raw source record
    │  parser específico do tribunal
    ▼
Normalized provider record
    │  contrato canônico
    ▼
Canonical legal record
    ├── SDK Python
    ├── CLI / exportadores
    ├── SQLite / research runs
    └── MCP local / Studio
```

O provider conhece o contrato da fonte. O núcleo conhece normalização,
paginação, auditoria e persistência. Essa separação permite adicionar fontes
sem contaminar o modelo comum com semânticas específicas de um tribunal.

## Integridade e uso responsável

NanoJuris trabalha somente com fontes públicas ou legitimamente acessíveis ao
usuário. O projeto não tenta contornar captcha, login, WAF, geoblock ou outra
barreira de acesso. Quando um documento não pode ser obtido, essa limitação é
registrada em vez de ser mascarada.

Os resultados são dados para pesquisa e automação. Eles não substituem a
leitura da fonte oficial, a análise profissional do caso ou a verificação da
vigência de um entendimento. Consulte [Uso responsável](docs/responsible-use.md)
antes de incorporar resultados em fluxos jurídicos.

## Documentação

O [Portal de documentação](docs/README.md) organiza a leitura em quatro
percursos:

1. **Usar:** instalação, Python, CLI, MCP e armazenamento.
2. **Compreender:** arquitetura, contratos canônicos e pipeline de extração.
3. **Expandir:** dossiês, playbook de descoberta e desenvolvimento de providers.
4. **Governar:** segurança, releases, contribuição, autoria e decisões do projeto.

## Desenvolvimento

```bash
python -m pip install -e ".[dev,mcp,studio]"
python -m pytest
ruff check src tests examples tools
ruff format --check src tests examples tools
mypy src
```

Leia [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md),
[MAINTAINERS.md](MAINTAINERS.md) e [GOVERNANCE.md](GOVERNANCE.md) antes de abrir
uma contribuição.

## Autoria e contexto institucional

O NanoJuris é criado e mantido principalmente por
[Luciano Molero](https://github.com/lucmolero), responsável pela arquitetura,
implementação, releases e manutenção técnica.

O projeto foi desenvolvido no contexto do
[Núcleo de Direito, Tecnologia e Jurimetria (NDTJ)](https://ndtj.com.br/), um
centro acadêmico que relaciona direito, tecnologia, inteligência artificial e
jurimetria. O contexto institucional apoia a colaboração e não altera a
autoria dos commits, do código ou das decisões técnicas. A estrutura formal de
manutenção está em [MAINTAINERS.md](MAINTAINERS.md) e
[GOVERNANCE.md](GOVERNANCE.md).

## Licença

Distribuído sob a [licença MIT](LICENSE). O NanoJuris não é produto oficial do
CNJ, STF, STJ, TST, TJSP ou de qualquer outro tribunal.
