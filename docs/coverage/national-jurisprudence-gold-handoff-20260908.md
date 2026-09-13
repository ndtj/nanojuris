# Handoff — cobertura nacional ouro de jurisprudência

Este é o apontador operacional para o SDD 0098:
[`specs/changes/0098-national-jurisprudence-gold-coverage/`](../../specs/changes/0098-national-jurisprudence-gold-coverage/).

## Estado de partida

Snapshot observado em 2026-09-08:

- 73 fontes documentadas;
- 68 providers em runtime;
- 50 fontes na busca unificada;
- 45 fontes primárias de jurisprudência textual;
- 56 fontes com algum suporte documental;
- 25/27 autoridades estaduais com workpack completo de segundo grau;
- CJPG 8/27 e CJSG 25/27;
- 60 tarefas abertas, sendo 44 externas e 16 humanas.

Regenerar tudo antes de agir. Estes números não são uma promessa de
disponibilidade nem de legalidade.

## O que o próximo modelo deve fazer

1. Ler o prompt operacional e os artefatos do SDD 0098.
2. Selecionar um lote de uma a três superfícies.
3. Confirmar rota oficial e executar chamada bounded.
4. Implementar apenas quando contrato, grau, fixture e acesso forem provados.
5. Procurar exportações e portais oficiais alternativos antes de classificar
   uma fonte como bloqueada.
6. Regenerar inventários ao final do lote e registrar evidência.

CAPTCHA, WAF, Turnstile, login, 403, 429, timeout e TLS não são resultados
vazios. Nenhuma técnica de evasão é permitida.

## Saídas esperadas

- provider/dossiê/SDD atualizado;
- fixture sanitizada e testes;
- evidence record redigido;
- estado de superfície e promoção regenerados;
- relatório de limitações e próximo lote.

