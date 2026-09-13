# 0064 - reconciliação de épocas dos catálogos gerados

Status: verified
Owner: Provider/Data Engineering

## Intenção

Impedir que o catálogo de providers e a auditoria documental mantenham uma
data de snapshot anterior às evidências live estruturadas já versionadas.

## Requisitos

- REQ-001: o gerador de cobertura deve manter a data existente quando nenhuma
  evidência mais recente estiver disponível;
- REQ-002: evidências estruturadas com timestamp posterior devem avançar a
  data do snapshot sem acesso à rede;
- REQ-003: a auditoria documental deve usar a mesma data do catálogo operacional;
- REQ-004: a regra deve ser determinística, tolerar artefatos inválidos e não
  alterar contratos de providers;
- REQ-005: testes devem provar a reconciliação e os artefatos gerados devem
  permanecer iguais aos builders.

## Critérios de aceite

- AC-001: catálogo, auditoria e work packs usam a mesma época observada;
- AC-002: evidência posterior a um catálogo antigo atualiza o snapshot;
- AC-003: ausência ou JSON inválido não interrompe a geração;
- AC-004: testes de cobertura, documentação, work packs e topologia passam.

## Fora de escopo

Chamadas live, alteração de providers, promoção federada, publicação, deploy e
qualquer mudança de produção.
