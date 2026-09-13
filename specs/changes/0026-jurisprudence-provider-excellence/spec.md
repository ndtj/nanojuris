# Especificação — excelência nacional de providers de jurisprudência

ID: 0026-jurisprudence-provider-excellence
Status: verified
Owner: NanoJuris engineering
Data: 2026-09-01

## Problema e intenção

A NanoJuris já documenta 56 fontes, implementa 46 providers e expõe 42 fontes
na busca unificada. Essa fotografia não é o denominador de toda a jurisprudência
brasileira. A expansão por volume, porém, pode produzir contratos
desiguais, respostas vazias falsas, perda de provenance, dependências pesadas e
promessas de cobertura não comprovadas.

O programa cria uma arquitetura e um processo de promoção que permitam ampliar
a cobertura brasileira com qualidade verificável, aproveitando evidência e
código MIT do Juscraper onde houver equivalência, sem acoplar o domínio da
NanoJuris ao modelo pandas ou às decisões internas do projeto externo.

## Objetivos

- consolidar jurisprudência textual pública em contratos canônicos estáveis;
- fechar a cobertura dos tribunais estaduais por ondas verificáveis;
- padronizar transporte, paginação, erros, traces e inteiro teor;
- transformar fixtures e chamadas bounded em evidência de qualidade;
- permitir evolução, suspensão e rollback por provider;
- preservar compatibilidade das interfaces públicas existentes;
- tornar documentação, catálogo e maturidade derivados da mesma fonte de
  verdade.
- definir o universo nacional por ramo, instituição, coleção, grau, tipo
  documental e período antes de publicar percentuais de cobertura;
- garantir identidade e versionamento capazes de distinguir decisões do mesmo
  processo e reconciliar republicações da mesma decisão;
- tornar a busca federada explícita quanto à equivalência de query, ranking,
  filtros e completude;
- oferecer coleta local resumível e reproduzível sem prometer redistribuição ou
  espelhamento integral de acervos.

## Fora de escopo

- consulta processual, partes, movimentos, timelines, comunicações e DataJud;
- redistribuição integral de acervos sem base jurídica e operacional;
- contorno de CAPTCHA, WAF, login, TLS, rate limit ou controle de acesso;
- scraping em massa durante discovery ou validação live;
- dependência obrigatória do Juscraper no runtime;
- alteração de produção, publicação ou release neste pacote.

## Requisitos

- REQ-001: toda fonte deve declarar identidade, autoridade, categoria,
  coverage_role, capacidades, maturidade e status operacional.
- REQ-002: toda busca deve diferenciar sucesso, vazio real, query inválida,
  bloqueio, rate limit, timeout, indisponibilidade, TLS e mudança de schema.
- REQ-003: todo registro canônico deve preservar fonte, URL, instante, raw
  mínimo, identidade, completude e traces.
- REQ-004: filtros, ordenação e paginação devem declarar semântica nativa,
  traduzida, pós-filtrada, não suportada ou não verificada.
- REQ-005: reutilização do Juscraper deve ocorrer por adaptação explícita, com
  análise de licença, provenance do código e testes de equivalência.
- REQ-006: um provider só pode entrar na busca unificada após contrato,
  fixtures, parser, testes, documentação e decisão de maturidade.
- REQ-007: inteiro teor deve possuir pipeline separado, limitado, com hash,
  content type, tamanho, origem e falhas explícitas.
- REQ-008: validação live deve ser opt-in, bounded, rate-aware, reproduzível e
  incapaz de transformar falha externa em zero resultados.
- REQ-009: mudanças devem declarar impacto em SDK, CLI, MCP, Studio, exports,
  store, docs e compatibilidade legada.
- REQ-010: a arquitetura deve permitir desativação, rollback e quarentena por
  provider sem indisponibilizar a busca federada inteira.
- REQ-011: métricas de qualidade devem medir dados, contrato e operação; número
  bruto de providers não pode ser métrica de sucesso isolada.
- REQ-012: cada pacote filho deve fechar sua cadeia requisito, tarefa, teste e
  evidência antes da promoção seguinte.
- REQ-013: cobertura deve usar denominadores versionados por ramo, autoridade,
  coleção e período; “provider” não é sinônimo de “tribunal coberto”.
- REQ-014: identidade deve distinguir processo, julgamento, decisão, versão,
  documento e publicação, preservando relações entre eles.
- REQ-015: deduplicação deve ser conservadora, explicável e reversível; número
  de processo isolado nunca pode fundir decisões.
- REQ-016: busca federada deve declarar quais campos cada fonte pesquisa e não
  comparar scores nativos heterogêneos como se fossem equivalentes.
- REQ-017: coleta persistente deve usar run manifest, checkpoint, cursor,
  fingerprint de query/contrato e política de freshness.
- REQ-018: novas superfícies externas, inclusive primeiro grau e detalhe, devem
  entrar no backlog antes do catálogo runtime e possuir source ID planejado.
- REQ-019: conclusões do autopilot devem ser invalidadas quando qualquer
  evidência normativa do provider mudar.
- REQ-020: maturidade de engenharia, qualidade de dados e saúde operacional são
  dimensões independentes.

## Comportamentos obrigatórios

### Resultado válido

O adapter retorna registros canônicos, metadados de paginação, estado de
completude e traces associados à requisição e à extração.

### Resultado vazio confirmado

O adapter só retorna empty quando a fonte respondeu validamente e o contrato da
fonte comprovou ausência de registros para a consulta.

### Registro parcial

Campos ausentes permanecem nulos, o motivo é preservado quando conhecido e a
completude do registro é calculada sem inventar valores.

### Falha da fonte

A falha é classificada por provider, preserva evidência mínima e não elimina
resultados válidos de outras fontes federadas.

### Mudança de schema

Campos ou estruturas obrigatórias ausentes causam parser_contract_changed e
quarentena da resposta; não geram resultado vazio.

## Critérios de aceite

- AC-001: o programa possui spec-of-specs e quatorze pacotes filhos com gates
  independentes.
- AC-002: a linha de base de 56 fontes, 46 runtime e 42 unificadas está
  registrada como fotografia, não como garantia live.
- AC-003: existe arquitetura explícita source-to-evidence-to-canonical-to-
  interfaces com limites de confiança.
- AC-004: existe matriz de adoção do Juscraper com sobreposição, candidatos,
  bloqueios e itens fora de escopo.
- AC-005: contrato, transporte, qualidade, documento, observabilidade e release
  possuem pacotes separados.
- AC-006: todos os requisitos do programa apontam para pacote, tarefa e gate.
- AC-007: a validação SDD passa sem exigir alteração de runtime.
- AC-008: nenhuma produção, publicação ou chamada live é executada por este
  pacote de planejamento.
- AC-009: existe topologia nacional que expõe lacunas de Trabalho, Eleitoral,
  Militar, Federal, Estadual e tribunais superiores.
- AC-010: as 29 superfícies jurisprudenciais úteis observadas no snapshot
  Juscraper possuem decisão de intake explícita.
- AC-011: o estado autônomo diferencia trabalho, saúde operacional e disposição
  final e usa fingerprint para revalidação.
- AC-012: claims públicos de cobertura derivam de artefato gerado e datado.

## Riscos

- portais públicos alteram rotas e schemas sem versionamento;
- cobertura nominal pode ser confundida com cobertura temporal ou integral;
- cópia direta pode importar dependências e semânticas inadequadas;
- excesso de abstração pode dificultar providers simples;
- validação live pode produzir pressão indevida sobre fontes oficiais;
- inteiro teor pode trazer volume, formatos e riscos maiores que a busca.
