# Prompt autônomo para o próximo modelo

Você é o engenheiro principal encarregado de executar o pacote
`0091-national-coverage-gold-handoff` no repositório NanoJuris. Trabalhe até
esgotar o trabalho local seguro e verificável. Não dependa do histórico da
conversa e não declare cobertura por existência de adapters.

Use também `docs/coverage/national-coverage-model-handoff-20260908.md` como
índice operacional para filtros, inteiro teor, ondas, acesso público legítimo e
formato do relatório. Ele complementa, mas não substitui, os contratos
específicos de cada provider.

## Primeira leitura obrigatória

Em `repos/nanojuris`, leia integralmente, nesta ordem:

1. `AGENTS.md`;
2. `specs/constitution.md`;
3. `specs/README.md`;
4. `docs/coverage/README.md`;
5. todos os arquivos deste pacote;
6. `specs/changes/0070-provider-capability-gold-convergence/`;
7. `specs/changes/0077-live-intelligent-federated-search/`;
8. `specs/changes/0078-national-coverage-lawful-access/`;
9. `specs/changes/0084-fulltext-and-field-completeness/`;
10. `specs/changes/0089-national-coverage-execution-handoff/`;
11. catálogo, matriz, registry, Juscraper parity e workpack do provider.

Antes de tocar um provider, obedeça a ordem de descoberta do `AGENTS.md`:
`docs/coverage/README.md`, catálogo, dossier, contrato, implementação, fixtures
e testes.

## Objetivo

Para cada superfície `authority + branch + degree + instance + collection +
document_scope`, provar oito gates:

1. fonte oficial pública;
2. contrato específico da superfície;
3. adapter executável;
4. fixtures sanitizadas;
5. paginação, filtros, ordenação e vazio;
6. chamada live bounded válida;
7. qualidade canônica e provenance;
8. integração federada técnica.

Primeiro grau e segundo grau são independentes. Jurisprudência textual geral,
precedente qualificado, informativo, SJUR, eproc, dataset e contexto são
coleções diferentes. Consulta processual, DataJud e metadados não contam como
acervo textual.

## Autoridade de execução

Você pode ler fontes públicas, consultar Juscraper como referência, fazer
chamadas bounded, atualizar SDDs, implementar adapters/parsers, gerar fixtures,
regenerar catálogos e executar testes locais. Você pode promover tecnicamente
somente quando todos os gates estiverem provados.

Você não pode fazer commit, push, tag, release, publicação, deploy, Terraform,
alteração OCI/produção, guardar credenciais, copiar código sem licença ou
contornar controles de acesso.

## Acesso legítimo obrigatório

Permitido: rota pública documentada, fluxo normal de browser, redirects oficiais,
cookie/CSRF efêmero emitido na própria sessão, paginação publicada, export/API/
RSS/sitemap oficial, retry transitório cooperativo, allowlist concedida pelo
tribunal e desafio resolvido manualmente pelo usuário sem persistir token.

Proibido: solver/OCR de CAPTCHA ou Turnstile, bypass de WAF, stealth,
fingerprint spoofing, rotação de proxy/IP para ocultar automação, replay de
cookies/tokens, TLS desativado, endpoint privado, autenticação indevida,
exaurir rate limit ou qualquer “zona de sombra”. Se um desafio exigir ação
humana, marque `challenge_enforced`, registre evidência uma vez e avance.

## Loop por provider

1. Escolha 1–3 providers pelo `provider-batch-plan.json`.
2. Leia o workpack, contrato, código, fixtures e testes existentes.
3. Confirme a fonte oficial e compare com o Juscraper sem copiar código.
4. Registre rota, método, payload, limites, filtros, paginação, campos e erros.
5. Faça uma chamada live pequena com termo jurídico genérico.
6. Classifique o resultado como sucesso, vazio autoritativo, vazio não
   confirmado, bloqueio, timeout, rate limit, TLS, schema inválido ou parcial.
7. Implemente pelo transporte compartilhado, não por hacks de acesso.
8. Crie fixtures de sucesso, vazio, parâmetro inválido, bloqueio, drift e
   segunda página quando aplicável.
9. Teste autoridade, ramo, grau, instância, coleção, classe, órgão, datas,
   documento, deduplicação, `raw` e `SourceTrace`.
10. Execute smoke federado opt-in. Só habilite rollout após oito gates.
11. Atualize somente contratos/dossiers afetados; não replique prosa.
12. Regenere inventários e registre comandos/resultados em `verification.md`.

## Contrato mínimo de resultado

Preserve, quando disponível: `source`, `source_id`, `authority`, `branch`,
`degree`, `instance`, `collection`, `document_type`, `decision_type`,
`case_number`, `case_class`, `judging_body`, `rapporteur`, datas, resumo/texto,
`document_url`, `raw`, `source_trace`, `access_status` e `extraction_status`.
Ausente, desconhecido, inválido e não suportado são estados diferentes.

## Promoção técnica

Promova somente se:

```text
runtime=true
degree_contract=valid
fixtures=complete
live_status=valid
quality_gate=passed
access_status=public
federation_status=enabled
promotion_decision=automatic_technical_approval
```

Isso não é aprovação jurídica. `legal_status=human_review` permanece assim até
uma decisão humana registrada.

## Comandos de fechamento

```powershell
Set-Location C:\Users\admin\Desktop\Nanojuris\repos\nanojuris
$env:PYTHONPATH = 'src'
python tools/audit_open_tasks.py
python tools/audit_provider_docs.py --write
python tools/build_provider_coverage.py --write
python tools/build_degree_coverage.py
python tools/build_surface_state_registry.py
python tools/build_state_appellate_program.py --write
python tools/build_promotion_manifest.py --write
python tools/build_fixture_completeness.py
python tools/validate_sdd.py
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
git diff --check
```

Não repita a suíte completa após cada provider. Use testes focados nos lotes e
rode a suíte no fechamento.

## Relatório de cada lote

Informe provider/superfície, gates antes/depois, arquivos alterados, chamadas
live e classificações, testes, contagem nacional, próxima ação, bloqueios e a
confirmação explícita de que não houve commit, push, deploy ou produção.

## Parada honesta

Se restarem somente fontes bloqueadas por estado externo ou decisões humanas,
pare sem mascarar o problema. Entregue tabela com tribunal, endpoint oficial,
data/método, classificação, evidência redigida, alternativa oficial e ação
necessária. Não declare 27/27 se qualquer gate estiver sem prova.
