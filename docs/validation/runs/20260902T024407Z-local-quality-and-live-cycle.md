# Ciclo local de qualidade e validação live — 2026-09-02

## Escopo

Rodada exclusivamente local e de chamadas públicas limitadas. Nenhum commit,
push, plan/apply ou deploy foi executado.

## Alterações verificadas

- Scorecard offline para 59 entradas (50 runtime), com nove dimensões e pesos
  explícitos; 30 entradas atingem tier técnico gold, 16 silver, 4 bronze e 9
  permanecem mapped. Não há lacunas críticas no runtime nesta rodada.
- Golden set sanitizado com oito cenários: sucesso, vazio explícito, parcial,
  erro, timeout, controle de acesso, rate limit e mudança de schema.
- Invariantes canônicas em `nanojuris.quality`: identidade, SourceTrace,
  datas, URLs, texto sem HTML cru e duplicidades.
- Retry seguro: operações não idempotentes não são repetidas; Retry-After tem
  limite; jitter é injetável e determinístico em testes.
- Catálogo aponta para o scorecard e o CI valida o relatório sem rede.

## Resultados

| Verificação | Resultado |
| --- | --- |
| Suíte offline | 1.053 passed, 12 skipped |
| Cobertura | 85,34% (gate mínimo 85%) |
| Suíte live completa (variáveis públicas habilitadas) | 1.064 passed, 1 skipped |
| Live focado dos providers alterados/relevantes | 48 passed em 5,47 s |
| Ruff check/format | passed |
| Mypy (`src`) | passed, 104 arquivos |
| SDD | passed |
| Build sdist/wheel | passed (`nanojuris-0.4.0`) |
| Twine check | passed |
| Limite de pacote | passed (213.073 / 300.000 bytes estáticos) |
| Plataforma | 143 passed; lint/format/mypy passed |
| Infraestrutura | Terraform validate, SDD (37) e guardrails passed |

## Interpretação live

As 59 entradas não foram todas chamadas nesta rodada: a suíte live só consulta
rotas públicas cobertas por testes opt-in. Os estados access-controlled,
blocked-access, blocked-transport e source-unavailable permanecem explícitos;
nenhum erro foi convertido em lista vazia.

## Bloqueios que permanecem

Ainda dependem de decisão ou autoridade externa: aceite humano de tiers,
licenciamento/termos de cada tribunal, contratos de rotas candidatas, CAPTCHA,
WAF, login/SSO, credenciais de CI, revisão de release e qualquer deploy OCI.
Os pacotes SDD mantêm essas tarefas abertas e não são falsamente marcados como
concluídos.
