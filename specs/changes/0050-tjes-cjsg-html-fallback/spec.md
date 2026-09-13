# 0050 - Fallback HTML do TJES/CJSG

Status: verified
Owner: Provider Engineering, Data Quality, QA e Security

## Intencao

Evitar perda de ementa ou inteiro teor quando a API publica do TJES/CJSG
entregar apenas os campos HTML (`ementa_html`/`acordao_html`). O fallback deve
continuar separado do CJPG, preservar o valor original em `raw` e nunca
transformar bloqueio ou erro em resultado vazio.

## Requisitos

- REQ-001: preferir `ementa` e `acordao` planos quando forem textos utilizaveis;
- REQ-002: usar os campos HTML correspondentes somente quando o campo plano
  estiver ausente ou vazio;
- REQ-003: remover markup e decodificar entidades HTML sem apagar os campos
  originais de `raw`;
- REQ-004: manter `ExtractionStatus.COMPLETE` quando houver texto primario
  recuperado pelo fallback, e `PARTIAL` quando nenhum texto existir;
- REQ-005: preservar o contrato `core=pje2g`, `collection=second_degree` e os
  tratamentos atuais de HTTP, schema drift e identidade;
- REQ-006: cobrir o comportamento com fixture sanitizada e teste deterministico.

## Criterios de aceite

- AC-001: documento com `ementa_html`/`acordao_html` e campos planos vazios gera
  `summary`/`full_text` sem tags HTML;
- AC-002: documento com campos planos presentes nao sofre alteracao de valor;
- AC-003: `raw` conserva os campos HTML e registra a origem do fallback;
- AC-004: todos os testes existentes e gates locais passam;
- AC-005: nenhuma chamada adicional em escala, deploy ou federacao padrao e
  autorizada por esta mudanca.

## Fora de escopo

Rota de detalhe, novos cores TJES, CJPG, consulta processual, redistribuicao em
escala e alteracao de status juridico/licenciamento.
