# Especificação — cobertura nacional de jurisprudência com qualidade ouro

Status: `proposed`

## Objetivo

Elevar a biblioteca NanoJuris de um conjunto de adapters heterogêneos para uma
malha nacional de jurisprudência pública, rastreável e eficiente. O plano cobre
primeiro grau, segundo grau, tribunais superiores, federal, eleitoral,
trabalhista e militar, sem afirmar cobertura onde a fonte oficial não permite
acesso público reproduzível.

## Requisitos funcionais

- **REQ-001** — Registrar cada superfície como combinação de autoridade, ramo,
  grau, instância, coleção e provider.
- **REQ-002** — Manter lifecycle, contrato, disponibilidade, maturidade,
  federação, documento e legalidade como dimensões independentes.
- **REQ-003** — Descobrir e usar somente rotas, APIs, exportações ou jornadas
  públicas oficialmente observáveis ou formalmente autorizadas.
- **REQ-004** — Implementar filtros somente quando comprovados pelo contrato;
  distinguir remoto, traduzido, local, ignorado e não suportado.
- **REQ-005** — Preservar identidade, classe, órgão, relator, tipo documental,
  datas, ementa, inteiro teor, URL, campos brutos e `SourceTrace`.
- **REQ-006** — Distinguir vazio autoritativo, vazio não confirmado, bloqueio,
  timeout, rate limit, erro de transporte, schema inválido, parcial e cancelado.
- **REQ-007** — Obter inteiro teor ou documento oficial sob demanda quando a
  fonte o oferecer, verificando MIME, tamanho, hash, codificação e extração.
- **REQ-008** — Aplicar paginação, cursor, ordenação, deduplicação e limites sem
  sobreposição indevida e sem transformar falha em ausência de resultados.
- **REQ-009** — Promover automaticamente apenas providers que satisfaçam o gate
  técnico; manter decisões legais e de release fora da automação.
- **REQ-010** — Integrar providers elegíveis à federação sem retirar do
  diagnóstico os candidatos ou bloqueados.
- **REQ-011** — Revalidar periodicamente schema, disponibilidade, completude,
  latência e estabilidade do parser com baixa frequência.
- **REQ-012** — Manter cache apenas efêmero de respostas live, não pesquisável e
  invalidável por provider.
- **REQ-013** — Comparar técnicas do Juscraper por contrato, rota e semântica,
  nunca considerar sua existência como prova de disponibilidade atual.
- **REQ-014** — Aplicar minimização de dados pessoais, retenção documentada e
  trilha de auditoria sem armazenar credenciais ou tokens de desafio.
- **REQ-015** — Entregar handoff reproduzível para outro modelo com comandos,
  estados, limites, critérios de parada e artefatos versionados.

## Critérios de aceite

- **AC-001** — O registro nacional contém uma entrada única para cada superfície
  obrigatória e nenhuma contagem é mantida manualmente.
- **AC-002** — Todo provider promovido possui fonte oficial, contrato, runtime,
  fixture, chamada live bounded, qualidade canônica e trace.
- **AC-003** — Toda chamada com CAPTCHA, WAF, Turnstile, 403, 429, timeout, TLS
  ou schema inválido mantém o estado explícito e não produz lista vazia.
- **AC-004** — Para cada filtro declarado existe evidência de aplicação remota,
  tradução, aplicação local ou não suporte.
- **AC-005** — Paginação de pelo menos duas páginas, quando suportada, é testada
  contra sobreposição, ordenação e deduplicação.
- **AC-006** — Cada documento aceito possui URL oficial, MIME coerente, limite
  de bytes, hash, método de extração e status de texto.
- **AC-007** — Registros aceitos de segundo grau têm `degree=second` e
  `instance=second`; registros incompatíveis são rejeitados ou diagnosticados.
- **AC-008** — A federação retorna status, latência, filtros, páginas, total e
  trace por fonte, incluindo fontes que falharam.
- **AC-009** — A comparação com Juscraper gera diferença semântica e evidência
  live; não há cópia de código ou bypass de proteção.
- **AC-010** — A suíte local, validação SDD, lint, type check, compile e diff
  check passam no fechamento de cada lote.
- **AC-011** — Nenhuma tarefa humana (licença, retenção, owner, release) é
  marcada como aprovada sem registro humano correspondente.
- **AC-012** — O handoff permite que outro modelo retome do último baseline sem
  depender do histórico de conversa.

## Não objetivos

Não é objetivo prometer 27/27, extrair fontes protegidas, resolver desafios,
armazenar corpus completo, ou substituir a revisão jurídica e operacional.

