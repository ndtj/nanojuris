# Inventário de rotas TJRO/JURIS — ciclo 14 (2026-09-02)

Uma auditoria bounded da página pública oficial e do bundle Next.js confirmou
três superfícies de dados reproduzíveis e uma superfície observada que ainda
não tem contrato de runtime fechado. Nenhuma credencial foi usada e nenhum corpo bruto foi
persistido.

| Rota | Superfície | Estado | Evidência |
| --- | --- | --- | --- |
| `POST /search/varios_parametros/` | Busca CJPG/CJSG | `implemented` | HTTP 200, JSON, total 676.011, um registro em chamada pública de `responsabilidade` |
| `GET /pje/buscar_pdf_ou_docx/<sistema>/<id>/<pdf\|docx>/` | Inteiro teor público | `implemented` | HTTP 200, PDF de 63.134 bytes para `PJEPG/117961509`, texto extraído com sucesso |
| `POST /search/agregacoes` | Facetas/catálogos | `pending_contract` | HTTP 200, nove agregações e 3.480.824 documentos; adapter aguarda modelo canônico e política de retenção |
| `GET /search/documentos_relacionados/<id_documento_principal>` | Documentos relacionados PJESG | `implemented` | HTTP 200, quatro hits para amostra PJESG `7384224`; método sob demanda, sem fan-out |

O módulo TJRO do Juscraper expõe somente o `POST` de busca. A rota de download
foi confirmada na aplicação oficial e adicionada ao adapter NanoJuris com
identidade composta por `id_processo_documento` + `sistema_origem`, formatos
`pdf`/`docx`, preservação dos bytes e `SourceTrace`.

O frontend usa `Origin`, `Referer` e um cabeçalho `Accept` compatível com
navegador. Isso é parte do contrato público observado, não um contorno de WAF,
CAPTCHA, login ou limite. Respostas 401/403/420/429/5xx são erros explícitos e
nunca viram lista vazia.

Detalhes, hashes e bloqueadores estão em
[`tjro-jurisprudencia-route-inventory-20260902-cycle14.json`](tjro-jurisprudencia-route-inventory-20260902-cycle14.json).
O provider continua `candidate_opt_in_only` até a revisão dos gates globais
0031/0034 e o fechamento dos contratos de filtros, facetas e documentos
relacionados. A resposta de facetas foi registrada apenas por metadados e
hash; nomes e corpo bruto não foram persistidos.
