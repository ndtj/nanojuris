# SDD 0108 — dispatcher da família ePROC federal

Status: `verified`  
Owner: Provider Engineering  
Data: `2026-09-10`

## Objetivo

Materializar uma interface de família para as superfícies ePROC federais que
já possuem adapters independentes, sem transformar a família em uma busca
agregada não comprovada. O chamador deve selecionar explicitamente a
autoridade (`TNU`, `TRF2`, `TRF4` ou `TRF6`); o dispatcher delega ao adapter
específico e preserva seus limites, filtros e estados de acesso.

## Escopo

- roteamento explícito por autoridade, com aliases `TRF02`/`TRF04`/`TRF06`;
- reutilização dos adapters e do transporte compartilhado existentes;
- recuperação de detalhes somente quando o identificador contém prefixo de
  autoridade reconhecido;
- exposição de capabilities e parâmetros para diagnóstico opt-in;
- registro no runtime normal como binding explícito; a capacidade continua
  opt-in e não participa da federação agregada.

## Fora de escopo

- fan-out automático entre TNU/TRFs ou inclusão na federação padrão;
- inferência de autoridade a partir de texto ou de identificador ambíguo;
- contorno de CAPTCHA, WAF, autenticação, rate limit ou TLS;
- alteração de contratos dos adapters filhos;
- deploy, credenciais, publicação ou produção.

## Requisitos e aceite

- **REQ-001/AC-001** — ausência de `authority` é rejeitada explicitamente.
- **REQ-002/AC-002** — autoridade válida é delegada ao adapter correto sem
  duplicar parser ou transporte.
- **REQ-003/AC-003** — resultados e traces conservam `authority`, ramo,
  grau, instância, coleção e estados do adapter filho.
- **REQ-004/AC-004** — detalhe/documento só é encaminhado para identificador
  com prefixo conhecido; outros IDs são rejeitados.
- **REQ-005/AC-005** — a família é um binding runtime explícito, continua
  opt-in, não é uma fonte agregada padrão e não altera a contagem de
  superfícies sem evidência live própria.
- **REQ-006/AC-006** — testes cobrem ausência de autoridade, aliases e
  delegação por fixture.
