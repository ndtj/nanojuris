# Threat model

Referência: `specs/changes/0002-provider-discovery/spec.md`

## Ativos

- tokens e cookies que possam aparecer em headers;
- corpos brutos e documentos públicos capturados;
- allowlist e configuração de descoberta;
- integridade dos artefatos SDD;
- disponibilidade das fontes consultadas.

## Ameaças e controles

| Ameaça | Controle |
| --- | --- |
| SSRF para rede privada | rejeição de IP privado, loopback, link-local e destinos sem allowlist |
| Vazamento de segredo | redaction de headers, query e payload; nunca persistir credenciais |
| Crawl descontrolado | limite de páginas, profundidade, bytes, redirects e tempo |
| Confundir bloqueio com vazio | classificação explícita e teste de estados |
| Fixture excessiva | hash, amostra limitada e minimização antes do commit |
| Seletor semanticamente errado | confiança, múltiplas fixtures e revisão humana |
| Dependência browser indisponível | adaptador opcional e erro acionável |
| Alteração automática de provider | saída somente como draft e sem escrita no catálogo |

## Decisão de confiança

O worker de descoberta é ferramenta de pesquisa. Ele não recebe autoridade para
publicar provider, alterar produção, alterar catálogo gerado ou declarar
maturidade.
