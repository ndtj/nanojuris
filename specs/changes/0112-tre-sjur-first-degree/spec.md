# SDD 0112 — família SJUR/TRE de primeiro grau

Status: `verified`  
Owner: Provider Engineering  
Data: 2026-09-11

## Objetivo

Expor, de forma explícita e separada, as decisões de primeiro grau que o
serviço público SJUR/TRE eventualmente retorna, sem misturá-las ao adapter
`tre_sjur_jurisprudencia` de segundo grau.

## Escopo

- dispatcher por `authority=TRE-XX` para a família eleitoral de primeiro grau;
- reutilização do transporte, DSL, parser de campos e limites do SJUR/TRE;
- aceitação somente de rótulos que contenham `Sentença` ou `primeiro grau`;
- preservação de `degree=first`, `instance=first`, autoridade, trace e `raw`;
- disponibilidade apenas opt-in até que cada UF prove paginação, fixtures e
  inteiro teor.

## Fora de escopo

- inferir primeiro grau para rótulos desconhecidos;
- converter resultados de segundo grau em primeiro grau;
- contornar CAPTCHA, WAF, rate limit, login ou controles da fonte;
- federação padrão, sincronização em massa ou deploy.

## Requisitos e aceite

- **REQ-001/AC-001** — a família exige uma autoridade TRE válida e rejeita TSE,
  estados inválidos e consultas sem escopo.
- **REQ-002/AC-002** — somente rótulos explicitamente classificados como
  primeiro grau chegam ao resultado; acórdãos e rótulos desconhecidos são
  descartados com contagem no motivo de completude.
- **REQ-003/AC-003** — cada registro aceito possui `authority`,
  `branch=electoral`, `degree=first`, `instance=first`, `collection=SJUR` e
  `SourceTrace` com a rota por UF.
- **REQ-004/AC-004** — páginas remotas diferentes de 1 continuam rejeitadas
  enquanto a fonte repetir a janela; `total_known=false` e
  `is_complete=false` permanecem explícitos.
- **REQ-005/AC-005** — o cliente disponibiliza a família e os bindings por UF
  somente em modo candidato/opt-in; nenhum provider entra na federação padrão.
