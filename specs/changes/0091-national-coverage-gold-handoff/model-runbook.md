# Runbook de execução para outro modelo

Este pacote é um handoff executável, não uma autorização de publicação. O
executor deve trabalhar em lotes de no máximo três providers e conservar as
alterações existentes na worktree.

## Sequência operacional

1. Execute `python tools/audit_open_tasks.py` e os geradores de inventário.
2. Leia o dossiê, contrato, implementação, fixtures e testes do provider alvo.
3. Faça no máximo uma chamada pública bounded para descoberta e uma chamada de
   confirmação quando a primeira for válida. Classifique 403, CAPTCHA, WAF,
   Turnstile, login, TLS, timeout, 429 e schema inválido como bloqueio ou falha
   explícita; nunca como vazio.
4. Atualize o contrato e implemente somente a rota oficial reproduzível.
5. Adicione fixtures sanitizadas de sucesso, vazio autoritativo, erro externo,
   schema inválido e segunda página quando aplicável.
6. Rode testes focados e os gates locais. Só depois atualize os inventários.
7. Promova tecnicamente apenas quando os oito gates do `promotion-gate.schema`
   forem verdadeiros. Aprovação jurídica, retenção e rollout continuam sendo
   decisões humanas.

Para regenerar o pacote inteiro, use também `python tools/build_surface_workpacks.py --write`,
`python tools/audit_0091_local_gates.py --write` e `python tools/build_0091_baseline.py --write`.
O primeiro comando materializa um workpack conservador para cada superfície nacional;
não promove fontes por si só.

## Proteções obrigatórias

Não resolver CAPTCHA, OCRizar desafio, contornar WAF/Turnstile, reutilizar
tokens/cookies, rotacionar IP/proxy para evadir limites, degradar TLS, acessar
rotas privadas ou reproduzir tráfego autenticado sem autorização. Se a fonte
oferecer exportação, API, allowlist ou contato oficial, registre-a como ação
externa no ledger e avance para outro provider.

## Critério de parada

Pare o provider quando o contrato estiver comprovadamente fechado, quando a
fonte estiver bloqueada de forma terminal ou quando uma decisão humana for
necessária. Não repita chamadas contra a mesma proteção. Ao final, produza
`verification.md` com comandos, hashes, classificação live, limitações e
próximo lote. Commit, push, tag, release, deploy e alterações de produção são
proibidos neste handoff.
