# Topologia nacional de jurisprudência

O arquivo [`national-topology.json`](national-topology.json) é uma fotografia
versionada do inventário conhecido pela NanoJuris. Ele separa autoridade,
collection, superfície técnica e provider; por isso não deve ser interpretado
como prova de cobertura nacional ou disponibilidade atual.

O catálogo institucional desta época individualiza 94 autoridades de tribunal,
incluindo os 27 TREs e os três TJMs estaduais. A evidência estrutural do CNJ
está em [`cnj-tribunal-register-20260901.json`](cnj-tribunal-register-20260901.json);
ela sustenta existência institucional, não disponibilidade de provider.
O probe limitado de URLs-raiz está em
[`court-catalog-url-probe-20260901.json`](court-catalog-url-probe-20260901.json)
e registra separadamente portais alcançáveis e respostas controladas (HTTP
403), sem transformar bloqueio em resultado vazio.

O artefato é gerado offline:

```powershell
python tools/build_national_topology.py
```

Claims e lacunas também são gerados offline a partir da mesma topologia:

```powershell
python tools/build_national_coverage.py
```

O JSON [`national-coverage-claims-20260901.json`](national-coverage-claims-20260901.json)
contém numerador, denominador, data, época, histórico e uma lacuna por
collection não implementada. A versão legível está em
[`national-coverage-claims-20260901.md`](national-coverage-claims-20260901.md).
O contrato do artefato esta versionado em
[`national-coverage.schema.json`](national-coverage.schema.json).
O denominador de providers inclui bindings ainda não reconciliados para evitar
que uma reconciliação parcial produza artificialmente 100%.

Para o planejamento por grau e coleção, consulte também a matriz
[`degree-coverage-matrix-20260901.json`](degree-coverage-matrix-20260901.json)
e sua versão legível
[`degree-coverage-matrix-20260901.md`](degree-coverage-matrix-20260901.md).
Ela separa explicitamente `CJPG` (primeiro grau) e `CJSG` (segundo grau) dos
demais ramos e registra cada lacuna sem promover um provider equivalente a um
contrato de grau específico.

O probe opcional das URLs-raiz (uma chamada pública por autoridade) pode ser
reproduzido com:

```powershell
python tools/probe_court_catalog_urls.py --output docs/topology/court-catalog-url-probe-20260901.json
```

Providers que ainda não possuem autoridade/collection reconciliada aparecem em
uma collection `authority:unknown`, com `status: unknown`. Essa representação é
intencional: ela preserva a lacuna para revisão, mas impede que um source ID
seja contado como tribunal ou como cobertura jurídica.

Cada época possui versão da topologia e data de corte. Claims de cobertura
devem informar a época, dimensão, numerador e denominador; percentuais sem
essas quatro informações não são claims válidos.
