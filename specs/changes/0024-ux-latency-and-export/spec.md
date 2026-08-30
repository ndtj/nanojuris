# 0024 — UX de baixa latência e exportação do Workbench

Status: `verified` (verificação local; produção não alterada)

## Intento

Reduzir a percepção de lentidão no Studio e oferecer uma exportação compatível
com Excel, sem alterar contratos de providers nem publicar infraestrutura.

## Requisitos

- REQ-001: a interface deve usar linguagem de consulta ativa (sem mencionar
  cold start, aquecimento ou despertar do servidor).
- REQ-002: o Workbench deve oferecer exportação estruturada para Excel em um
  formato que abra nativamente no Excel, além dos formatos existentes.
- REQ-003: a infraestrutura deve permitir provisioned concurrency opcional,
  desativada por padrão para não gerar custo sem autorização.
- REQ-004: resultados e erros de fontes devem manter a semântica atual.
- REQ-005: nenhuma alteração desta mudança pode executar deploy ou alterar
  produção.

## Critérios de aceite

- AC-001: estados de carregamento exibem “Consultando fontes...” ou equivalente
  e não exibem termos de cold start.
- AC-002: o botão Exportar permite baixar um arquivo `.xls` compatível com
  Excel, com consulta, fonte, identificador, título, ementa, datas e status.
- AC-003: `npm run typecheck` e `npm run build` passam.
- AC-004: Terraform valida com provisioned concurrency `NONE` (padrão) e
  `CONSTANT` com contagem válida, sem aplicar o plano.
- AC-005: testes existentes permanecem verdes ou são atualizados apenas para o
  texto de UX equivalente.

## Fora de escopo

Troca do API Gateway, mudança de provider, autoscaling destrutivo, alteração de
DNS e deploy em OCI.
