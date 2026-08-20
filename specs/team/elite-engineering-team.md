# Equipe premium de engenharia da NanoJuris

Status: `accepted`
Escopo: produto, providers, discovery, dados, SDD, plataforma e operação.

## Missão

Construir a plataforma de jurisprudência pública brasileira mais rastreável,
testável e operável possível, com qualidade de dados suficiente para pesquisa,
jurimetria e agentes de IA.

## Núcleo permanente

### 1. Product/Domain Owner

Define problema, prioridade, escopo jurídico, critérios de aceite e decisão de
maturidade. É a autoridade final sobre valor e comportamento do produto.

### 2. Principal Architecture Lead

Mantém fronteiras entre discovery, providers, canonicalização, MCP, Studio e
operação. Aprova designs, ADRs, compatibilidade e caminho de evolução.

### 3. Legal Data/Jurimetry Lead

Define identidade, campos canônicos, tipos documentais, datas, completude,
proveniência e critérios estatísticos. Impede que contexto seja confundido com
jurisprudência textual ampla.

### 4. Provider Discovery Lead

Opera `nanojuris.discovery`, investiga fontes públicas, captura rotas e XHR,
organiza replay, propõe fixtures e entrega drafts SDD.

### 5. Provider Engineering Lead

Implementa adapters, parsers, paginação, normalização, traces e integração com
CLI/MCP/Studio conforme o contrato aprovado.

### 6. Data Quality and Evaluation Lead

Mantém fixtures golden, invariantes, deduplicação, estabilidade de identidade,
regressão de parser e avaliação de completude.

### 7. Security/Privacy Lead

Revisa superfícies de confiança, secrets, permissões, supply chain, logs,
minimização e riscos do worker de discovery.

### 8. Platform/SRE Lead

Cuida de build, CI/CD, OCI, observabilidade, SLOs, backup, restore, rollback e
runbooks.

### 9. QA/Verification Lead

Fecha a relação entre requisito, teste, fixture, comando, evidência e decisão.
Mantém regressão e quality gates.

### 10. Documentation/SDD Lead

Garante consistência entre specs, dossiês de provider, source contracts,
catálogo gerado, README, changelog e handoff.

## Competências de elite

- engenharia Python tipada e testável;
- HTTP, HTML, JSON, JavaScript, XHR, browser automation e parsing;
- modelagem de dados canônicos e provenance;
- jurisprudência brasileira e jurimetria;
- SDD, ADR, C4, threat modeling e revisão adversarial;
- testes offline, contract tests, property-based thinking e avaliação;
- OCI, Linux, CI/CD, observabilidade, backup e recuperação;
- segurança de aplicações, privacidade e supply chain;
- comunicação escrita clara e decisões rastreáveis.

## Célula mínima por provider

```text
Domain Owner + Discovery Lead + Provider Engineer + Data Quality + QA
                         |
                Architecture/Security/SRE
                  conforme nível de risco
```

## Pacote obrigatório de handoff

1. `research.md` com evidências locais e hipóteses;
2. `clarify.md` com decisões e perguntas abertas;
3. `spec.md` com requisitos, falhas e ACs;
4. `design.md` e ADRs;
5. `tasks.md` com dependências;
6. fixtures minimizadas e evidências de replay;
7. código e testes;
8. `verification.md` e `traceability.md`;
9. dossier do provider e source contract;
10. decisão registrada de release ou pendência.

## Scorecard premium

Um provider deve ser avaliado por:

- autoridade e estabilidade da fonte;
- cobertura e completude;
- identidade estável e deduplicação;
- conteúdo textual e datas;
- qualidade do parser e fixtures;
- provenance e extraction trace;
- comportamento sob falha;
- documentação sincronizada;
- observabilidade e capacidade de recuperação;
- risco residual e manutenção prevista.

Quantidade de providers não é métrica primária de excelência.
