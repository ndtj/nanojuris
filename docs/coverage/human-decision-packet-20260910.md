# Pacote de decisões humanas — NanoJuris

Data: 2026-09-10  
Responsável indicado: mantenedor NanoJuris

Este documento consolida as tarefas classificadas como `human_review` no
`open-task-audit-current.json`. As tarefas repetidas em vários SDDs são
referenciadas por decisão; uma resposta do mantenedor pode ser aplicada a
todas as referências, mas não é registrada automaticamente como aprovação.

## Como responder

Copie a seção **Decisão do mantenedor** para um registro assinado ou altere-a
com a data, nome e observações. Depois, atualize os SDDs referenciados e rode
os geradores de inventário. Não marque uma tarefa como concluída apenas por
existir uma recomendação.

## D1 — Rótulos de relevância e holdout

**Abrangência:** 0077/T62, 0089/T037, 0091/T045, 0092/T027.  
**Artefato:** `docs/benchmarks/live-ranking-review-matrix-20260909.md`.

**Recomendação:** aprovar a amostra de 80 linhas (8 consultas × top 10) com
dois revisores independentes, escala 0–3. Adicionar um terceiro revisor apenas
quando a diferença absoluta for pelo menos 2. Separar desenvolvimento e
holdout; não calibrar pesos no holdout. Registrar o nome/identificador dos
revisores e a data, sem armazenar texto identificável de usuário.

**Você precisa decidir:** quem são os dois revisores e se a amostra é
representativa. A aprovação deve ser explícita; pré-rótulos do agente não
contam como julgamento humano.

**Decisão do mantenedor:** `pendente`  
Revisores: `________________`  Data: `____/____/______`  Assinatura: `________________`

## D2 — Licença, retenção, frequência e owner por fonte

**Abrangência:** 0089/T036, 0091/T047, 0092/T029, 0098/T010 e T042,
0095/T009, 0096/T010, 0097/T010, 0099/T012.

**Recomendação padrão de baixo risco:**

- owner técnico: mantenedor NanoJuris;
- cache live efêmero: 600 segundos;
- telemetria agregada: 30 dias;
- nenhum corpus pesquisável persistente e nenhum inteiro teor bruto fora do
  fluxo autorizado;
- no máximo uma requisição por provider a cada 2 segundos, sem paralelismo no
  mesmo host, até três páginas por sonda;
- respeitar `Retry-After`, robots, termos publicados e limites do tribunal;
- fixtures sanitizadas, sem credenciais, cookies ou tokens;
- registrar licença/termos como `unknown` até haver fonte oficial ou decisão
  humana; não inferir permissão a partir de HTTP 200.

**Você precisa decidir:** confirmar que o owner é o mantenedor, aprovar a
retenção acima e preencher eventuais restrições específicas de cada fonte.

**Decisão do mantenedor:** `aprovar política padrão; revisar exceções por fonte`  
Owner: `________________`  Data: `____/____/______`  Exceções: `________________`

## D3 — Coleções curadas e fontes especializadas

**Abrangência:** 0090/T008, 0095/T008, 0098/T055.

**Recomendação:** manter bancos de sentenças, boletins, ementários, SJUR/TRE,
TCEs, TJMs e fontes contextuais como `opt_in`/`curated_context` até que cada
superfície prove busca textual, contrato, paginação, documento e os oito gates.
Elas podem ser consultadas explicitamente, mas não competem no rollout padrão
com jurisprudência geral.

**Você precisa decidir:** confirmar se alguma coleção deve entrar no padrão
antes dos oito gates. A recomendação é **não**.

**Decisão do mantenedor:** `manter opt-in/contextual`  Data: `____/____/______`

## D4 — Contatos e ações externas

**Abrangência:** 0091/T037 e 0098/T010; fontes bloqueadas e sem contrato
limitado, incluindo Falcão, TJAP, TJMA, TJRJ/TJSC, TJMMG e outras listadas em
`docs/coverage/external-action-requests-20260909.json`.

**Recomendação:** preparar os pedidos, mas não enviar automaticamente. Cada
pedido deve solicitar apenas rota pública documentada, API/export, allowlist,
limite de frequência ou esclarecimento de termos. Não solicitar remoção de
CAPTCHA, WAF, Turnstile, login ou outro controle.

**Você precisa decidir:** autorizar o envio manual dos pacotes e informar o
canal/contato de cada tribunal. Sem essa ação externa, a tarefa permanece
`external_source` e o provider continua bloqueado ou em descoberta.

**Decisão do mantenedor:** `preparar; envio manual ainda não autorizado`  
Autorização para envio: `sim / não`  Data: `____/____/______`

## D5 — Promoção técnica e federação padrão

**Abrangência:** 0091/T047, 0092/T030, 0098/T046 e T059.

**Recomendação:** promover automaticamente apenas providers com runtime,
contrato de grau/coleção, fixtures, live bounded válido, qualidade, acesso
público e trace comprovados. A promoção altera apenas o manifesto/federação
local; não autoriza release, produção ou aprovação jurídica. Candidatos,
bloqueados, `live_not_federated` e fontes contextuais ficam fora do rollout
padrão.

**Você precisa decidir:** confirmar essa separação entre aprovação técnica e
aprovação jurídica/operacional. A recomendação é **aprovar**.

**Decisão do mantenedor:** `aprovar promoção técnica local; produção bloqueada`  
Data: `____/____/______`  Observações: `________________`

## D6 — Release, deploy, OCI e alteração externa

**Abrangência:** 0092/T030 e qualquer tarefa que mencione publicação, release,
deploy, allowlist ou mudança de produção.

**Recomendação:** não autorizar nesta etapa. Manter tudo local até que o
benchmark atinja os critérios, os bloqueios externos tenham responsável, as
políticas de retenção/licença estejam registradas e o smoke de staging passe.

**Você precisa decidir:** emitir uma autorização explícita futura para
commit/push/release/deploy/OCI. Sem essa autorização, o agente não executará
essas ações.

**Decisão do mantenedor:** `não autorizar agora`  Data: `____/____/______`

## Mapa de fechamento

| Decisão | Resultado recomendado | Pode ser automatizada? |
|---|---|---|
| D1 Rótulos | Aprovar matriz de 80, dois revisores e holdout separado | Não |
| D2 Retenção/licença | Aprovar política conservadora e preencher exceções | Não |
| D3 Curadas | Manter opt-in/contextual | Sim, como regra técnica; confirmação do escopo é humana |
| D4 Contatos | Apenas preparar; envio manual | Não |
| D5 Promoção | Habilitar localmente após oito gates | Parcialmente; aprovação legal continua humana |
| D6 Release/deploy | Manter bloqueado | Não |

## Estado atual após estas decisões

Enquanto as seis decisões não forem registradas com data e responsável, é
correto manter as tarefas humanas abertas. Isso não bloqueia o trabalho técnico
local: adapters, fixtures, testes, inventários e rechecagens públicas bounded
podem continuar. Bloqueios HTTP 403/429, CAPTCHA, WAF, Turnstile, TLS, timeout
ou schema inválido continuam estados explícitos e nunca são convertidos em
vazio.

Nenhum commit, push, release, deploy, Terraform apply ou alteração de produção
faz parte deste pacote.
