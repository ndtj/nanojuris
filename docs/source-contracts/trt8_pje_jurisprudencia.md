# Contrato de fonte — TRT8 PJe jurisprudência

## Identidade

- autoridade: `TRT8`;
- ramo: `labor`;
- grau/instância: `second`;
- coleção: `CJSG`/`JURISPRUDENCIA`;
- tipo documental: `acordao`.

## Rotas oficiais

| Método | Rota | Uso |
| --- | --- | --- |
| GET | `/juris-backend/api/opcoes` | opções públicas e política de desafio |
| POST | `/juris-backend/api/filtros` | agregações de filtros |
| POST | `/juris-backend/api/documentos` | busca paginada |
| POST | `/juris-backend/api/documentos/{id}` | ementa, dispositivo e inteiro teor |

O host permitido é exclusivamente `pje.trt8.jus.br`.

## Payload mínimo

```json
{
  "ordenarPor": "relevancia",
  "andField": ["dano", "moral"],
  "instancia": ["2ª Instância"],
  "tipoDocumento": ["Acórdão"],
  "paginationSize": 10,
  "paginationPosition": 1,
  "fragmentSize": 512
}
```

Campos opcionais só são enviados quando suportados e preenchidos. O adapter
mantém os valores de `instancia` e `tipoDocumento` obrigatórios para impedir a
mistura com decisões de primeiro grau.

## Envelope e qualidade

Busca válida retorna `hits: int`, `documents: list[object]` e agregações. Cada
documento aceito deve conter `id`, `instancia=2ª Instância` e
`tipoDocumento=Acórdão`; número, classe, órgão, relator, assuntos e datas são
preservados quando publicados. O detalhe deve conter `inteiroTeorHTML` para
ser considerado completo.

`hits=0` com `documents=[]` é vazio autoritativo. HTTP 403/429, timeout, TLS,
desafio ou JSON incompatível são respectivamente controle de acesso, rate
limit, transporte ou schema inválido; nenhum é vazio.

## Evidência live

Veja `docs/provider-discovery/trt8-pje-jurisprudencia-live-20260909.json` para
hashes, tamanhos, contagens, páginas 1/2 e detalhe. Nenhum corpo bruto ou token
de desafio foi persistido.

## Dados canonicos

O adapter preserva `id`, numero do processo, classe, orgao julgador, relator,
ementa, inteiro teor, datas, URL, `raw` e `SourceTrace`. Todo registro aceito e
marcado como `authority=TRT8`, `branch=labor`, `degree=second`,
`instance=second` e `collection=CJSG`. Registros fora de `2a Instancia` ou que
nao sejam `Acordao` falham explicitamente no parser.

## Estados e limites

- `hits=0` com lista vazia e vazio autoritativo;
- timeout, HTTP 403/429, TLS, desafio e schema invalido permanecem como erro
  explicito e nunca sao convertidos em vazio;
- pagina 1 e pagina 2 foram reproduzidas com filtros de segundo grau;
- o detalhe pode nao disponibilizar inteiro teor para documento sigiloso;
- a consulta e bounded e respeita o intervalo configurado por host.

## Fixtures e promocao

O contrato e coberto por fixtures sanitizadas de sucesso, segunda pagina,
vazio, bloqueio e schema invalido:

- `tests/fixtures/trt8_pje_success.json`;
- `tests/fixtures/trt8_pje_page2.json`;
- `tests/fixtures/trt8_pje_detail.json`;
- `tests/fixtures/trt8_pje_empty.json`;
- `tests/fixtures/trt8_pje_blocked.json`;
- `tests/fixtures/trt8_pje_schema_invalid.json`.

A evidencia live de 2026-09-09 confirma filtros explicitos, paginacao e
inteiro teor publico. A promocao tecnica local e permitida; release, deploy e
qualquer alteracao de producao continuam fora deste repositorio de trabalho.

## MCP

O MCP expoe o provider com o mesmo contrato e os mesmos estados de acesso. Nao
gera, resolve ou persiste desafios, tokens ou cookies.

## Proximos passos

Manter smoke live bounded periodico, observar schema drift e reavaliar o
inteiro teor quando a fonte alterar o backend. A ordem federada e deterministica
apos a consolidacao de cada onda.
