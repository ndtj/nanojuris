# Clarificações

- A mudança corrige o contrato de transporte; não garante disponibilidade do
  tribunal, pois WAF, CAPTCHA, TLS e robots podem bloquear a chamada.
- O GET da página 1 é feito também para uma solicitação de página posterior,
  pois ele estabelece/valida a sessão e fornece o `conversationId` do TJSP.
- O valor de `conversationId` não é credencial; ainda assim não será incluído
  em artefatos públicos, somente sua presença será testada.
- CJPG, TJRO LIAME e consultas processuais não serão misturados nesta alteração.
