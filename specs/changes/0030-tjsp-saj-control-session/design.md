# Design

## Fluxo

```text
GET formulario
  -> coletar campos atuais
  -> POST captchaControleAcesso.do com uuidCaptcha do formulario
  -> substituir uuidCaptcha somente se a fonte devolver outro UUID
  -> POST resultadoCompleta.do
  -> parsear resultados ou classificar controle explicitamente
```

O provider e o exemplo usam uma sessao efemera em memoria. A rota de controle
nao e tratada como fonte de jurisprudencia; ela apenas prepara a sessao publica
conforme o fluxo declarado pelo SAJ.

## Compatibilidade

Quando a fonte nao devolver JSON ou nao devolver UUID, o payload original segue
para a busca e o retorno posterior continua sujeito ao diagnostico existente.
Resultados, CAPTCHA, login, sessao ausente e respostas sem contrato continuam
com estados distintos.
