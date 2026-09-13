# 0044 — adapter TJES CJPG (primeiro grau)

Status: verified
Owner: Provider Engineering, Legal Data, Security e QA

## Intenção

Adicionar à NanoJuris uma fonte pública reproduzível de jurisprudência de
primeiro grau do TJES, sem confundir CJPG (`pje1g`) com CJSG, turma recursal,
precedentes qualificados ou consulta processual.

## Requisitos

- REQ-001: usar somente `GET /consulta-jurisprudencia/api/search` no domínio
  oficial, com `core=pje1g`.
- REQ-002: mapear identidade, número, classe, assunto, órgão, comarca,
  magistrado, data de juntada, ementa e inteiro teor quando presentes.
- REQ-003: preservar o documento recebido em `raw` e registrar `SourceTrace`
  com status, URL final, tipo, bytes, tempo e hash.
- REQ-004: respeitar o limite conservador de 20 itens por página, timeout e
  `rate_limit_interval` configurados.
- REQ-005: distinguir página vazia confirmada de falha HTTP, bloqueio,
  timeout, resposta não-JSON ou alteração de schema.
- REQ-006: declarar `supports_unified_search=True` somente após os gates
  técnicos e a decisão operacional explícita; a promoção permanece local e
  federada nesta rodada, sem deploy ou publicação.
- REQ-007: não usar cookies, CAPTCHA, WAF bypass, credenciais ou código
  upstream em runtime.

## Critérios de aceite

- AC-001: uma chamada pública bounded reproduz HTTP 200, documentos e total;
- AC-002: fixtures sanitizadas cobrem sucesso, vazio, erro e schema drift;
- AC-003: parser mapeia para `JurisprudenceResult` e
  `CanonicalDecision`, mantendo campos desconhecidos;
- AC-004: testes verificam parâmetros, limite, trace e classificação de 4xx,
  429 e 5xx;
- AC-005: documentação, catálogo e inventário identificam a fonte como
  opt-in e de primeiro grau;
- AC-006: nenhum deploy, push ou alteração de produção é realizado.

## Fora de escopo

Rotas de detalhe não observadas, ingestão em escala, redistribuição integral do
acervo, segundo grau/turma recursal, consulta processual e promoção à federação.
