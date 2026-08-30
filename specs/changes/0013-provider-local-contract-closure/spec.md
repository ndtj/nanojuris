# Fechamento de contratos locais dos providers

Status: `verified`

## Intenção

Executar uma verificação reproduzível de entrada e saída para todos os
providers registrados, fechar lacunas de rotas e mapeamentos somente quando
existir evidência local, e tornar diferenças de contrato explícitas.

## Escopo

- inventário runtime/catalog/dossiê/testes/fixtures para cada provider;
- validação local de entradas, saídas canônicas, vazios e falhas;
- ajustes de adapter, fixture ou documentação quando comprovados;
- geração de relatórios sem chamadas externas.

## Fora de escopo

Não afirmar disponibilidade live, não burlar CAPTCHA/WAF/login, não inventar
rotas a partir de suposições, não editar catálogos gerados manualmente e não
publicar em produção.

## Requisitos

- **REQ-001**: cada provider runtime deve possuir contrato de entrada e saída
  verificável por fixture ou teste determinístico.
- **REQ-002**: cada rota deve declarar método, filtros, paginação, limites e
  estados de sucesso, vazio e falha quando houver evidência.
- **REQ-003**: dados canônicos devem preservar identidade, fonte, traces e
  campos ausentes sem converter bloqueios em vazio.
- **REQ-004**: lacunas sem evidência devem ser reportadas como pendentes, não
  preenchidas por inferência.
- **REQ-005**: qualquer ajuste deve manter compatibilidade e passar os gates.

## Critérios de aceite

- **AC-001**: inventário local cobre todos os providers runtime e lista lacunas.
- **AC-002**: testes de entrada/saída e estados negativos passam.
- **AC-003**: auditorias de documentação e catálogo gerado permanecem em
  paridade.
- **AC-004**: suíte, lint, compilação e SDD passam.
- **AC-005**: relatório distingue evidência local de disponibilidade live.
