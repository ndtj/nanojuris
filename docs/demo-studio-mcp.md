# NanoJuris Demo: Studio e MCP

Roteiro rapido para demonstrar o NanoJuris como biblioteca, Studio local e
MCP para agentes de IA.

## Pre-flight

Execute na raiz do repositorio:

```powershell
git pull
.\.venv\Scripts\python.exe -m pytest tests\test_studio.py tests\test_mcp_tools.py
.\.venv\Scripts\python.exe -m ruff check src tests
```

Quando o ambiente local tiver proxy quebrado ou corporativo, use o Studio sem
herdar `HTTP_PROXY`, `HTTPS_PROXY` ou `ALL_PROXY`:

```powershell
.\.venv\Scripts\python.exe -m nanojuris.cli studio --host 127.0.0.1 --port 8765 --ignore-env-proxy
```

Abra:

```text
http://127.0.0.1:8765
```

## Demo do Studio

Sequencia recomendada:

1. Abrir a tela inicial e mostrar a busca unificada limpa.
2. Buscar `incidente`.
3. Usar fontes maduras primeiro.
4. Mostrar que cada resultado preserva tribunal, numero, relator, orgao julgador,
   datas, ementa, fonte e rastreabilidade.
5. Abrir o painel de diagnostico para mostrar fontes consultadas, fontes puladas
   por razao semantica e fontes que exigem atencao.
6. Trocar para uma busca mais juridica, por exemplo:

```text
responsabilidade civil dano moral consumidor
```

### Verificacao live das fontes

O botao **verificar fontes** executa uma consulta minima nas fontes selecionadas
e mostra o contrato observado naquele momento. A verificacao e opt-in: abrir o
Studio nao dispara requisicoes contra tribunais automaticamente.

Os estados possuem significados diferentes:

- `valida`: a resposta passou pelo contrato normalizado minimo;
- `vazia`: a fonte respondeu, mas nao retornou registros para a consulta;
- `bloqueada`: a fonte exigiu controle de acesso;
- `indisponivel`: houve falha de rede, timeout ou indisponibilidade;
- `contrato alterado` / `contrato invalido`: a resposta nao corresponde ao
  contrato esperado e precisa de investigacao do provider.

Chamada equivalente pela API local:

```powershell
$body = @{
  query = "responsabilidade civil"
  sources = @("tjdf_juris", "tst_jurisprudencia")
  timeout = 45
} | ConvertTo-Json -Depth 6

Invoke-RestMethod `
  -Uri http://127.0.0.1:8765/api/validate `
  -Method Post `
  -ContentType "application/json" `
  -Body $body `
  -TimeoutSec 60
```

Exemplo de chamada direta da API do Studio:

```powershell
$body = @{
  query = "incidente"
  page_size = 3
  sources = @(
    "tjdf_juris",
    "trf4_eproc_jurisprudencia",
    "trf6_eproc_jurisprudencia"
  )
  filters = @{}
} | ConvertTo-Json -Depth 6

Invoke-RestMethod `
  -Uri http://127.0.0.1:8765/api/search `
  -Method Post `
  -ContentType "application/json" `
  -Body $body `
  -TimeoutSec 60
```

## Demo do MCP

O MCP local usa o entrypoint:

```powershell
.\.venv\Scripts\python.exe -m nanojuris.mcp_server
```

Em clientes MCP que aceitam configuracao JSON, use algo neste formato:

```json
{
  "mcpServers": {
    "nanojuris": {
      "command": "C:\\Users\\luciano.finozzi\\Desktop\\NanoJuris\\.venv\\Scripts\\python.exe",
      "args": ["-m", "nanojuris.mcp_server"],
      "env": {
        "NANOJURIS_TRUST_ENV": "0"
      }
    }
  }
}
```

Prompts prontos para demonstrar com agente:

```text
Liste as fontes de jurisprudencia disponiveis no NanoJuris e diga quais sao mais maduras para pesquisa unificada.
```

```text
Busque jurisprudencia publica sobre "incidente de desconsideracao da personalidade juridica" em fontes maduras e monte um resumo por tribunal.
```

```text
Pesquise "responsabilidade civil dano moral consumidor" e separe os resultados por tribunal, com numero do processo, relator, orgao julgador e tese/ementa.
```

```text
Explique quais fontes foram puladas ou falharam e diferencie erro de rede, controle de acesso e fonte fora do escopo.
```

## Mensagem central

NanoJuris nao tenta contornar controles de acesso. Ele centraliza rotas publicas
validas, preserva dados juridicos estruturados, expõe diagnostico transparente
e permite que advogados, pesquisadores e agentes de IA trabalhem com
jurisprudencia publica de forma rastreavel.
