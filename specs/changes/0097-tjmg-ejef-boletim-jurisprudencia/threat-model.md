# Threat model

## Riscos

- mudança do schema DSpace;
- PDF malformado, excessivo ou image-only;
- mistura acidental com outras coleções;
- leitura indevida como cobertura integral;
- excesso de chamadas à Biblioteca Digital.

## Controles

UUID fixo allowlisted, timeout e limite de tamanho, rate limit compartilhado,
validação de MIME/assinatura, trace por campo, `collection` explícita,
mensagem de escopo curado e nenhuma tentativa de contornar controles.
