# Registro de rodada Playwright live (template)

Use este modelo para registrar uma nova rodada autenticada do NanoJuris sem
misturar evidência de produção com fixtures offline. O runner
`repos/nanojuris-platform/tests/live_authenticated_trace.py` abre o navegador
visível; a autenticação é feita manualmente pelo operador e a aba pode ser
reutilizada durante toda a rodada.

## Identificação

- `run_id`: `YYYYMMDDTHHMMSSZ-<descricao-curta>`
- `started_at_utc` / `finished_at_utc`:
- ambiente: `production` / `staging`
- URL base (sem query, fragmento ou token):
- commit/build da plataforma:
- operador: registrar apenas identificador interno, nunca e-mail ou segredo
- evidência bruta: caminho local protegido (não anexar ao relatório público)
- resumo sanitizado: `docs/validation/runs/<run_id>.{json,md}`

## Privacidade e segurança (obrigatório)

- [ ] Nenhum cookie, token, senha, código OAuth, request ID ou cabeçalho
  sensível foi persistido.
- [ ] Queries, fragmentos e identificadores de usuário foram redigidos.
- [ ] Corpos de busca, documentos jurídicos e respostas da IA não foram
  copiados para o resumo, salvo autorização documental explícita.
- [ ] Screenshots mascaram sessão, diretório de usuários e auditoria.
- [ ] A rodada não tentou contornar CAPTCHA, WAF, robots.txt ou controle de
  acesso da fonte.

## Inventário de rotas observadas

Registre somente rotas realmente emitidas pelo navegador. Não derive endpoints
de nomes encontrados em JavaScript, documentação ou suposições.

| Método | Rota (sem query) | Finalidade | Status observado | Tentativas | Resultado |
|---|---|---|---|---:|---|
| `GET` | `/auth/login/oracle` | iniciar login Oracle | | | |
| `GET` | `/auth/callback` | concluir retorno OAuth | | | |
| `GET` | `/auth/session` | confirmar sessão | | | |
| `GET` | `/api/v1/sources` | obter catálogo | | | |
| `POST` | `/api/v1/search` | busca federada | | | |
| `POST` | `/bff/assistant` | assistente contextual | | | |
| `GET` | `/api/v1/keys` | área de chaves | | | |
| `GET` | `/api/v1/admin/access` | autorização do painel | | | |
| `GET` | `/api/v1/admin/users` | diretório administrativo | | | |
| `GET` | `/api/v1/admin/audit` | auditoria administrativa | | | |

Rotas administrativas podem possuir query de paginação ou filtro; preserve
somente a rota sem query e marque a query como redigida.

## Busca e providers

- consulta de teste (descrever semanticamente; não incluir dados pessoais):
- seleção: `all_sources` / lista explícita:
- catálogo: HTTP/status e quantidade:
- batches enviados / tamanho máximo por batch:
- providers pesquisados:
- providers com dados:
- providers vazios (somente se a resposta confirmou vazio):
- providers ignorados por capability:
- falhas classificadas por provider e tipo (`access_control`, `tls`,
  `query_rejected`, `source_unavailable`, `timeout`):
- total agregado observado (deixar claro que não é deduplicado global):

Não classifique falha de transporte ou bloqueio como resultado vazio. A lista
por provider deve ser derivada de `searched_sources`, `skipped_sources` e
`provider_errors` do envelope sanitizado.

## Paginação, reader e assistente

- página inicial e status exibido:
- página seguinte avançada: `sim` / `não` / `não aplicável`:
- reader/detalhe aberto: `sim` / `não`:
- assistente HTTP/status, tamanho da resposta e citações:
- assistente exibiu resposta completa: `sim` / `não`:

## Diagnóstico e evidências

- falhas de request do navegador:
- erros de página:
- erros de sessão:
- sinais de console agrupados por categoria:
- screenshots sanitizados e seus propósitos:
- limitações conhecidas e itens que exigem nova rodada:

## Conclusão

Descreva separadamente o que foi comprovado pela rodada, o que permaneceu
parcial/indisponível e o que não foi testado. Uma rodada live é uma fotografia
reproduzível; ela não garante disponibilidade futura dos providers nem autoriza
alterações ou deploy automático.

