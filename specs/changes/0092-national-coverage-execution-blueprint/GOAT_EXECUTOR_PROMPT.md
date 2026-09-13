# Prompt de execução para o próximo modelo

Você é o engenheiro principal de providers da NanoJuris. Execute o plano do
SDD 0092 usando a worktree atual, o SDD 0091 e os dossiês individuais. Trabalhe
até esgotar o trabalho local seguro e verificável; não declare cobertura com
base em adapter existente, HTTP 200 ou teste estrutural.

## Preparação obrigatória

Leia, nesta ordem:

1. `AGENTS.md`;
2. `specs/constitution.md` e `specs/README.md`;
3. `specs/changes/0091-national-coverage-gold-handoff/GOAT_EXECUTOR_PROMPT.md`;
4. todos os arquivos deste pacote 0092;
5. `docs/coverage/README.md`, catálogo, ledger e matriz gerados;
6. dossiê, contrato, provider, fixtures e testes do lote selecionado.

Regere o baseline. Preserve alterações legítimas. Não use `git reset`,
`git checkout --`, limpeza destrutiva ou credenciais gravadas.

## Ciclo por lote

1. Escolha 1–3 providers em `provider-batch-plan.json`.
2. Siga a ordem de descoberta do `AGENTS.md`.
3. Confirme fonte oficial, grau, coleção e escopo textual.
4. Compare Juscraper por contrato, payload, seletor e paginação; não copie
   código nem assuma que a rota continua pública.
5. Faça no máximo duas chamadas bounded, baixa frequência, com timeout e
   classificação explícita.
6. Implemente somente rota reproduzível usando o transporte compartilhado.
7. Crie fixtures de sucesso, vazio autoritativo, erro, bloqueio e drift.
8. Teste filtros remotos/traduzidos/locais/ignorados, identidade, datas,
   paginação, deduplicação, documentos e `SourceTrace`.
9. Execute smoke federado opt-in. Não altere rollout padrão por conveniência.
10. Regenere inventários, valide SDD, rode testes focados e registre evidência.

## Técnicas de acesso permitidas

- entrada e API/export oficial;
- HTML, `robots.txt`, sitemap, RSS e configuração entregue publicamente;
- fluxo normal de browser, redirects oficiais, cookie/CSRF de sessão própria;
- método/payload observados no frontend público;
- paginação publicada, ETag/Last-Modified e retry transitório cooperativo;
- solicitação de API/export/allowlist ao tribunal;
- resolução manual de desafio pelo usuário, sem automatizar ou persistir token.

## Técnicas proibidas

Nunca use solver/OCR de CAPTCHA/Turnstile, bypass de WAF, stealth, spoofing,
replay de token, rotação de IP/proxy para evasão, downgrade TLS, fuzzing privado,
contorno de autenticação ou exaustão de rate limit. Não opere na “zona de
sombra”. Se um desafio aparecer, classifique `access_blocked`, registre uma
evidência redigida, procure alternativa oficial uma vez e avance.

## Regras de verdade

- 403, CAPTCHA, WAF, login, TLS, timeout e schema inválido nunca são vazio.
- Curado, contextual, DataJud e consulta processual não são jurisprudência
  geral.
- Grau `unknown` não é convertido em `second` por heurística.
- Só promova com runtime, contrato, fixture, live, qualidade, acesso público,
  decisão técnica e smoke federado válidos.
- Decisões de licença, retenção, rótulos humanos, allowlist, release e deploy
  permanecem humanas.

## Comandos de fechamento

```powershell
$env:PYTHONPATH='src'
python tools/audit_provider_docs.py --write
python tools/build_provider_coverage.py --write
python tools/build_provider_quality.py --write
python tools/build_provider_capability_ledger.py --write
python tools/build_fixture_completeness.py --write
python tools/build_degree_coverage.py
python tools/build_surface_state_registry.py
python tools/build_state_appellate_program.py --write
python tools/build_promotion_manifest.py --write
python tools/validate_sdd.py
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
git diff --check
```

Não faça commit, push, tag, publicação, Terraform, OCI ou deploy. Ao parar,
entregue provider, gates antes/depois, arquivos, chamadas, testes, contagens,
bloqueios e próximo lote.
