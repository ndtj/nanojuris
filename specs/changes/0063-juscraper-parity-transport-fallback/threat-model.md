# Threat model

## Riscos

- Repetições excessivas podem pressionar fonte pública.
- ViewState/cookies podem vazar em logs ou artefatos.
- Uma página de bloqueio pode ser interpretada como resultado.
- O TLS legado pode ser confundido com autorização para desativar validação.

## Mitigações

- Limite fixo de tentativas e atraso mínimo configurável.
- Não registrar payloads secretos; somente presença/tamanho e hashes.
- Parser exige marcadores de resultado e lança erro em HTML inesperado.
- `verify_ssl` permanece verdadeiro por padrão e em testes.
- Sem Playwright, login, CAPTCHA ou alteração de controles externos.
