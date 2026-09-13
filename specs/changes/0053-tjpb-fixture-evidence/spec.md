# 0053 - Evidencia versionada do contrato TJPB/PJe

Status: verified
Owner: Provider Engineering, Data Quality, QA e Security

## Intencao

Eliminar a divida de evidencia do `tjpb_pje_jurisprudencia` com uma resposta
sanitizada e versionada para replay local. A fixture comprova o mapeamento do
envelope de busca, mas nao substitui a validacao live nem afirma que os dados
sinteticos pertencem ao acervo do tribunal.

## Requisitos

- REQ-001: versionar um envelope JSON minimo com `total`, `hits`, `_id`, ementa,
  numero de processo e data;
- REQ-002: exercitar a mesma funcao de parser usada pelo provider;
- REQ-003: deixar explicita a natureza sintetica da fixture e nao incluir dados
  pessoais, cookies, tokens ou corpo live;
- REQ-004: manter a semantica de pagina, identidade TJPB, URL de detalhe e
  `SourceTrace` sem alterar o contrato HTTP;
- REQ-005: atualizar dossie, source contract, catalogo e auditorias em paridade;
- REQ-006: manter desafios de acesso e ausencia de detalhe como bloqueios
  distintos, sem promover novas rotas.

## Criterios de aceite

- AC-001: o teste carrega `tests/fixtures/tjpb_pje_jurisprudencia_success.json`;
- AC-002: o parser retorna um resultado canonico com id, ementa, data e URL de
  detalhe coerentes;
- AC-003: a auditoria de fixtures deixa de classificar TJPB como divida de
  evidencia;
- AC-004: todos os testes e gates locais passam;
- AC-005: nenhuma chamada adicional em escala, deploy, push ou federacao padrao
  e autorizada por esta mudanca.

## Fora de escopo

Captura de credenciais/tokens, persistencia de respostas live, bypass de WAF ou
CAPTCHA, validacao de inteiro teor e alteracao da matriz de cobertura nacional.
