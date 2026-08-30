# Alternativas oficiais para ampliar a cobertura

Esta matriz orienta a próxima rodada de adapters da NanoJuris. Só promovemos uma
fonte quando há contrato reproduzível, escopo de jurisprudência claro e fixture
sanitizada. Nenhuma chamada ou publicação em produção faz parte deste registro.

| Prioridade | Fonte oficial | Superfície | Decisão |
| --- | --- | --- | --- |
| P0 | TJDFT | `POST /api/v1/pesquisa` (JSON) | Implementada no adapter `tjdf_juris` como opt-in; HTML continua default. |
| P1 | STJ Dados Abertos | CKAN `package_search`/`package_show` e arquivos JSON/CSV/ZIP | Reutilizar o provider de sincronização local existente; não duplicar como busca online. |
| P1 | TJPE | API REST de jurisprudência | Próximo candidato; confirmar contrato, paginação e TLS em fixture antes de alterar o runtime. |
| P1 | TJPB PJe | Pesquisa de jurisprudência de segundo grau | Candidato restrito ao subconjunto PJe; requer payload versionado e identidade estável. |
| P1 | TCE-PR ViaJuris | Exportação anual de acórdãos em CSV, com dicionário de dados | Novo candidato de baixo risco para sincronização documental; requer fixture, checksum, parser e novo `source_id`. |
| P1 | TJES Consulta Jurisprudência | `GET /consulta-jurisprudencia/api/search` com `core`, `q`, `page` e `per_page`; `/cores`, `/facets` e `/health` | Contrato JSON público reproduzido em 28/08/2026 para cinco cores e documentos com ementa/acórdão; criar adapter local após fixtures, limites, paginação e revisão de reutilização. |
| P2 | TCE-GO Dados Abertos | `POST /api/Transparencia/TceJuris` (JSON) | Rota oficialmente documentada, mas chamada pública atual devolveu erro de backend; manter bloqueada até sucesso reproduzível. |
| P2 | TCE-CE Jurisprudência | Consulta textual pública e boletins | Portal oficial confirmado, porém sem contrato estruturado público; manter pendente. |
| P2 | TRT2 PJe Jurisprudência | `/juris-backend/api/opcoes` e `/filtros` (JSON) | Configuração e agregações públicas reproduzíveis; documentos retornam desafio; manter somente como contrato parcial/diagnóstico. |
| P2 | TRT2 BASIS/Boletins/Ementários | Catálogo HTML e PDFs oficiais de boletins, ementários e jurisprudência consolidada | Fonte documental candidata, sem JSON/CSV ou licença explícita; só ingestão curada com catálogo, checksum e parser, separada da busca PJe. |
| P2 | TJAP Tucujuris | Consulta institucional | Entrada atual retorna Cloudflare 403 e alternativa não resolve DNS; bloqueado, sem adapter. |
| P2 | Falcão JT | Repositório nacional da Justiça do Trabalho | Raiz oficial retorna CloudFront 403; sem contrato de resultados; manter bloqueado. |
| P2 | TJCE/TJSP CJSG | e-SAJ de segundo grau | Manter adapters com diagnóstico de controle de acesso; não contornar CAPTCHA. |
| P2 | TRE-SP | Pesquisa geral e temas selecionados | O provider atual cobre apenas temas selecionados; a pesquisa geral não tem contrato público estável. |
| Fora do escopo | CNJ DataJud | Metadados processuais e movimentações | Não implementar na NanoJuris; pertence ao produto de dados processuais NanoJud. |

## Critérios de promoção

1. Fonte oficial e escopo jurídico documentados.
2. Rota e payload reproduzíveis sem segredo ou bypass.
3. Fixture de sucesso, vazio e erro esperado, com identidade estável.
4. Parser canônico preservando `raw`, datas, completude e `SourceTrace`.
5. Testes determinísticos, auditoria offline e SDD aprovados.

## Evidências oficiais

- [API pública do TJDFT](https://www.tjdft.jus.br/transparencia/tecnologia-da-informacao-e-comunicacao/dados-abertos/webservice-ou-api)
- [Documentação da API do TJDFT](https://www.tjdft.jus.br/transparencia/tecnologia-da-informacao-e-comunicacao/dados-abertos/documentacao_api_seti_transparencia.pdf/@@download/file/Documentação_API_SETI_Transparência.pdf)
- [Datasets de jurisprudência do STJ](https://dadosabertos.web.stj.jus.br/group/jurisprudencia)
- [Webservices oficiais do TCU](https://sites.tcu.gov.br/dados-abertos/webservices-tcu/)
- [Endpoints públicos do DataJud](https://datajud-wiki.cnj.jus.br/api-publica/endpoints/)
