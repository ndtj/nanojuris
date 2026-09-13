# Modelo de ameaças

| Ameaça | Controle |
| --- | --- |
| Mistura entre primeiro e segundo grau | `core=pje1g` fixo e validação de `core_used` |
| Schema drift silencioso | erro `ParserContractChangedError` e fixtures negativas |
| Falha apresentada como zero resultados | classificação explícita de HTTP/transport |
| Excesso de carga na fonte | limite de 20, timeout e rate limit configuráveis |
| Vazamento de payload sensível em logs | trace só com metadados; sem headers/cookies |
| Redistribuição indevida | fonte opt-in e gate jurídico antes de escala |
