# Especificação — cobertura nacional de jurisprudência

Status: `proposed`

## Requisitos

### Registro e identidade

- **REQ-092-001** — cada combinação tribunal, ramo, grau, instância e coleção
  deve possuir um registro canônico independente.
- **REQ-092-002** — o registro deve separar `lifecycle`, `maturity`,
  `live_status`, `contract_status`, `federation_status` e `legal_status`.
- **REQ-092-003** — evidência live deve conter data, método, status, rota
  redigida, hash opcional e `evidence_id`.

### Contrato e filtros

- **REQ-092-004** — filtros declarados devem ser classificados como remotos,
  traduzidos, locais, ignorados ou não suportados.
- **REQ-092-005** — o contrato deve distinguir total zero, total conhecido,
  total desconhecido e falha de acesso.
- **REQ-092-006** — grau, instância, ramo, coleção, tipo documental, classe,
  órgão, autoridade e datas devem ser canônicos quando disponíveis.

### Texto e documentos

- **REQ-092-007** — inteiro teor deve ser representado por referência de
  documento, MIME, magic bytes, tamanho, hash, extração e proveniência.
- **REQ-092-008** — OCR somente pode operar sobre documentos públicos permitidos;
  nunca sobre CAPTCHA, Turnstile ou páginas de desafio.
- **REQ-092-009** — ausência de texto deve ser diferente de texto indisponível,
  link condicionado e documento inválido.

### Juscraper e descoberta

- **REQ-092-010** — o Juscraper é referência de descoberta, não autorização para
  copiar código ou presumir que uma rota continua disponível.
- **REQ-092-011** — cada equivalência deve comparar endpoint, método, payload,
  seletores, filtros, paginação e semântica de grau.

### Federação e qualidade

- **REQ-092-012** — o planner deve excluir candidatos, contextuais e bloqueados
  do rollout padrão, mantendo-os visíveis no diagnóstico.
- **REQ-092-013** — ranking e deduplicação devem ser determinísticos e preservar
  diversidade apenas quando os scores forem materialmente próximos.
- **REQ-092-014** — cada lote deve ter fixtures de sucesso, vazio autoritativo,
  erro, bloqueio e drift quando aplicável.

### Acesso responsável

- **REQ-092-015** — chamadas live devem ser bounded, de baixa frequência e
  obedecer robots, termos, rate limit e instruções da fonte.
- **REQ-092-016** — nenhum agente pode resolver automaticamente desafio,
  contornar WAF/login, rotacionar IP para evasão ou usar endpoint privado.

## Critérios de aceite

- **AC-092-001** — o baseline é regenerável e não contém contagem manual.
- **AC-092-002** — uma superfície bloqueada aparece como bloqueada em todos os
  envelopes e não como lista vazia.
- **AC-092-003** — filtro sem suporte é visível no diagnóstico e não é descartado.
- **AC-092-004** — provider promovido possui runtime, contrato, fixture, live,
  qualidade, acesso público e smoke federado aprovados.
- **AC-092-005** — outro modelo consegue executar um lote somente lendo este
  pacote, 0091 e o dossiê do provider.
- **AC-092-006** — nenhuma tarefa deste pacote autoriza commit, push, release,
  deploy ou produção.
