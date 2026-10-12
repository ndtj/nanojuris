# Research

- O script standalone fornecido pelo usuario, executado em 2026-10-12 com
  `dano moral`, fez GET do formulario, POST de `captchaControleAcesso.do`, POST
  da busca e retornou 20 acordaos reais.
- O provider anterior, com a mesma consulta, parava em
  `AccessControlRequiredError` antes do POST valido porque nao inicializava o
  UUID da sessao publica.
- O retorno observado da rota de controle e JSON com novo `uuidCaptcha`; nenhum
  token reCAPTCHA e resolvido ou fabricado.
