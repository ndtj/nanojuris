# Verificação — TRT8 PJe

## Live bounded

Em 2026-09-09, a superfície oficial retornou `captchaOption=0`. A busca
filtrada por `dano moral`, `2ª Instância` e `Acórdão` informou 46.181 registros;
as páginas 1 e 2 retornaram 10 documentos cada. O detalhe de
`pje2_15349541` respondeu 200 com `inteiroTeorHTML`.

Evidência redigida:
`docs/provider-discovery/trt8-pje-jurisprudencia-live-20260909.json`.

## Testes

```text
python -m pytest -q tests/test_trt8_pje_jurisprudencia.py
python -m ruff check src/nanojuris/providers/trt8_pje_jurisprudencia.py tests/test_trt8_pje_jurisprudencia.py
```

Resultado local: 7 testes aprovados; lint aprovado.

## Resultados

- O endpoint oficial foi observado com `captchaOption=0` e retornou páginas
  filtradas de segunda instância e acórdãos.
- O adapter preserva `access_status`, `extraction_status`, `SourceTrace`,
  total conhecido e estados explícitos de bloqueio, timeout e schema inválido.
- O smoke direto do adapter foi revalidado em 2026-09-09: uma página com
  resultado válido foi obtida com `degree=second` e `document_type=acordao`.
- As duas primeiras tentativas do runner federado expiraram por
  `SourceUnavailableError: timeout`; elas permanecem registradas nas
  evidências redigidas existentes e não foram tratadas como vazio.
- Uma terceira chamada pública bounded, com timeout de 30 segundos, respondeu
  HTTP 200, retornou um registro válido e total conhecido. A evidência está em
  `docs/provider-discovery/trt8-pje-federated-smoke-20260909-timeout30.json`.
- O manifesto técnico foi regenerado e marcou o provider como `enabled`; a
  federação local usa o adapter por padrão, sem qualquer alteração externa.

## Rastreabilidade

| Requisito | Evidência | Estado |
| --- | --- | --- |
| Escopo de segundo grau | `instancia=2ª Instância` validado no parser e no payload | aprovado |
| Tipo acórdão | `tipoDocumento=Acórdão` validado no parser e no payload | aprovado |
| Paginação | fixtures de página 1 e 2 e evidência live redigida | aprovado |
| Inteiro teor | fixture de detalhe e endpoint oficial de detalhe | aprovado |
| Estados externos | fixtures de bloqueio/schema e exceções explícitas | aprovado |
| Federação | smoke bounded bem-sucedido; `supports_unified_search=true` | aprovado tecnicamente |

## Decisão

Adapter tecnicamente implementado e habilitado na federação local após o smoke
bounded e a regeneração do manifesto. A promoção é técnica e reversível; não
substitui revisão humana de governança nem autoriza release, deploy ou produção.
