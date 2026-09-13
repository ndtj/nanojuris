# Threat model — programa de providers

Status: pending

## Ativos e limites

| Ativo | Classificação | Risco principal | Controle |
| --- | --- | --- | --- |
| contratos de fonte | público/interno | rota incorreta ou obsoleta | evidência e revisão |
| fixtures | público minimizado | dados pessoais ou conteúdo excessivo | sanitização e hash |
| respostas HTTP | transitório | conteúdo hostil ou muito grande | limites e parsing defensivo |
| traces e logs | interno | token, cookie, query ou PII | redaction e minimização |
| dependência externa | supply chain | código vulnerável ou incompatível | pin, SBOM, licença e auditoria |
| inteiro teor | público com alto volume | malware, zip bomb, formato inesperado | allowlist, limite e quarentena |

## Ameaças

| ID | Ameaça | Impacto | Controle obrigatório |
| --- | --- | --- | --- |
| TH-001 | SSRF por URL derivada da fonte | alto | host allowlist e redirect validation |
| TH-002 | exfiltração em logs | alto | redaction estrutural e testes |
| TH-003 | bypass de controle de acesso | alto | policy deny e revisão humana |
| TH-004 | supply-chain ao copiar código | alto | licença, diff, SBOM e testes |
| TH-005 | payload malicioso ou excessivo | alto | tamanho, content type e sandbox de parser |
| TH-006 | false empty por WAF/HTML | alto | classificação de acesso e schema |
| TH-007 | poisoning de cache | médio | chave completa, hash e isolamento por provider |
| TH-008 | colisão de identidade | alto | identidade source-aware e testes |
| TH-009 | sobrecarga da fonte oficial | alto | bounded concurrency, budget e backoff |
| TH-010 | fixture com dados pessoais | médio | minimização, revisão e remoção |

## Riscos residuais

Disponibilidade e mudança de portal permanecem fora do controle da NanoJuris.
O sistema deve torná-las observáveis, não prometer eliminá-las.
