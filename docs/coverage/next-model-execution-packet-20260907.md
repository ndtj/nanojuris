# Pacote de execução para o próximo modelo — NanoJuris

> **Superseded on 2026-09-08:** use
> `specs/changes/0091-national-coverage-gold-handoff/MODEL_HANDOFF.md` and
> `GOAT_EXECUTOR_PROMPT.md` as the current entrypoint. This historical packet
> is retained for provenance; its snapshot counts must not be used as current.

**Snapshot:** 2026-09-07  
**Escopo:** cobertura nacional de jurisprudência, qualidade da busca live e
documentos, sem publicação, deploy ou alteração de produção.

Este pacote é um ponto de entrada compacto para um novo executor. Os arquivos
referenciados abaixo são a fonte de verdade; este documento não substitui os
SDDs nem autoriza qualquer contorno de controle de acesso.

## Estado verificado

| Indicador | Estado | Fonte |
|---|---:|---|
| Providers catalogados | 67 | `docs/registry/provider-catalog.full.json` |
| Providers em runtime | 62 | `docs/registry/provider-catalog.full.json` |
| Fontes federadas declaradas | 47 | `docs/coverage/matrix.md` |
| Superfícies nacionais mapeadas/obrigatórias | 150 / 125 | `docs/coverage/surface-state-registry-20260902.json` |
| Autoridades estaduais de segundo grau | 27 | `docs/coverage/state-appellate-program-20260905.json` |
| Workpacks estaduais completos (8 gates) | 25/27 | mesmo programa |
| CJPG / CJSG | 7/27 / 25/27 | `docs/coverage/degree-coverage-roadmap-20260902.md` |
| Promovíveis sem pendência | 0 | `docs/operations/provider-certification-20260907.json` |
| Testes da biblioteca | 1531 pass, 26 skips opt-in | `docs/coverage/executor-packet-20260907.md` |
| Tarefas SDD não marcadas | 44 | `docs/coverage/open-task-audit-20260907.json` |
| Classificação das tarefas | 39 externas, 5 humanas, 0 locais | mesmo arquivo |

Os skips são smoke tests live opt-in sem credenciais/ambiente e não devem ser
contados como validação live. A alegação nacional continua sendo **25/27**, e
não 27/27.

## Ordem de leitura

1. `AGENTS.md`;
2. `specs/constitution.md` e `specs/README.md`;
3. `docs/coverage/README.md` e `docs/coverage/source-of-truth.md`;
4. `specs/changes/0069-state-appellate-national-coverage/`;
5. `specs/changes/0077-live-intelligent-federated-search/`;
6. `specs/changes/0078-national-coverage-lawful-access/`;
7. `docs/coverage/public-access-boundary-playbook-20260908.md` e
   `docs/coverage/public-access-boundary-playbook-20260908.json`;
8. `specs/changes/0081-state-first-degree-expansion/`;
9. `specs/changes/0082-national-labor-electoral-families/`;
10. `specs/changes/0089-national-coverage-execution-handoff/`;
11. `specs/changes/0083-federal-superior-military-closure/`;
12. `specs/changes/0084-fulltext-and-field-completeness/`;
13. `specs/changes/0085-continuous-provider-certification/`;
14. `specs/changes/0086-trt2-basis-jurisprudencia/`, `0087-trf3-jurisprudencia-exact-process/` e
    `0088-trt2-ementario-jurisprudencia/`;
15. `docs/provider-discovery/juscraper-parity-assessment-20260906.md`,
    `juscraper-court-inventory-20260906.json` e
    `juscraper-semantic-diff-20260906.json`;

> Atualização de 2026-09-08: o gate local `first-degree-federation-gate-20260908`
> fechou T012; o auditório atual passou a 45 tarefas abertas, com 39 externas,
> 5 humanas e 1 local (T023). Consulte `open-task-audit-20260907.json`.
14. o dossiê, contrato, adapter, fixtures e testes do provider escolhido.

## Tarefas restantes e classificação

### Evidência externa obrigatória

Estas tarefas só podem ser concluídas com uma rota pública oficial
reproduzível, resposta semântica válida, fixture sanitizada e trace:

| SDD | Tarefas | Foco |
|---|---|---|
| 0069 | T07 | TJAP/TJMA e alternativas oficiais, sem CAPTCHA solver |
| 0078 | T12–T17, T19, T21–T22 | superfícies CJPG/CJSG, famílias nacionais, filtros, documentos e validação semântica |
| 0081 | T03–T06 | primeiro grau estadual e gates de promoção |
| 0082 | T02, T04 | TRT/TST/TSE/TRE com autoridade e grau comprovados |
| 0083 | T04 | detalhe, documentos e temporalidade federal/superior/militar |
| 0084 | T02, T04–T05 | filtros, paginação, MIME, PDF, OCR permitido e ligação documental |
| 0087 | T008 | rechecagem live do TRF3; a tentativa de 2026-09-07 expirou por timeout |

### Revisão humana

- `0077 T62`: rótulos independentes de relevância, calibração em
  development e avaliação holdout;
- `0086 T009`: retenção e uso operacional do TRT2 BASIS.

Não fabrique rótulos, aprovação legal ou autorização de retenção no código.

## Fila de providers

### Candidatos ainda sem contrato operacional completo

`falcao_jt`, `tjap_tucujuris`, `tjse_jurisprudencia`,
`trt2_pje_jurisprudencia`.

### Família não executável como provider individual

`eproc_jurisprudencia_federal`. A família só deve ser materializada por
tribunal quando houver contrato público específico, parser, paginação,
fixtures e prova de grau.

### Trabalho recente que permanece conservador

- `trf3_jurisprudencia`: adapter opt-in de processo exato, sem federação padrão;
  a rechecagem direta teve `transport_error/timeout`;
- `trt2_ementario_jurisprudencia`: adapter opt-in para ementário oficial de
  segundo grau; a primeira navegação bounded respondeu com índice/tópico válidos,
  e tentativas posteriores foram classificadas como `partial/access_controlled`
  pelo CloudFront, sem bypass;
- `tjmg_jurisprudencia`: usar a API JSON oficial moderna; o formulário legado
  com CAPTCHA continua fora do runtime automatizado;
- `tjrj_ejuris`, `tjse_boletim_jurisprudencia` e TST têm evidências live úteis,
  mas ainda dependem dos gates de família, qualidade ou revisão definidos nos
  SDDs.

### Bloqueios que devem permanecer explícitos

TJAP/Tucujuris (Turnstile), TJMA/JurisConsult (reCAPTCHA), TJSP/CJSG,
TJCE/TJPE em rotas de transporte, TRF3 quando o transporte oficial expirar,
e qualquer fonte que requeira autenticação ou desafio humano. Bloqueio,
timeout, TLS, WAF, 403, 429 e schema inválido nunca são `authoritative_empty`.

## Oito gates de promoção

Um provider só pode ser promovido tecnicamente quando todos forem verdadeiros:

```text
fonte oficial
contrato específico de autoridade/grau/coleção
adapter executável
fixtures de sucesso, vazio, erro, bloqueio e drift
paginação/filtros/identidade validados
chamada live bounded válida
qualidade canônica e documento aprovados
federação habilitada e trace completo
```

O estado de acesso, o estado legal e a promoção técnica são dimensões
independentes. `live_validated` não significa `federation_enabled`.

## Playbook de acesso público permitido

1. Abrir a página oficial e seguir somente a navegação normal.
2. Usar uma consulta pequena, de baixa frequência e bounded.
3. Aceitar apenas cookies/CSRF emitidos pela própria sessão efêmera.
4. Executar Chromium padrão, sem stealth, spoofing ou fingerprint customizado.
5. Reproduzir somente XHR/fetch/GraphQL/BFF observados no fluxo público.
6. Seguir redirects apenas para hosts oficiais allowlisted.
7. Tentar HTTP/1.1 como compatibilidade, mantendo TLS e certificados
   verificados.
8. Usar retry apenas para falhas transitórias documentadas, com backoff,
   jitter, rate limit por fonte e limite de bytes.
9. Consultar APIs, exports, feeds, catálogos, ementários e downloads que a
   própria autoridade publique.
10. Seguir o link de detalhe/documento devolvido pela fonte e validar host,
    MIME, magic bytes, tamanho, hash e extração.

O documento completo está em
`specs/changes/0078-national-coverage-lawful-access/legitimate-techniques.md`
e `access-policy.md`.

## Técnicas proibidas

Não usar solver/OCR de CAPTCHA, extração ou replay de token, cookie importado,
stealth, spoofing de fingerprint, rotação de proxy/IP/ASN/User-Agent para
evitar bloqueio, distribuição para contornar rate limit, downgrade TLS,
credenciais não autorizadas, enumeração agressiva, fuzzing, exploração de
falha ou acesso a áreas autenticadas/sigilosas. Não insistir repetidamente na
mesma proteção estável.

Se o desafio aparecer mas o fluxo normal prosseguir sem token humano e
retornar jurisprudência válida, classificar como `challenge_incidental` e
registrar a observação. Se exigir token, interação humana ou sessão
autenticada, classificar `challenge_enforced`/`access_blocked` e avançar.

## Checklist por provider

Para cada lote de um a três providers:

1. ler o dossiê atual e a referência Juscraper;
2. descrever endpoint, método, payload, paginação, filtros, limites, erros,
   campos canônicos, `raw`, documentos e risco;
3. fazer uma chamada pública bounded e salvar evidência redigida;
4. classificar sucesso, vazio autoritativo, vazio não confirmado, bloqueio,
   timeout, rate limit, TLS, transporte ou schema inválido;
5. implementar pelo transporte compartilhado;
6. criar fixtures de sucesso, vazio, parâmetro inválido, bloqueio, drift e
   segunda página quando aplicável;
7. testar filtros remotos, traduzidos, locais e não suportados;
8. validar `authority`, `branch`, `degree`, `instance`, `collection`,
   identidade, datas, URL, documento e `SourceTrace`;
9. verificar sobreposição entre páginas e deduplicação;
10. executar smoke federado opt-in;
11. regenerar catálogos, ledgers e matrizes;
12. promover apenas se todos os gates passarem.

## Comandos de fechamento do lote

```powershell
cd C:\Users\admin\Desktop\Nanojuris\repos\nanojuris
$env:PYTHONPATH = 'src'
python tools/audit_provider_docs.py --write
python tools/build_provider_coverage.py --write
python tools/build_provider_quality.py --write
python tools/build_provider_capability_ledger.py --write
python tools/build_document_capability_inventory.py --write
python tools/build_degree_coverage.py
python tools/build_surface_state_registry.py
python tools/build_state_appellate_program.py --write
python tools/build_promotion_manifest.py --write
python tools/validate_sdd.py
python tools/audit_open_tasks.py
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
git diff --check
```

Depois de qualquer mudança no catálogo/qualidade, a ordem `quality` antes do
`capability_ledger` evita hashes obsoletos. Nunca apagar artefatos gerados para
“limpar” a worktree.

## Critério de conclusão

Só declarar cobertura nacional concluída quando o programa gerado apresentar:

```text
summary.authorities == 27
summary.complete_8_of_8 == 27
summary.incomplete == 0
summary.coverage_claim == "27/27"
open_tasks == 0
```

Além disso, cada tribunal precisa de fixture, contrato, chamada live, teste
federado e ausência de erro externo mascarado como vazio. Se restarem somente
bloqueios externos ou decisões humanas, emitir relatório de bloqueio com URL,
data, método bounded, classificação, evidência redigida, alternativas oficiais
avaliadas e ação necessária.

## Limites operacionais

Este pacote não autoriza commit, push, tag, publicação, release, alteração de
OCI, Terraform apply, secrets, IAM ou deploy. Preservar a worktree existente;
não usar `git reset --hard`, `git checkout --` ou limpeza destrutiva.
