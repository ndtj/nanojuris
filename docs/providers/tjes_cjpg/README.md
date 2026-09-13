# TJES CJPG (jurisprudência de primeiro grau)

Status: `implemented`, `live_validated`, `federation_enabled`.

Promotion addendum (2026-09-05): the operator approved local/federated use
after the technical contract, fixtures, quality checks and bounded live check
passed. This does not authorize deployment or redistribution. The default
federation preserves the explicit CJPG/first-degree discriminator.

O provider `tjes_cjpg` consulta exclusivamente a coleção pública `pje1g` do
Tribunal de Justiça do Espírito Santo. Ele é uma fonte de decisões de primeiro
grau (CJPG), separada de CJSG, de precedentes qualificados e de consulta
processual. Não participa da busca unificada por padrão.

## Identidade da fonte

Tribunal: Tribunal de Justiça do Estado do Espírito Santo (TJES). Coleção:
jurisprudência de primeiro grau/PJe (`pje1g`).

## Contrato observado

- Portal oficial: <https://sistemas.tjes.jus.br/consulta-jurisprudencia/>.
- Rota: `GET /consulta-jurisprudencia/api/search`.
- Parâmetros obrigatórios: `core=pje1g`, `q`, `page`, `per_page`.
- Limite remoto conservador usado pelo adapter: `per_page <= 20`.
- Filtros reproduzidos: `exact_match`, `magistrado`, `dataIni`, `dataFim` e
  `sort`.
- Resposta: objeto JSON com `docs`, `total`, `page`, `per_page` e
  `total_pages`.

Cada documento pode conter número CNJ, classe, assunto, comarca, órgão,
magistrado, data de juntada e `inteiro_teor`/`inteiro_teor_html`. A fonte não
garante uma ementa separada; quando ela não existe, o resumo canônico é um
prefixo claramente identificado do inteiro teor.

## Dados retornados

O adapter expõe os campos canônicos `case_number`, `decision_type`,
`case_class`, `subject`, `rapporteur`, `judging_body`, `origin_county`,
`judgment_date`, `summary` e `full_text`. O documento original completo e
qualquer campo futuro permanecem em `raw`.

## Uso

```python
from nanojuris import NanoJurisClient

client = NanoJurisClient()
page = client.search(
    "responsabilidade civil",
    source="tjes_cjpg",
    page=1,
    page_size=10,
)
```

O resultado inclui `SourceTrace` com URL final, status HTTP, tipo de conteúdo,
bytes, tempo e hash SHA-256. Campos desconhecidos do documento original são
preservados em `raw` para detectar evolução do schema.

## Limites e segurança

- Falhas HTTP, timeout, bloqueio e alteração de schema geram erro explícito;
  nunca são convertidas em lista vazia.
- O inteiro teor vem inline; não há rota de detalhe independente promovida.
- O adapter não contorna CAPTCHA, WAF, login ou limite de frequência.
- A disponibilidade pública não equivale a autorização de redistribuição em
  massa. A revisão jurídica/licenciamento continua um gate antes de qualquer
  coleta em escala ou promoção à federação.
- Fixtures do projeto são sanitizadas e não reproduzem o corpo live.

## Fixtures

As fixtures sanitizadas estão em:

- `tests/fixtures/tjes_cjpg_success.json` — duas decisões sintéticas, com
  ementa ausente em uma delas e campos extras;
- `tests/fixtures/tjes_cjpg_empty.json` — total remoto zero;
- `tests/fixtures/tjes_cjpg_invalid.json` — envelope sem `docs`;
- `tests/fixtures/tjes_cjpg_schema_drift.json` — chave `documents` inesperada.

Nenhuma fixture contém corpo copiado da fonte live ou dados pessoais reais.

## MCP

O provider pode ser consultado explicitamente por ferramentas que aceitem
`source="tjes_cjpg"`, sempre exibindo o trace e o estado de completude. A
capability está marcada como `supports_unified_search=True` e o provider está
habilitado no manifesto técnico local; o binding de primeiro grau permanece
separado de CJSG e erros de acesso nunca são inferidos como ausência de
resultados.

## Próximos passos

1. repetir a chamada bounded em cada ciclo de atualização;
2. monitorar schema, paginação e filtros sem aumentar a frequência;
3. manter o manifesto e o estado de acesso atualizados; deploy e publicação
   continuam fora deste ciclo.

## Evidência live

Em 2026-09-01, uma chamada pública limitada a uma página (`q=responsabilidade`,
`per_page=2`) respondeu HTTP 200 com JSON válido, dois documentos e total
declarado de 313.496 registros. O corpo foi analisado em memória; somente
metadados e hash foram usados como evidência. Execute o teste com
`NANOJURIS_RUN_LIVE=1` quando desejar repetir a verificação.
