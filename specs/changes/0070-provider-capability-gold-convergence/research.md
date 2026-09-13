# Pesquisa — convergência de capacidades

Mudança: `specs/changes/0070-provider-capability-gold-convergence/spec.md`
Data da revisão: `2026-09-06`
Responsável: arquitetura NanoJuris

## Pergunta

Como provar, provider por provider, que todos os filtros e dados públicos
disponíveis foram descobertos e implementados, incluindo inteiro teor, sem
prometer capacidades que a fonte não oferece?

## Fontes locais examinadas

| Fonte | Fotografia | Achado verificável | Consequência |
| --- | --- | --- | --- |
| `docs/registry/provider-catalog.full.json` | 2026-09-06 | 60 fontes, 52 runtime, 38 unificadas, 34 com full text declarado | denominador inicial do programa |
| `docs/quality/provider-quality.json` | 2026-09-06 | 32 gold no score offline; 17 com bloqueio operacional | score atual não prova completude de capacidades |
| `docs/provider-discovery/unified-contract-matrix.json` | 2026-09-05 | 52 providers, 250 classificações nativas, 37 unsupported e 1.533 unverified | maior lacuna é classificação de filtros |
| `docs/coverage/document-capability-inventory.json` | atual | 18 runtime sem full text declarado; 17 com acesso documental fraco/ausente | inteiro teor exige onda própria |
| `docs/provider-discovery/all-provider-sweep.json` | 2026-08-20 | somente 44 providers observados | discovery profundo está defasado em relação ao runtime |
| `src/nanojuris/models.py` | worktree atual | semânticas `native`, `translated`, `local_postfilter`, `unsupported`, `unverified` já existem | ampliar evidência sem quebrar API |
| SDDs 0007, 0026, 0027, 0031, 0032 e 0038 | atual | fundações existem e estão verificadas | 0070 deve convergir execução, não reescrever fundações |

## Diagnóstico

### Divergência de ouro

O catálogo registra 14 providers com `maturity_tier=gold`, enquanto o
scorecard offline registra 32 com `quality_tier=gold`. As duas métricas usam
critérios diferentes. Nenhuma delas exige que todos os filtros observáveis
tenham estado terminal nem que o caminho documental tenha sido testado de ponta
a ponta.

### Filtros

O contrato unificado contém 35 filtros canônicos. No snapshot analisado, a
maior parte das combinações provider/filtro permanece `unverified`. Isso não
significa que a fonte suporta o filtro; significa apenas ausência de prova.

Cobertura nativa mais comum no snapshot:

- texto: 38 providers;
- número: 34;
- atualização: 20;
- publicação: 19;
- expressão exata: 18;
- tipo: 13;
- relator: 7;
- classe processual: 2;
- órgão julgador: 1.

Campos como grau, instância, ramo, coleção e tipo documental podem estar
presentes nos registros canônicos sem que a fonte permita filtrá-los
remotamente. Extração e capacidade de consulta são dimensões separadas.

### Inteiro teor

`supports_full_text=true` também não é prova suficiente. É necessário separar:

```text
inline_text
detail_api
document_link
public_download
ocr_required
not_offered_by_source
access_blocked
unverified
```

Uma ementa, tese, resumo ou link não deve ser rotulado como inteiro teor. Uma
fonte que comprovadamente não oferece inteiro teor pode atingir ouro de
engenharia, mas não `document_gold`; sua limitação continua visível.

## Estratégia de descoberta

Para cada superfície oficial, a pesquisa seguirá oito passes bounded:

1. **Entrada oficial:** páginas de pesquisa, ajuda, documentação e catálogos.
2. **Controles de UI:** inputs, selects, valores ocultos, opções, validações e
   combinações dependentes.
3. **Contrato de rede:** métodos, rotas, headers, payloads, cookies públicos,
   GraphQL/OpenAPI e requests disparados pela UI.
4. **Bundles públicos:** apenas inspeção estática para localizar rotas, nomes de
   campos e enums; nenhum segredo ou bypass.
5. **Teste diferencial:** consulta base versus uma variação por filtro para
   provar que o filtro altera request e/ou resultado de forma coerente.
6. **Pagina/detalhe:** segunda página, ordenação, total, identificador, página
   de detalhe e relações entre registros.
7. **Documento:** URL, método, MIME, tamanho, hash, páginas, texto e necessidade
   legítima de OCR.
8. **Falhas:** vazio autoritativo, parâmetro inválido, timeout, rate limit,
   acesso controlado e schema drift.

## Política de evidência

Cada capacidade precisa apontar para ao menos uma evidência reproduzível:

- fixture sanitizada;
- teste contratual;
- snapshot de catálogo oficial;
- request/response bounded com hash e data;
- documentação oficial;
- comparação diferencial que demonstre efeito.

Nomes de inputs encontrados no HTML ou em JavaScript são hipóteses até que uma
requisição válida prove sua semântica.

## Limitações

- Fontes podem não oferecer inteiro teor, determinados filtros ou dados
  estruturados.
- Controles de acesso legítimos permanecem bloqueios.
- O programa não demonstra completude histórica do acervo; demonstra
  completude do contrato público observado.
- Evidência live envelhece e requer TTL/revalidação.

