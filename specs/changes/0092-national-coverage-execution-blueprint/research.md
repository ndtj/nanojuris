# Pesquisa e referências

## Fontes do repositório

- `AGENTS.md`: ordem de descoberta, catálogo gerado e limites de acesso.
- `specs/constitution.md`: contrato antes de código, evidência e uso responsável.
- SDD 0070: capacidades ouro, filtros e documentos.
- SDD 0077: busca live, intenção, planner e ranking CPU-only.
- SDD 0078: runtime de acesso público e classificação de desafios.
- SDDs 0081–0089: famílias, documentos e handoff nacional.
- SDD 0091: snapshot operacional e prompt de execução.
- `docs/provider-discovery/juscraper-*`: inventário e diferenças já observadas.

## Fontes oficiais a consultar por adapter

O executor deve registrar a URL específica da fonte, não apenas o domínio:

- portal de jurisprudência do tribunal;
- API ou BFF documentado no frontend público;
- exportação oficial, sitemap ou RSS;
- documentação pública de filtros e termos;
- página oficial de acesso/indisponibilidade.

Não usar páginas de terceiros como prova de cobertura. Juscraper serve para
descobrir nomes, seletores e estratégias, mas a confirmação é sempre feita na
fonte oficial atual.

## Referências acadêmicas para relevância

- BEIR: Benchmarking Information Retrieval — <https://arxiv.org/abs/2104.08663>.
- Legal Case Retrieval Survey — <https://aclanthology.org/2024.acl-long.350/>.
- Legal Elements for Case Retrieval — <https://aclanthology.org/2024.findings-acl.139/>.
- Reciprocal Rank Fusion no OpenSearch —
  <https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/rrf/>.

Estas referências orientam avaliação e fusão de ranking; não autorizam IA,
embeddings ou uma inferência sobre a disponibilidade de qualquer tribunal.

## Princípio de atualização

Toda descoberta live deve informar data, método, status, tamanho/resultado
redigido, classificação e TTL. Um resultado antigo é evidência histórica, não
prova de disponibilidade atual.
