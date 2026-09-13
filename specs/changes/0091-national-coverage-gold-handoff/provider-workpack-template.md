# Template de workpack por superfície

Copie este arquivo apenas quando a fonte tiver sido selecionada para um lote.
Não marque gates por inferência.

## Identidade

```yaml
surface_id: AUTH/BRANCH/DEGREE/INSTANCE/COLLECTION/DOCUMENT_SCOPE
authority:
branch:
degree:
instance:
collection:
provider:
coverage_role: primary_textual_jurisprudence | qualified_precedent | context
owner:
```

## Fonte oficial

- URL pública de entrada:
- endpoint/método:
- commit/versão da fonte observada:
- termos/robots/licença:
- data e timezone da observação:
- frequência permitida:
- alternativa oficial:

## Contrato observado

- payload e headers não sensíveis:
- paginação/cursor:
- ordenação:
- limites:
- filtros nativos:
- filtros traduzidos:
- filtros locais:
- filtros não suportados:
- campos de resultado:
- campos de detalhe:
- datas e granularidade:
- erros esperados:
- estado de acesso e total:

## Evidência live bounded

| Evidência | Método | Resultado | Estado | ID/arquivo |
| --- | --- | --- | --- | --- |
| página inicial | | | | |
| segunda página | | | | |
| vazio autoritativo | | | | |
| parâmetro inválido | | | | |
| detalhe/documento | | | | |

## Fixtures e qualidade

- [ ] sucesso sanitizado
- [ ] vazio autoritativo
- [ ] erro externo/bloqueio
- [ ] schema drift
- [ ] segunda página, se aplicável
- [ ] identidade, grau, coleção e autoridade
- [ ] datas, classe, órgão e tipo
- [ ] deduplicação e republicação
- [ ] `SourceTrace` e completude

## Gates e decisão

```yaml
runtime: false
degree_contract: pending
fixtures: pending
live_status: pending
quality_gate: pending
access_status: pending
federation_status: disabled
promotion_decision: pending
legal_status: human_review
```

## Próxima ação e parada

Descrever uma única ação. Se houver CAPTCHA, WAF, login, 403, 429, TLS ou
schema inválido, registrar a evidência uma vez, marcar o bloqueio e avançar;
não repetir nem tentar evasão.
