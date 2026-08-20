# Especificação de mudança

ID: `0003-premium-team-operating-model`
Status: `accepted`
Owner: `NanoJuris engineering`
Data: `2026-08-20`

## Problema e intenção

A NanoJuris possui contratos, providers, SDD e uma camada de descoberta, mas a
execução premium exige papéis especializados, autoridade clara, revisão cruzada
e uma cadeia de evidências que sobreviva à troca de agentes e colaboradores.

## Objetivos

- formalizar a equipe virtual premium;
- definir responsabilidades, competências e saídas por papel;
- estabelecer RACI para produto, provider, dados, plataforma e release;
- conectar a célula de discovery aos artefatos SDD;
- separar proposta, implementação, verificação e aceite;
- definir gates de qualidade, maturidade e promoção;
- criar um modelo de operação repetível para novos providers.

## Fora de escopo

- contratar pessoas ou escolher fornecedores comerciais;
- publicar ou promover provider automaticamente;
- alterar providers existentes nesta mudança;
- substituir a constituição, os contratos ou os gates do NanoJuris;
- criar autorização implícita para produção ou operações irreversíveis.

## Atores

- Product/Domain Owner humano;
- Architecture Lead;
- Legal Data/Jurimetry Lead;
- Provider Discovery Lead;
- Provider Engineering Lead;
- Data Quality and Evaluation Lead;
- Security/Privacy Lead;
- Platform/SRE Lead;
- QA/Verification Lead;
- Documentation/SDD Lead;
- agentes especializados sob escopo mínimo.

## Requisitos funcionais

### RF-001 — Papéis e charter

Cada papel deve possuir missão, entradas, entregáveis, competências, autoridade
e critérios de saída documentados.

### RF-002 — Separação de autoridade

Nenhum agente ou implementador pode ser a única autoridade sobre intenção,
arquitetura, implementação, verificação e release da mesma mudança.

### RF-003 — Célula de provider

Cada novo provider deve ser atendido por um conjunto mínimo de domínio,
discovery, engenharia, qualidade e revisão, com Security/SRE acionados conforme
risco.

### RF-004 — Fluxo SDD

Toda mudança deve percorrer `inspect`, `clarify`, `specify`, `design`, `plan`,
`apply`, `verify`, `review` e `release`, com artefatos persistentes.

### RF-005 — Pareceres independentes

Mudanças de alto impacto devem receber parecer separado de arquitetura,
domínio/dados, segurança, qualidade e operação antes do aceite.

### RF-006 — Gate de provider premium

Provider só pode ser classificado como pronto quando possuir contrato,
identidade estável, conteúdo textual, datas ou datas brutas, canonical output,
provenance, fixtures, testes, documentação e comportamento operacional.

### RF-007 — Métricas da equipe

O modelo deve acompanhar cobertura, taxa de contratos confirmados, regressões,
completude, freshness, tempo de recuperação, documentação pendente e riscos
abertos.

### RF-008 — Continuidade

Outra pessoa ou agente deve conseguir retomar uma mudança a partir dos artefatos
sem depender da memória da conversa ou de conhecimento tribal.

## Critérios de aceite

- `AC-001` - O charter lista todos os papéis, competências, entradas e saídas.
- `AC-002` - A matriz RACI cobre produto, discovery, provider, dados, segurança, SRE, QA e release.
- `AC-003` - O fluxo define gates e artefatos obrigatórios por fase.
- `AC-004` - Existe separação explícita entre quem implementa, verifica e aprova.
- `AC-005` - A célula mínima de provider possui domínio, discovery, engenharia e qualidade.
- `AC-006` - O gate de maturidade referencia contrato, canonicalidade, provenance, fixtures e operação.
- `AC-007` - A documentação permite handoff sem depender do histórico de chat.
- `AC-008` - A validação SDD do repositório passa.

## Riscos e questões em aberto

- Uma equipe virtual pode gerar sobreposição; RACI e dono único por decisão devem
  ser preenchidos em cada mudança.
- Muitos gates podem reduzir velocidade; o nível de revisão deve ser
  proporcional ao impacto e ao risco.
- Métricas de volume podem incentivar providers frágeis; qualidade e cobertura
  devem prevalecer sobre contagem.
