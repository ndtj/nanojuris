# Clarificações

- “Ajustar” não significa contornar bloqueios: CAPTCHA, WAF, login e TLS
  inválido continuam bloqueios explícitos.
- O REST TJPE não é removido. O modo `auto` só usa JSF após erro de transporte
  sem resposta HTTP; respostas 4xx/5xx continuam com a classificação original.
- O fallback não promete disponibilidade nacional: cada tribunal pode alterar
  seu contrato ou limitar IPs públicos.
- Nenhum teste live guarda corpo, cookie, ViewState, token ou credencial.
