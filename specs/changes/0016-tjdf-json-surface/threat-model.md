# Threat model

- **Credenciais**: a rota pública não recebe credenciais; não há segredo novo.
- **Disponibilidade**: rate limit e timeouts existentes continuam ativos.
- **Integridade**: identidade obrigatória e erro de contrato evitam registros
  vazios ou colididos.
- **Confidencialidade**: traces não devem registrar tokens; fixtures são
  sanitizadas.
- **Abuso**: a opção opt-in evita ativar uma superfície não comparada em
  instalações existentes.
