# Clarify

- "Ajustar o NanoJuris" significa fazer o provider reproduzir a inicializacao
  publica observada no formulario SAJ antes do POST da pesquisa.
- Isso nao autoriza resolver CAPTCHA, fabricar `recaptcha_response_token`, usar
  credenciais, persistir cookies ou transformar uma tela de controle em resultado.
- A resposta de `captchaControleAcesso.do` sera usada somente para atualizar o
  `uuidCaptcha` retornado pela propria fonte.
