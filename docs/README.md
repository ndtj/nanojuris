# Documentação NanoJuris

Esta é a porta de entrada para a documentação técnica e operacional do
NanoJuris. O projeto separa claramente **usar**, **entender**, **expandir** e
**governar** a biblioteca.

## 1. Usar

| Necessidade | Documento |
| --- | --- |
| Instalar e fazer a primeira busca | [Quickstart](quickstart.md) |
| Consultar pelo terminal | [Quickstart: CLI](quickstart.md#use-a-cli) |
| Conectar um agente de IA | [MCP local](mcp.md) |
| Salvar e exportar pesquisas | [Armazenamento](storage.md) |
| Carregar e auditar inteiro teor | [Documentos](documents.md) |
| Escolher uma fonte | [Capacidades por fonte](source-capabilities.md) |
| Ver implementação, validação e evidência live | [Status das fontes](provider-status.md) |

## 2. Entender

| Tema | Documento |
| --- | --- |
| Visão das camadas | [Arquitetura](architecture.md) |
| Aquisição, parsing e evidência | [Pipeline de extração](extraction-pipeline.md) |
| Contrato de dados dos providers | [Contratos de fonte](source-contracts/README.md) |
| Pesquisa federada e cobertura | [Mapa de cobertura](provider-coverage-map.md) |
| Estado operacional e limites de acesso | [Status das fontes](provider-status.md) |
| Limites e uso responsável | [Uso responsável](responsible-use.md) |

## 3. Expandir

| Tarefa | Documento |
| --- | --- |
| Criar um provider | [Desenvolvimento de providers](provider-development.md) |
| Mapear uma nova rota | [Playbook de mapeamento](route-mapping-playbook.md) |
| Ler o contrato de uma fonte | [Dossiês por provider](providers/README.md) |
| Consultar o catálogo para humanos e IA | [Registry JSON](registry/providers.json) |
| Ver a fila de implementação | [Fila de providers](provider-development-queue.md) |
| Consultar o template de dossiê | [Template](provider-dossier-template.md) |

## 4. Governar

| Tema | Documento |
| --- | --- |
| Manutenção e autoria | [MAINTAINERS](../MAINTAINERS.md) |
| Decisões do projeto | [Governança](../GOVERNANCE.md) |
| Reportar vulnerabilidades | [Segurança](../SECURITY.md) |
| Contribuir | [CONTRIBUTING](../CONTRIBUTING.md) |
| Preparar uma release | [Checklist de release](release-checklist.md) |
| Preparar a transferência institucional | [Checklist GitHub](github-transfer-checklist.md) |

## Como ler um provider

Cada provider possui um dossiê próprio em
`docs/providers/<source-id>/README.md`. O dossiê deve permitir que uma pessoa
ou um agente responda, antes de executar uma busca:

- qual é a fonte oficial e qual é o limite de acesso público;
- quais rotas, métodos, parâmetros e filtros foram observados;
- quais campos são extraídos e como são normalizados;
- como a fonte responde a sucesso, vazio, erro, timeout e bloqueio;
- quais fixtures sustentam o parser;
- o que ainda não foi comprovado.

O [registry](registry/providers.json) é a referência machine-readable de status,
capabilities e links. Um dossiê de candidato é evidência de pesquisa, não uma
promessa de que o provider já está disponível em runtime.

## Evidência e atualidade

Rotas públicas podem mudar, ficar indisponíveis ou aplicar limites diferentes
conforme rede, horário e política do tribunal. Os relatórios de validação sempre
registram data, ambiente e resultado observado. Eles não devem ser interpretados
como garantia permanente de disponibilidade.
