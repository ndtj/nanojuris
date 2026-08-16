# Migracao Para NanoJud

NanoJuris agora mantem uma fronteira de produto mais rigorosa: a biblioteca e
voltada a jurisprudencia textual, precedentes, inteiro teor decisorio publico e
normalizacao para pesquisa juridica, jurimetria, dados e agentes de IA.

Consultas processuais, linhas do tempo, movimentacoes, partes, DataJud/CNJ e
comunicacoes judiciais pertencem ao NanoJud.

## Mapa De Destino

| Antiga superficie no NanoJuris | Destino correto no NanoJud | Motivo |
| --- | --- | --- |
| `comunica_pje` | `nanojud.djen` e `DjenProvider` | Retorna comunicacoes, intimacoes e publicacoes, nao jurisprudencia decisoria. |
| `tjac_esaj_cpopg` | `EsajProcessProvider` com perfil TJAC CPOPg | Consulta processual de primeiro grau. |
| `tjsp_esaj_cpopg` | `EsajProcessProvider` com perfil TJSP CPOPg/CPOSG | Consulta processual, partes e movimentacoes. |
| DataJud/CNJ processual | `nanojud.datajud` e `DataJudProvider` | Dados estruturados de processos, nao base de acordaos. |
| timeline processual | `nanojud.extraction` e `nanojud.timeline` | Linha do tempo combina processo, movimentos e comunicacoes. |

## Regra Pratica

Use NanoJuris quando a pergunta for:

- "quais decisoes existem sobre este tema?";
- "qual e a ementa, tese, relator, orgao julgador ou inteiro teor?";
- "quero montar uma base de jurisprudencia textual";
- "quero uma busca federada por tribunais e fontes jurisprudenciais".

Use NanoJud quando a pergunta for:

- "quais sao os andamentos deste processo?";
- "quais partes, movimentacoes ou audiencias aparecem?";
- "houve comunicacao no DJEN?";
- "o DataJud retornou dados estruturados deste CNJ?";
- "quero montar uma linha do tempo processual".

## Exemplo NanoJud

```python
from nanojud import api

numero = "0000000-00.0000.0.00.0000"

extrato = api.get_extrato(numero)
datajud = api.consultar_datajud(numero)
djen = api.consultar_djen(numero)
```

## Compatibilidade

Os providers processuais e de comunicacoes foram removidos do runtime do
NanoJuris para evitar confusao entre jurisprudencia e andamento processual.
Registros historicos de pesquisa podem mencionar esses contratos, mas novas
interfaces, exemplos e documentacao operacional devem apontar para NanoJud.
