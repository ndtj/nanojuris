# Threat model

- CAPTCHA/WAF/login: detectar e classificar como acesso requerido; nunca
  contornar.
- PII em decisoes: nao persistir respostas live nos artefatos de evidencia;
  aplicar politicas de retencao antes de armazenamento.
- Drift de HTML: validar container, linha, identificador e texto; gerar erro
  explicito em vez de zero resultados.
- Paginacao: manter a mesma sessao publica e limite de 10; parar em falha.
- Mistura semantica: identidade `tjsp_cjpg` e discriminador de primeiro grau
  impedem mistura automatica com `tjsp_cjsg`.
