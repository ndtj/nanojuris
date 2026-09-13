# 0041 - adapter de jurisprudencia textual do TJRN

Status: verified
Owner: Provider Engineering, Legal Data, Security e QA

## Intencao

Fechar o contrato publico observado do portal de jurisprudencia do Tribunal de
Justica do Rio Grande do Norte sem misturar busca processual, SAJ legado ou
precedentes qualificados.

## Requisitos

- REQ-001: usar somente a rota publica `POST /api/pesquisar` do portal oficial;
- REQ-002: mapear ementa, inteiro teor, numero, relator, orgao, classe, datas,
  grau, sistema e identificadores para o modelo canonico;
- REQ-003: preservar payload minimizado em `raw` e registrar `SourceTrace`;
- REQ-004: fechar pagina, ordenacao, filtros e semantica de total antes de
  registrar o provider no runtime;
- REQ-005: HTTP 4xx/5xx, timeout, schema drift e acesso controlado permanecem
  outcomes observaveis e nunca `zero_results`;
- REQ-006: manter o provider opt-in e fora da federacao ate todos os gates.

## Criterios de aceite

- AC-001: contrato, fixture sanitizada e parser independente reproduzem um
  resultado real da evidencia live de 2026-09-01;
- AC-002: existem fixtures de sucesso, vazio confirmado, payload invalido,
  timeout/acesso e schema drift;
- AC-003: identidade 0037 deduplica sem apagar origem, pagina e completude;
- AC-004: testes e documentacao passam sem usar credencial, browser cookie ou
  bypass de CAPTCHA/WAF.

## Fora de escopo

Consulta processual, endpoint e-SAJ legado bloqueado, crawling em escala,
redistribuicao integral do acervo e alteracao de producao.
