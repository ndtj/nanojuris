# Pesquisa — runtime compartilhado

Status: in_progress

## Evidência atual

O catálogo contém famílias e implementações independentes, enquanto mudanças
anteriores registram retries, caches e falhas repetidas. O risco principal é
unificar comportamento específico demais.

## Decisão orientada

Compartilhar somente política e transporte. Parsing, payload e interpretação de
resposta continuam pertencendo ao provider.

## Medições necessárias

- duplicação real de código;
- defaults atuais de timeout/retry;
- dependências e chamadas síncronas/assíncronas;
- impacto de cache nas interfaces.
