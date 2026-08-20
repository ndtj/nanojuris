# Adaptação premium do template para NanoJuris

ID: `0005-template-adaptation`
Status: `in_progress`
Owner: `NanoJuris engineering`
Data: `2026-08-20`

## Objetivo

Adaptar as capacidades de maior ganho do template local para criar um pipeline
profissional de parsing, normalização e coleta de jurisprudência pública,
preservando contratos canônicos, proveniência, deduplicação e resumibilidade.

## Requisitos

- RF-001: fornecer parser compartilhado com CSS/XPath, texto, atributos, links,
  regex e seletores estruturais.
- RF-002: usar backend lxml quando disponível e fallback funcional sem tornar o
  import do NanoJuris dependente de lxml.
- RF-003: centralizar normalização de texto, datas, número CNJ, tipos de decisão
  e URLs, preservando valores brutos quando a conversão não for segura.
- RF-004: fornecer memória adaptativa de seletores com fingerprint, confiança,
  evidência e aprovação explícita; nunca alterar parser oficial sozinha.
- RF-005: fornecer runner de coleta por provider com limites, deduplicação,
  checkpoint e manifestos de falha.
- RF-006: persistir coletas em `SQLiteStore` sem duplicar registros canônicos.
- RF-007: migrar discovery e parsers HTML selecionados para os primitives sem
  quebrar fixtures existentes.
- RF-008: manter CLI, MCP, SDD, SourceTrace e ExtractionTrace coerentes.

## Critérios de aceite

- AC-001: parser local extrai CSS/XPath e texto de fixtures sem rede.
- AC-002: fallback BeautifulSoup funciona quando lxml não está disponível.
- AC-003: normalizadores mantêm entrada bruta e produzem valores canônicos
  somente quando a conversão é verificável.
- AC-004: memória adaptativa não promove seletor sem aprovação.
- AC-005: runner retoma checkpoint e não reemite identificadores já vistos.
- AC-006: falhas de acesso, timeout e mudança de parser aparecem no manifesto.
- AC-007: pelo menos dois providers HTML usam o adapter compartilhado com
  fixtures equivalentes.
- AC-008: testes existentes, novos testes e validação SDD passam.
