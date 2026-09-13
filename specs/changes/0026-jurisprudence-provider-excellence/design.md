# Design — arquitetura nacional de jurisprudência

Referência: 0026-jurisprudence-provider-excellence

## Princípios

1. Contrato canônico estável; adapters variáveis.
2. Transporte, parsing, canonicalização e exposição separados.
3. Evidência offline antes de afirmação live.
4. Falha isolada por fonte.
5. Compatibilidade por facade, não por duplicação.
6. Dependências opcionais por capacidade.
7. Instituição, coleção, superfície técnica e provider são entidades distintas.
8. Identidade jurídica é conservadora e versionada.
9. Federação não inventa comparabilidade entre scores das fontes.
10. Todo aceite expira quando sua evidência muda.

## Fluxo

    fonte oficial pública
            |
            v
    policy + transport + rate budget
            |
            v
    SourceResponse imutável
      bytes + status + headers seguros + hash + timing
            |
            v
    parser específico ou família
            |
            v
    ProviderRecord tipado + raw minimizado
            |
            v
    canonical mapper + identity + quality evaluation
            |
            v
    CanonicalDecision / CanonicalPrecedent / CanonicalDocument
            |
            +--> store e deduplicação
            +--> SDK e CLI
            +--> MCP e Studio
            +--> exports

Antes do registry de runtime existe uma topologia de cobertura:

    ramo -> autoridade -> coleção -> superfície -> source contract -> provider

Uma coleção pode migrar de portal sem perder sua identidade conceitual; uma
superfície pode servir várias coleções somente quando o contrato comprovar essa
distinção.

## Camadas

### Registry

Fonte única das declarações runtime: identidade, categoria, capabilities,
filtros, paginação, erros, maturidade, interfaces e feature flag.

### Policy

Decide se uma chamada é permitida, seu limite, user agent, timeout, retry e
necessidade de opt-in. Não executa parsing.

### Transport

Executa HTTP sem interpretar o conteúdo jurídico. Produz resposta imutável e
redigida para logs.

### Parser

Converte uma resposta conhecida em registros específicos da fonte. Mudança
estrutural obrigatória gera erro de contrato.

### Canonical

Normaliza sem apagar raw relevante. Identidade e deduplicação consideram fonte,
tribunal, número CNJ/local e hash textual quando necessário.

Processo, decisão, publicação e documento possuem IDs distintos. Um fingerprint
textual é sinal de equivalência, não prova isolada. Toda união preserva aliases,
evidência e razão; toda decisão de merge pode ser revertida.

### Quality

Calcula completude, estabilidade da identidade, cobertura de campos e
confiabilidade da evidência. Não inventa conteúdo ausente.

### Interfaces

SDK, CLI, MCP, Studio e exports consomem somente facades públicas. Interfaces
não conhecem detalhes de HTML, GraphQL, JSF ou Solr.

### Federation

Traduz a intenção de busca para capacidades verificadas. Mantém ranking por
fonte, aplica ordenação global determinística somente sobre campos comparáveis,
expõe fontes falhas e calcula completude da janela sem declarar total nacional.

### Collection

Runs persistidos guardam query normalizada, capabilities, parser, páginas,
checkpoints, hashes e tombstones. O store é uma coleção de pesquisa local, não
um espelho oficial nem uma garantia de acervo integral.

## Modelo de capability

Cada provider declara:

- tipos de documento;
- busca textual e filtros;
- paginação e ordenação;
- total conhecido ou desconhecido;
- detalhe e inteiro teor;
- formatos;
- autenticação ou controle de acesso;
- participação na busca unificada;
- risco e maturidade;
- data e natureza da última evidência.
- autoridade, coleção, grau e período comprovado;
- semântica dos campos pesquisados e do score nativo;
- política de freshness e fingerprint do contrato.

## Estratégia Juscraper

O intake possui quatro resultados possíveis:

- adopt_algorithm: algoritmo equivalente adaptado ao contrato NanoJuris;
- adopt_fixture: fixture minimizada e licenciada usada para teste;
- use_as_evidence: rota ou comportamento apenas documentado;
- reject_or_defer: fora do escopo, bloqueado ou incompatível.

Não haverá wrapper de DataFrame no núcleo nem dependência runtime obrigatória.

## Resiliência

- limites por host e por operação;
- retry apenas para falhas idempotentes e transitórias;
- backoff com jitter e Retry-After;
- circuit breaker por provider;
- resposta parcial federada com erros por fonte;
- cache com chave por contrato e TTL explícito;
- quarentena para schema drift e payload inválido.

## Evolução

A API atual permanece como facade de compatibilidade. Modelos v2 são
introduzidos internamente, medidos em paralelo e só substituem contratos
públicos por versão semântica e guia de migração.

## Segurança

Nenhuma credencial, cookie de usuário ou token entra no pacote. URLs são
allowlisted por provider; redirects, tamanho, content type, arquivos e logs são
validados. Browser automation não é mecanismo de bypass.
