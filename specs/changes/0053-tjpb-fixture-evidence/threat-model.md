# Threat model

- **Proveniencia:** valores da fixture sao explicitamente sinteticos e nao
  podem ser apresentados como jurisprudencia do TJPB.
- **Privacidade:** nao ha nomes de partes, cookies, tokens ou identificadores
  reais.
- **Integridade:** o teste verifica id, numero, data, ementa e URL de detalhe.
- **Acesso:** nenhum WAF, CAPTCHA, rate limit ou login e contornado.
- **Operacao:** a mudanca e offline; nao dispara deploy, push ou federacao.
