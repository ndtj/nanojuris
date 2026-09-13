# Handoff operacional para o próximo modelo — cobertura nacional ouro

Versão: `2026-09-08`

Entrada normativa: [`SDD 0091`](../../specs/changes/0091-national-coverage-gold-handoff/)

Escopo: preparação de execução local, sem commit, publicação, deploy ou produção.

Este arquivo é um índice operacional. O SDD 0091 continua sendo a fonte normativa;
os inventários gerados continuam sendo a fonte dos números. O objetivo é permitir
que outro modelo comece a executar sem repetir a análise da conversa.

## Estado que deve ser regenerado

Comece sempre recalculando os artefatos abaixo. Os valores do snapshot de 8 de
setembro são apenas referência e não são uma declaração de cobertura concluída:

| Indicador | Snapshot | Fonte de verdade |
| --- | ---: | --- |
| fontes catalogadas | 73 | `docs/registry/provider-catalog.full.json` |
| providers em runtime | 68 | mesmo catálogo, `summary.implemented_sources` |
| fontes unificadas declaradas | 50 | mesmo catálogo, `summary.unified_search_sources` |
| superfícies nacionais | 151 / 125 obrigatórias | `docs/coverage/surface-state-registry-20260902.json` |
| CJPG comprovados | 8/27 | `docs/topology/degree-coverage-matrix-20260901.json` |
| CJSG comprovados | 25/27 | mesma matriz |
| workpacks estaduais completos | 25/27 | `docs/coverage/state-appellate-program-20260905.json` |
| tarefas abertas | 60 (0 locais, 44 externas, 16 humanas) | `docs/coverage/open-task-audit-current.json` |

## Lote local concluido nesta preparacao

Foi incorporado `tjma_informativos` como fonte oficial curada e opt-in. A fonte
lista edicoes PDF do TJMA, comprova escopo de segundo grau nos informativos e
oferece inteiro teor sob demanda; ela nao e contada como CJSG geral. O lote tem
adapter, fixture, contrato, teste de falhas, evidencia live redigida e entradas
nos inventarios. Evidencia: `docs/provider-discovery/tjma-informativos-live-20260908.json`.

Resultado do fechamento local: **1593 testes aprovados e 26 skips**; Ruff,
formatacao, mypy, compilacao, SDD e pacote executor aprovados. Os skips sao
smokes live opt-in ou dependencia opcional, nao falhas do lote.

O provider mais recente do ciclo foi `tjmg_ejef_boletim_jurisprudencia`, uma
colecao oficial DSpace de boletins EJEF/TJMG. A chamada bounded retornou dois
itens com total conhecido e o smoke federado de fonte unica confirmou os dois
registros e o PDF oficial, sem bypass. A colecao permanece curada e nao e uma
alegacao de cobertura integral do TJMG.

Regeneração mínima:

```powershell
Set-Location C:\Users\admin\Desktop\Nanojuris\repos\nanojuris
$env:PYTHONPATH = 'src'
python tools/audit_open_tasks.py
python tools/build_provider_coverage.py --write
python tools/build_provider_quality.py --write
python tools/build_provider_capability_ledger.py --write
python tools/build_fixture_completeness.py
python tools/build_degree_coverage.py
python tools/build_surface_state_registry.py
python tools/build_state_appellate_program.py --write
python tools/build_promotion_manifest.py --write
python tools/audit_0091_local_gates.py --write
```

## Ordem de leitura

### Evidencia adicional do TJRO

Na preparacao deste handoff, `tjro_jurisprudencia` foi rechecado com uma
consulta publica bounded de segundo grau e `fetch_details=True`. O resultado
PJESG teve PDF `application/pdf` de 29.618 bytes e 11.949 caracteres extraidos;
o hash SHA-256 foi registrado sem persistir o corpo bruto. A prova redigida e
`docs/provider-discovery/tjro-jurisprudencia-fulltext-live-20260908.json`.
Isso atualiza a evidencia documental do provider, mas nao fecha as duas
autoridades estaduais restantes nem autoriza release.

1. `AGENTS.md`, `specs/constitution.md`, `specs/README.md` e
   `docs/coverage/README.md`;
2. todos os arquivos de `specs/changes/0091-national-coverage-gold-handoff/`;
3. SDD 0070 (capabilities), 0077 (busca live), 0078/0080 (acesso público),
   0084 (documentos), 0089 (handoff anterior) e 0090 (banco de sentenças);
4. `docs/registry/provider-catalog.full.json`, capability ledger, registro de
   superfícies, inventário de documentos, qualidade e auditoria de tarefas;
5. dossiê, contrato, adapter, fixtures e testes do lote escolhido;
6. referência Juscraper e fonte oficial do tribunal. Juscraper é comparação
   técnica, nunca autorização nem código a ser copiado.

## Definição de ouro por superfície

Uma superfície é `authority + branch + degree + instance + collection +
document_scope`. Ela só pode ser promovida quando os oito gates forem verdadeiros:

1. fonte oficial identificada;
2. contrato específico da superfície;
3. adapter executável pelo runtime compartilhado;
4. fixtures sanitizadas de sucesso, vazio, erro/bloqueio e schema drift;
5. filtros, ordenação, paginação, identidade e semântica de vazio validados;
6. chamada live pública, pequena e reproduzível;
7. qualidade canônica, datas, provenance e documento validados;
8. smoke federado opt-in aprovado e estado técnico habilitado.

`implemented`, `live_validated`, `quality_passed`, `federation_enabled` e
`legal_status` são dimensões diferentes. Um adapter existente não fecha nenhum
gate sozinho.

## Protocolo de cobertura completa

Para cada provider, o próximo modelo deve produzir os seguintes artefatos e
testes, em vez de apenas ampliar a lista de adapters:

| Etapa | Evidência exigida |
| --- | --- |
| descoberta | URL oficial, método, payload, limites, paginação, ordenação e escopo |
| filtros | matriz `native`, `translated`, `local_postfilter`, `unsupported`, `blocked` ou `unverified` |
| identidade | autoridade, ramo, grau, instância, coleção, classe, órgão e tipo documental |
| temporalidade | julgamento, publicação, atualização e disponibilização, com granularidade |
| texto | resumo/ementa, inteiro teor, link de documento ou `not_offered`, sem inferência |
| documentos | host allowlist, redirect, MIME, magic bytes, tamanho, hash e extração |
| paginação | segunda página, cursor/offset, sobreposição, total conhecido/desconhecido |
| erros | vazio autoritativo separado de bloqueio, timeout, 403, 429, TLS e schema |
| proveniência | `raw`, `SourceTrace`, fingerprint, versão do parser e instante |
| promoção | fixture, teste focado, smoke federado, manifesto e `verification.md` |

Ausente, desconhecido, inválido e não suportado nunca são equivalentes. Consulta
processual, DataJud, catálogo, tema ou metadado contextual não conta como
jurisprudência textual geral.

## Acesso público legítimo

O limite técnico está em
[`public-access-boundary-playbook-20260908.md`](public-access-boundary-playbook-20260908.md)
e na matriz do SDD 0091. São permitidos, quando publicados pela própria fonte:

- API, exportação, RSS, sitemap, dataset, PDF/HTML/JSON/XML e download oficial;
- jornada HTTP ou navegador padrão de usuário anônimo;
- cookies/CSRF efêmeros emitidos na sessão corrente;
- redirects para hosts oficiais allowlisted;
- paginação publicada, `ETag`/`Last-Modified` e retry transitório cooperativo;
- proxy institucional fixo apenas para conectividade, sem ocultar origem;
- allowlist, ambiente de homologação ou rota fornecida pelo tribunal;
- desafio mediado manualmente pelo usuário, sem persistir token ou cookie.

CAPTCHA, Turnstile, WAF, login, 403, 429, TLS e schema inesperado são estados
explícitos. Não há “zona de sombra” operacional. É proibido solver/OCR de
desafio, stealth, spoofing de fingerprint, rotação de IP/proxy, replay de
cookies/tokens, fuzzing de endpoint privado, downgrade TLS, exaustão de limite
ou autenticação não autorizada. Uma página seguinte aparentemente acessível não
autoriza extrair token ou reproduzir uma sessão desafiada.

Classifique cada tentativa como:

```text
success_with_results | authoritative_empty | unconfirmed_empty |
access_blocked | challenge_enforced | rate_limited | timeout |
transport_error | schema_invalid | partial | cancelled
```

Após um bloqueio estável, registre uma evidência redigida uma vez, procure API,
exportação, rota oficial alternativa ou suporte/allowlist, e avance. Não repita
chamadas contra a mesma proteção.

## Ondas de execução

| Onda | Conteúdo | Regra de saída |
| --- | --- | --- |
| G0 | baseline e reconciliação | catálogo, runtime, live, qualidade e federação sem divergência |
| G1 | contrato e envelope federado | estados de total, filtros e acesso distintos |
| G2 | CJPG/primeiro grau | rota oficial textual e grau provado, sem contar processo |
| G3 | CJSG/segundo grau | 27 autoridades tratadas separadamente; bloqueios preservados |
| G4 | TRT/TST, TSE/TRE, TRF, superior, militar e eproc | contrato próprio por família |
| G5 | documentos e campos | detalhe, PDF/HTML, MIME, hash, OCR permitido e provenance |
| G6 | federação e busca web | uma chamada normal por provider, estados por fonte e ranking auditável |
| G7 | operação | smoke periódico, TTL, drift, shadow mode e rollback |
| G8 | revisão humana e release | somente após autorização explícita; fora deste handoff |

Trabalhe em lotes de um a três providers. A ordem estadual detalhada e os IDs
de tarefas estão em `provider-batch-plan.json` e `tasks.md` do SDD 0091.

## Relatório obrigatório do lote

```text
provider/superfície:
gates antes/depois:
arquivos alterados:
chamadas live (URL, método, data, classificação):
fixtures e testes:
inventários regenerados:
limitações e bloqueios externos:
próximo provider:
commit/push/deploy/produção: não realizados
```

## Condição de conclusão honesta

Só declarar cobertura nacional quando o programa gerado indicar `27/27`, todos
os workpacks estiverem sem `pending`, cada autoridade tiver fixture, contrato,
live, teste federado e qualidade, e nenhum erro externo tiver sido convertido em
vazio. Se restarem apenas bloqueios externos ou decisões humanas, entregar a
tabela de bloqueios com URL, método, data, classificação, alternativa oficial e
ação necessária; isso é uma parada legítima, não uma falsa conclusão.

Este handoff não autoriza commit, push, tag, publicação, Terraform, OCI, secrets,
IAM, deploy ou qualquer alteração de produção.
