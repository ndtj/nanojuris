# Threat model

- HTTP 403: classificar como acesso bloqueado; nunca fazer bypass.
- CAPTCHA/WAF/login: nao automatizar nem armazenar credenciais.
- Mistura semantica: CJPG deve possuir identidade propria e nao reutilizar
  resultados de CJSG ou consulta processual.
- Dados pessoais: nao persistir corpo live como fixture sem revisao de
  retencao e licenca.
