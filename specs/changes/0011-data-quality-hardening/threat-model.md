# Threat model

## Ativos

Identidade dos precedentes, completude dos resultados, traces de origem e
segredos de providers.

## Ameaças

- colisão de chaves mistura decisões distintas;
- falha silenciosa vira falso vazio;
- registro malformado interrompe lote válido;
- logs/quarentena expõem PII ou texto sensível.

## Mitigações

Chaves com escopo de fonte, classificação explícita de falhas, isolamento por
item, digests determinísticos e minimização de conteúdo nos traces. CAPTCHA,
WAF, login, TLS e rate limit continuam falhas observáveis.
