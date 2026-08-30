# Hardening da qualidade de dados

Status: `verified`

## Intenção

Tornar a entrada e a consolidação de resultados da NanoJuris auditáveis e
resistentes a registros malformados, colisões de identidade e respostas
parciais de providers.

## Escopo

- contabilizar e isolar registros que não possam ser canonicalizados;
- tornar a identidade de deduplicação determinística e consciente de fonte;
- preservar classificação explícita de sucesso, vazio, bloqueio e falha;
- ampliar testes de contrato, invariantes e regressão.

## Fora de escopo

Não inclui burlar controles de acesso, alterar credenciais, promover providers
sem evidência, alterar catálogos gerados manualmente ou publicar em produção.

## Requisitos

- **REQ-001**: uma página com registros válidos e inválidos deve manter os
  válidos, contabilizar os inválidos e registrar uma falha/quarentena auditável.
- **REQ-002**: a deduplicação deve usar identidade estável; IDs devem incluir
  a fonte, números locais devem considerar fonte/tribunal e números CNJ válidos
  podem ser compartilhados entre fontes.
- **REQ-003**: cada fonte solicitada deve aparecer exatamente em uma situação
  observável: pesquisada, ignorada por capacidade declarada ou falha com motivo.
- **REQ-004**: traces e falhas devem preservar fonte, momento, tipo de erro e
  completude sem registrar segredos ou texto jurídico integral desnecessário.
- **REQ-005**: mudanças devem manter compatibilidade das APIs públicas e ser
  cobertas por testes reproduzíveis.

## Critérios de aceite

- **AC-001**: `CollectionReport.invalid_records` reflete todos os registros
  rejeitados sem descartar os registros válidos da mesma página.
- **AC-002**: dois registros com o mesmo número local em fontes distintas não
  colidem; o mesmo ID na mesma fonte continua deduplicado.
- **AC-003**: resultados sem ID e sem número recebem chave determinística sem
  colapsar registros semanticamente distintos.
- **AC-004**: a suíte unitária, de contrato e documentação passa sem regressão.
- **AC-005**: a verificação registra limitações dos providers e não afirma
  saúde live onde houver bloqueio, TLS, rate limit ou mudança de fonte.
