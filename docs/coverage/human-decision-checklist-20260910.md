# Checklist de decisões humanas — NanoJuris

Atualizado em 2026-09-10. Este arquivo transforma as pendências classificadas
como `human_review` no auditor atual em decisões objetivas. As recomendações
abaixo preservam a política já fixada: operação pública bounded, sem bypass,
sem credenciais, sem corpus pesquisável persistente e sem deploy.

## Decisões globais recomendadas

- [ ] **G1 — Escopo:** manter core e superfícies condicionais inventariados;
  TCEs, TJMs, TREs, boletins, bancos curados e informativos ficam opt-in até
  provarem os oito gates.
- [ ] **G2 — Retenção:** aprovar cache live de 10 minutos, telemetria agregada
  por 30 dias, fixtures sanitizadas e nenhum inteiro teor bruto persistido fora
  do fluxo autorizado.
- [ ] **G3 — Frequência:** aprovar intervalo mínimo de 2 segundos por provider,
  sem paralelismo no mesmo host, no máximo três páginas por sonda e respeito a
  `Retry-After`.
- [ ] **G4 — Promoção:** autorizar apenas promoção técnica local quando os oito
  gates estiverem comprovados; não autorizar release, publicação, OCI ou
  produção.
- [ ] **G5 — Contatos:** autorizar o mantenedor a enviar manualmente os pacotes
  de contato já preparados em `external-action-requests-20260907.md` e no JSON
  de 2026-09-09. Nenhum contato é enviado pelo agente.
- [ ] **G6 — Benchmark:** aceitar a amostra de 8 consultas × top 10 (80 IDs
  sanitizados), com dois julgadores independentes; divergência de 2 pontos ou
  mais recebe terceiro julgamento.
- [ ] **G7 — Ranking:** manter os gates nDCG@10 +25%, irrelevantes no top 5
  reduzidos em 50% e ≤10%, filtros explícitos 100%, identificador exato em
  primeiro e p95 <150 ms.

Recomendação: aprovar G1–G7 em conjunto. Elas não concedem autorização legal,
não alteram dados de terceiros e não permitem bypass de CAPTCHA, WAF,
Turnstile, login, TLS ou rate limit.

## Pendências humanas por pacote

| Pacote/tarefa | Decisão necessária | Recomendação |
|---|---|---|
| `0077/T62` | Rotular development/holdout e medir o benchmark | Aprovar 80 julgamentos sanitizados; manter shadow mode até os critérios passarem |
| `0086/T009` | Retenção e uso do TRT2 BASIS | Opt-in/contextual; não persistir PDFs brutos sem política aprovada |
| `0089/T036` | Licença, retenção e owner por fonte | Usar G2 e owner “mantenedor NanoJuris” provisório; exigir confirmação da fonte |
| `0089/T037` | Aprovação dos rótulos de relevância | Aprovar somente após revisão humana dupla |
| `0090/T008` | Promoção do banco de sentenças TJRJ | Manter opt-in curado; não competir com jurisprudência geral |
| `0091/T037` | Allowlist/API/exportação para fontes bloqueadas | Enviar pedidos oficiais manualmente; não tentar contornar desafios |
| `0091/T045` | Rótulos e holdout do benchmark | Aplicar G6 e registrar conflitos |
| `0091/T047` | Licença, retenção, owner e promoção padrão | Aprovar apenas fontes públicas com oito gates; demais permanecem opt-in |
| `0092/T027` | Rótulos de benchmark/holdout | Mesmo procedimento G6 |
| `0092/T029` | Licença, frequência, retenção e owner | Aplicar G2/G3; confirmar termos da fonte antes de promoção |
| `0092/T030` | Promoção padrão, release ou mudança externa | **Não autorizar agora**; produção permanece bloqueada |
| `0095/T008` | Promoção do ementário de turma recursal TJAL | Manter contextual/opt-in |
| `0095/T009` | Política de atualização do TJAL | Revisão manual periódica; sem retenção de corpo bruto por padrão |
| `0096/T010` | Retenção/atualização dos PDFs ESAMAL/TJAL | Guardar apenas metadados e hash; PDF somente em fluxo autorizado |
| `0097/T010` | Retenção/atualização do boletim EJEF/TJMG | Contextual/opt-in, com revisão de atualização definida pelo mantenedor |
| `0098/T010` | Autorizações formais, allowlist, termos e retenção | Enviar solicitação oficial; nenhum acesso privilegiado ou token compartilhado |
| `0098/T042` | Owners, termos, licença, retenção e frequência | Owner provisório: mantenedor; confirmar termos por fonte |
| `0098/T046` | Promoção padrão, release ou mudança externa | **Não autorizar release/deploy** nesta fase |
| `0098/T055` | Escopo das superfícies condicionais | Manter inventário; só promover após decisão específica e oito gates |
| `0098/T059` | Smoke federado e promoção | Autorizar apenas smoke técnico opt-in; promoção padrão depende de G4 |
| `0099/T012` | Licença/frequência/retenção para novas rotas | Solicitar confirmação oficial antes de mudar rollout |
| `0106/T009` | Promoção do TRT6 | Manter bloqueado/opt-in enquanto exigir reCAPTCHA |
| `0107/T009` | Promoção dos TRE/SJUR | Manter por UF em opt-in até paginação e documento serem provados |
| `0108/T010` | Promoção de cada EPROC federal | Decidir individualmente; nenhum agregado automático |

## Ações que dependem de resposta externa

Enviar manualmente os pacotes para Falcão-JT, TJAP, TJMA, TJRJ/TJSC (CJPG),
TJMMG, TJMSP, TRT6, TRT15, TRT2/PJe e TSE/SJUR. Cada solicitação deve pedir
rota oficial, contrato de filtros/paginação, detalhe/documento, limites de uso,
fixture ou sandbox e política de automação. As tentativas atuais continuam
classificadas como bloqueio, desafio, timeout ou contrato não comprovado; nunca
como vazio.

## Resposta recomendada do mantenedor

```text
Aprovo G1–G7 conforme recomendado; autorizo somente smoke e promoção técnica
local de fontes que passem os oito gates; mantenho boletins, bancos curados,
TCEs, TJMs, TREs e fontes sem paginação como opt-in; autorizo o envio manual
dos pedidos externos; não autorizo commit, push, release, deploy, OCI ou
alteração de produção.
```

Após a aprovação, o agente pode fechar apenas tarefas técnicas locais. Licença,
retenção, owner, relevância, escopo condicional e promoção padrão continuam
registrados como decisões humanas até haver evidência explícita.
