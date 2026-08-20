# Constituição de Engenharia do NanoJuris

Status: `accepted`
Versão: `1.0`
Escopo: aplicação, providers, Studio, MCP, dados e operação.

Esta constituição define os princípios que agentes e pessoas devem preservar.
Uma mudança que precise quebrar um princípio deve registrar uma exceção,
justificativa, risco, prazo de revisão e aprovação humana.

## Artigo 1 — Contrato antes do código

Toda mudança não trivial começa por uma especificação versionada com escopo,
comportamento esperado, casos de erro, critérios de aceite e fora de escopo.
Prompts não substituem artefatos persistentes.

## Artigo 2 — Evidência antes de afirmação

Nenhum provider é considerado saudável porque respondeu uma vez. Resultados,
vazios, bloqueios, CAPTCHA, WAF, login, timeout, TLS e mudança de fonte devem
ser classificados explicitamente, preservando provenance e extraction trace.

## Artigo 3 — Fonte pública com uso responsável

O sistema consulta apenas conteúdo público permitido. Não burlar CAPTCHA, WAF,
login, rate limit, segredo de justiça ou controle de acesso. Falha de acesso
deve ser observável e não pode virar silenciosamente `zero_results`.

## Artigo 4 — Canonicalidade e rastreabilidade

Dados normalizados devem preservar identidade, fonte, URL, momento de consulta,
campos brutos relevantes, completude e motivo de ausência. A normalização nunca
deve apagar evidência necessária para auditoria.

## Artigo 5 — Segurança e minimização

Segredos ficam fora do Git. Fixtures e logs devem minimizar dados pessoais.
Permissões seguem menor privilégio. Acesso administrativo, publicação, mudança
de produção e operação destrutiva exigem autorização humana explícita.

## Artigo 6 — Qualidade verificável

Cada comportamento relevante deve possuir teste apropriado: unitário,
contrato, integração, E2E ou validação live bounded. A suíte deve cobrir também
falhas e estados incompletos, não apenas o caminho feliz.

## Artigo 7 — Operação reproduzível

Build, configuração, deploy, rollback e restauração devem ser reproduzíveis.
Infraestrutura deve ser declarativa e separada da aplicação. Estado e secrets
não pertencem ao repositório público.

## Artigo 8 — Agentes com limites

Agentes devem operar por fases (`inspect`, `plan`, `apply`, `release`), com
ferramentas allowlisted e escopo mínimo. Um agente implementador não é a única
autoridade de revisão. Toda conclusão deve apontar artefatos e comandos de
verificação.

## Artigo 9 — Compatibilidade explícita

Mudanças públicas devem declarar compatibilidade, migração, versionamento,
rollback e impacto em CLI, MCP, Studio, fixtures, documentação e distribuição.

## Artigo 10 — Simplicidade com caminho de evolução

Escolher a menor arquitetura que satisfaça os requisitos atuais, sem bloquear
alta disponibilidade, banco externo, workers ou múltiplos ambientes futuros.

## Definition of Done

Uma mudança só está concluída quando:

- sua especificação foi aceita;
- o design e as decisões estão registrados;
- tarefas foram executadas ou justificadamente descartadas;
- testes e validações passaram;
- documentação e artefatos gerados foram sincronizados;
- riscos e limitações estão registrados;
- `verification.md` contém evidência reproduzível.
