# Design

## Evidência

O relatório `docs/provider-discovery/tj-provider-sweep-20261012.json` foi
produzido por descoberta pública bounded com 26 providers `tj*`, limite de duas
observações por fonte, profundidade zero, respeito a robots e sem submissão de
POSTs adivinhados. A captura REA/TJSP também registra a entrada pública eproc
`.../externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar`.

## Decisão

Adicionar a rota GET de formulário antes das rotas POST/GET de resultado e
documento nas capabilities da família eproc. A URL base configurável continua
sendo usada pelo runtime; a nova entrada é uma declaração de contrato para
discovery, documentação e diagnóstico.

## Segurança

O discovery segue somente GETs declarados e não transforma respostas de
controle em resultados. CAPTCHA, WAF, login, robots, redirect fora da allowlist
e indisponibilidade continuam estados explícitos.

## Compatibilidade

É uma ampliação aditiva de metadata. Consultas, payloads e URLs de documento
não mudam. O catálogo gerado será reconstruído após a alteração.
