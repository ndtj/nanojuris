# Auditoria offline de descoberta de providers

Gerado em `2026-08-28T04:38:27+00:00`. Modo: **offline-only**; rede utilizada: **não**.

## Resultado executivo

- Entradas no catálogo: **56**.
- Candidates sem provider runtime: **9**.
- Entradas de família: **1**.
- Candidates sem fixture local: **9**.
- Análises de fixtures executadas: **3**.
- Providers runtime auditados: **46**; com fixture versionada: **43**.
- Providers runtime somente com payload inline: **1**; sem evidência de fixture: **2**.

A ausência de fixture local não é tratada como `empty`: é uma lacuna de evidência. O catálogo e os status live foram apenas lidos; não foram revalidados contra a internet.

## Candidates mapeados, ainda não implementados

| Provider | Score | Dossiê | Contrato | Fixture local | Teste local | Bloqueadores | Próxima ação |
| --- | ---: | :---: | :---: | :---: | :---: | --- | --- |
| `tjrj_ejuris` | 11 | sim | sim | não | não | no_runtime_module, no_checked_in_fixture_reference, no_local_test_reference, open_documentation_items | reproduzir contrato HTTP publico e criar fixture minima; fechar checklist objetivo do dossie; rodar validacao live pequena com termo juridico padrao |
| `trf3_jurisprudencia` | 11 | sim | sim | não | não | no_runtime_module, no_checked_in_fixture_reference, no_local_test_reference, open_documentation_items | reproduzir contrato HTTP publico e criar fixture minima; fechar checklist objetivo do dossie; rodar validacao live pequena com termo juridico padrao |
| `trt2_pje_jurisprudencia` | 11 | sim | sim | não | não | no_runtime_module, no_checked_in_fixture_reference, no_local_test_reference, open_documentation_items | reproduzir contrato HTTP publico e criar fixture minima; fechar checklist objetivo do dossie; rodar validacao live pequena com termo juridico padrao |
| `falcao_jt` | 15 | sim | sim | não | não | no_runtime_module, no_checked_in_fixture_reference, no_local_test_reference | reproduzir contrato HTTP publico e criar fixture minima; rodar validacao live pequena com termo juridico padrao |
| `tjap_tucujuris` | 15 | sim | sim | não | não | no_runtime_module, no_checked_in_fixture_reference, no_local_test_reference | reproduzir contrato HTTP publico e criar fixture minima; rodar validacao live pequena com termo juridico padrao |
| `tjes_jurisprudencia` | 15 | sim | sim | não | não | no_runtime_module, no_checked_in_fixture_reference, no_local_test_reference | reproduzir contrato HTTP publico e criar fixture minima; rodar validacao live pequena com termo juridico padrao |
| `tjmg_jurisprudencia` | 15 | sim | sim | não | não | no_runtime_module, no_checked_in_fixture_reference, no_local_test_reference | reproduzir contrato HTTP publico e criar fixture minima; rodar validacao live pequena com termo juridico padrao |
| `tjrn_jurisprudencia` | 15 | sim | sim | não | não | no_runtime_module, no_checked_in_fixture_reference, no_local_test_reference | reproduzir contrato HTTP publico e criar fixture minima; rodar validacao live pequena com termo juridico padrao |
| `tjse_jurisprudencia` | 15 | sim | sim | não | não | no_runtime_module, no_checked_in_fixture_reference, no_local_test_reference | reproduzir contrato HTTP publico e criar fixture minima; rodar validacao live pequena com termo juridico padrao |

## Evidência dos providers runtime

A auditoria separa fixture versionada de payload embutido no teste. Payload inline não é promovido automaticamente a fixture: ele deve ser extraído somente quando o conteúdo já estiver versionado e sanitizado.

### Somente payload inline

- `stf_informativo`: tests/test_stf_informativo.py

### Sem fixture nem payload inline

- `tjpb_pje_jurisprudencia`
- `tjrj_eproc_jurisprudencia`

## Execução prática sobre evidência local

A camada de discovery foi executada sobre referências de fixture encontradas nos dossiers. A família eproc possui evidências locais; os nove candidates mapeados não possuem fixture referenciada no repositório.

### `eproc_jurisprudencia_federal`
- `tests/fixtures/tnu_eproc_aposentadoria.html`: 353333 bytes, classificador offline `live_valid`, 88 rotas candidatas e 2 sugestões de seletores.
- `tests/fixtures/trf2_eproc_aposentadoria.html`: 873894 bytes, classificador offline `live_valid`, 97 rotas candidatas e 2 sugestões de seletores.
- `tests/fixtures/trf6_eproc_aposentadoria.html`: 633065 bytes, classificador offline `live_valid`, 97 rotas candidatas e 2 sugestões de seletores.

## Decisão de promoção

Nenhum candidate foi promovido automaticamente. O próximo passo de cada candidate é obter uma evidência pública reproduzível e adicioná-la como fixture/HAR sanitizado, depois fechar o contrato e implementar em mudança SDD separada.

## Próxima ordem de trabalho

1. Escolher um candidate com contrato mais detalhado no dossier e obter fixture pública revisável.
2. Reexecutar este relatório para confirmar a presença da evidência local.
3. Criar parser e provider somente após fixture de sucesso, vazio/erro e detalhe quando disponível.
4. Atualizar catálogo gerado somente pelos geradores oficiais.

Relatório JSON correspondente: `docs/provider-discovery/offline-audit.json`.
