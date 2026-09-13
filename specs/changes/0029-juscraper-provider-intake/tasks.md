# Tarefas

- [x] T01 - gerar inventario automatico de classes, metodos e superficies do snapshot fixado.
- [x] T02 - criar ledger de licenca e atribuicao.
- [x] T03 - cruzar 25 CJSG, 3 CJPG e 1 detalhe com catalogo e topologia 0036.
- [x] T04 - comparar cada superficie em campos, filtros, identidade, erro, paginacao e acesso.
- [x] T05 - selecionar candidatos por ganho e risco.
- [x] T06 - produzir spikes sem exposicao publica; smoke/recheck bounded e
  inventário diferencial foram registrados sem persistir corpos.
- [x] T07 - executar equivalencia, seguranca e regressao; matriz semantica, auditoria de reuso e testes diferenciais foram executados sem copiar codigo.
- [x] T08 - abrir pacotes por collection/provider aprovado e documentar bloqueados/rejeitados; SDDs 0041-0049 e ondas subsequentes registram o resultado.
- [x] T09 - atualizar delta quando o HEAD upstream mudar, sem promocao automatica.
- [x] T10 - reconciliar equivalencias por superficie com runtime/live atuais e
  impedir que adapters bloqueados sejam classificados como cobertura.

Dependencia: T01 -> T02 -> T03 -> T04 -> T05 -> T06 -> T07 -> T08 -> T09 -> T10.

Evidencia T04: `docs/provider-discovery/juscraper-semantic-diff-20260901.json`
e `.md` cobrem 29 pacotes e 87 superficies, separando dimensoes de campos,
filtros, paginacao, erros, acesso e identidade. A evidencia e estatica e nao
substitui equivalencia de parser ou chamada live.
