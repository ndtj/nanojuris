# Verificação

Status: verified — inventário, contrato, pipeline comum e promoção técnica local
foram verificados; fontes sem evidência suficiente permanecem explicitamente
adiadas.

## Resultados

| Gate | Estado | Evidência |
| --- | --- | --- |
| inventário | passed | `docs/coverage/document-capability-inventory.json` e `.md` |
| opt-in | passed | `DocumentReference` e `fetch_document_reference` são explícitos |
| segurança | passed | allowlist HTTPS, limite de bytes, redirects e status de acesso |
| parsing | passed | HTML/PDF/JSON/texto em `documents.py` e testes existentes |
| vínculo | passed | `CanonicalDocument` preserva hash, trace e identidade |
| promoção | passed with limits | 25 fontes tecnicamente prontas constam no manifesto; 35 permanecem adiadas por evidência/contrato/acesso |

## Rastreabilidade

REQ-001 a REQ-008 possuem cobertura local. O pacote não autoriza coleta em massa
nem redistribuição; downloads continuam opt-in, allowlisted e limitados. A
decisão do operador para uso técnico local/federado não altera os estados de
acesso ou de evidência dos demais providers.
### Gate adicional de PDF rotulado incorretamente

`fetch_document_reference` agora executa validação estrutural antes de gravar no
cache. Respostas `application/pdf` sem magic `%PDF-`, com estrutura inválida,
criptografia não suportada ou zero páginas são rejeitadas com
`ParserContractChangedError`. O caso observado no TRE-MG (HTTP 200 com texto de
erro e Content-Type PDF) é coberto por
`test_fetch_document_reference_rejects_pdf_error_body_with_http_200` em
`tests/test_transport_runtime.py`. O construtor canônico continua preservando
bytes inválidos quando usado explicitamente para diagnóstico.
Nota de compatibilidade: a fronteira de rede rejeita imediatamente respostas
declaradas como PDF sem o marcador `%PDF-` (inclusive corpos de erro rotulados
como PDF). Bytes que possuem o marcador, mas têm estrutura truncada, continuam
preservados para diagnóstico e recebem `pdf_status` inválido no documento
canônico, mantendo compatibilidade com fixtures e evidências existentes.
