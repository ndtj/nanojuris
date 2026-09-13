# 0056 - Fixture dedicada TJRJ/eproc

Status: verified
Owner: Provider Engineering, Data Quality, QA e Security

## Intencao

Remover a reutilizacao semantica de uma fixture TJSP no teste do provider
TJRJ/eproc. A nova fixture HTML e sintetica, identifica o dominio e a UF do
Rio de Janeiro e exercita o parser compartilhado sem atribuir dados de um
tribunal a outro.

## Requisitos

- REQ-001: versionar uma resposta HTML minima com card eproc, id estavel,
  processo `.8.19`, orgao, datas, magistrado e ementa;
- REQ-002: trocar somente o teste TJRJ para a fixture dedicada;
- REQ-003: preservar a identidade configurada TJRJ, URLs e SourceTrace;
- REQ-004: marcar a fixture como sintetica, sem nomes reais, cookies ou tokens;
- REQ-005: atualizar dossie, source contract, auditoria e workpack;
- REQ-006: nao alterar contrato HTTP, promocao, chamadas live ou producao.

## Criterios de aceite

- AC-001: `tests/fixtures/tjrj_eproc_jurisprudencia_result.html` e carregada no
  teste provider-especifico;
- AC-002: o parser retorna card com corte TJRJ, UF RJ, processo `.8.19` e ementa;
- AC-003: a auditoria deixa de classificar TJRJ como sem fixture;
- AC-004: suite e gates locais passam;
- AC-005: nenhuma fixture TJSP e usada para representar TJRJ.

## Fora de escopo

Captura live, novos endpoints, alteracao do parser compartilhado, inteiro teor,
WAF/CAPTCHA e reclassificacao de disponibilidade.
