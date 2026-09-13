# 0036 — topologia nacional de jurisprudência

Status: verified
Owner: Legal Domain, Data Architecture e Documentation

## Intenção

Definir o denominador nacional que permita medir cobertura sem confundir
instituição, coleção jurídica, portal, endpoint, provider e disponibilidade.

## Requisitos

- REQ-001: inventariar ramos, autoridades e collections de jurisprudência.
- REQ-002: cada collection declara grau, tipos documentais, período conhecido e
  autoridade oficial.
- REQ-003: mapear zero ou mais superfícies técnicas e source IDs por collection.
- REQ-004: distinguir desconhecido, lacuna, candidato, implementado, bloqueado e
  retired sem dupla contagem.
- REQ-005: cobrir superiores, Federal, Estadual, Trabalho, Eleitoral, Militar,
  precedentes nacionais e controle externo separado.
- REQ-006: métricas publicam numerador, denominador, data e dimensão.
- REQ-007: catálogo runtime é projeção da topologia, não seu denominador.
- REQ-008: mudanças institucionais e migrações de portal preservam histórico.
- REQ-009: cada execução de cobertura referencia uma `coverage_epoch` finita,
  ligada à versão da topologia e à data de corte.
- REQ-010: uma superfície pode servir várias collections, mas cada binding
  declara authority, grau, tipo e período sem dupla contagem.
- REQ-011: o inventário de autoridades deve individualizar os 27 TREs e os três
  TJMs estaduais, mantendo os tribunais superiores, TRFs e TRTs identificáveis.

## Critérios de aceite

- AC-001: matriz machine-readable possui IDs estáveis e schema versionado.
- AC-002: todos os 56 itens atuais reconciliam com collection ou família.
- AC-003: todas as 29 superfícies úteis do snapshot Juscraper reconciliam.
- AC-004: lacunas de TRT, TRE e Justiça Militar ficam visíveis.
- AC-005: gerador produz relatório humano e claims públicos consistentes.
- AC-006: teste detecta órfão, duplicidade, ID inválido e percentual sem data.
- AC-007: mudança de topologia encerra a época anterior e abre nova época sem
  apagar claims históricos.
- AC-008: o catálogo contém 94 autoridades de tribunal, incluindo 27 TREs e
  três TJMs estaduais, e registra a fonte institucional e a data do snapshot.

## Fora de escopo

Implementar providers, provar cobertura temporal integral ou alterar produção.
