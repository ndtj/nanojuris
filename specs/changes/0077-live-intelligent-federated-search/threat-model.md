# Threat model — busca live inteligente

Mudança: `specs/changes/0077-live-intelligent-federated-search/spec.md`
Responsável: Platform Security
Status: `proposed`

## Ativos e limites de confiança

| Ativo | Classe | Origem | Proteção |
| --- | --- | --- | --- |
| consulta do usuário | potencialmente sensível | navegador | TLS, não persistir em telemetria |
| resultados jurídicos | público, pode conter PII pública | tribunais | projeção allowlisted e limites |
| token de sessão | confidencial | OCI Identity | cookie/header existente, nunca logar |
| plano de busca | interno | backend | validação, expiração e HMAC se autocontido |
| léxico/pesos | público versionado | repositório | review, testes e benchmark |
| telemetria | interna minimizada | plataforma | HMAC diário, TTL 30 dias, menor privilégio |

## Ameaças e controles

| ID | Ameaça | Impacto | Controle preventivo | Evidência | Residual |
| --- | --- | --- | --- | --- | --- |
| TH-001 | query/raw/PII em log | alto | logs estruturados allowlisted; HMAC; redaction | testes de captura de log | baixo |
| TH-002 | abuso multiplicando chamadas | alto | 12 fontes, 240 candidatos, 3 ondas, guard/rate limit | testes de limites | médio |
| TH-003 | plano adulterado chama fonte indevida | médio | recomputar/validar sources; token HMAC opcional | teste de tamper | baixo |
| TH-004 | resposta enorme/compressão abusiva | alto | transporte e projeção com limites existentes | testes de tamanho/MIME | baixo |
| TH-005 | XSS em razões ou conteúdo | alto | texto via DOM seguro, sem `innerHTML` | browser tests | baixo |
| TH-006 | resultado enganoso por score | alto | razões verificáveis, benchmark, versionamento | nDCG e testes de sinais | médio |
| TH-007 | fonte bloqueada tratada como vazio | alto | outcomes v2 e mapeamento obrigatório | testes 403/CAPTCHA | baixo |
| TH-008 | cache vaza consulta entre usuários | alto | chave scoped, TTL, sem endpoint de enumeração | testes de isolamento | baixo |
| TH-009 | fingerprint permite dicionário offline | médio | HMAC com secret e rotação diária | inspeção de schema | baixo |
| TH-010 | reordenação causa ação no item errado | alto | identidade estável, freeze ao interagir | testes E2E | baixo |
| TH-011 | expansão jurídica altera intenção | alto | léxico conservador, peso <= 0,4, chip removível | golden queries | médio |
| TH-012 | dependência de IA entra por acidente | médio | auditoria de imports/config e teste negativo | gate T52 | baixo |
| TH-013 | DoS por regex patológica | alto | regex compilada simples, limites de 300 chars | benchmark adversarial | baixo |
| TH-014 | stale cache parece live | médio | `cache_status`, idade e outcome preservados | testes TTL/stale | baixo |

## Regras de segurança obrigatórias

- Não armazenar query em claro em analytics.
- Não incluir raw, headers, cookies ou corpo de provider em razões.
- Não seguir rota, proxy ou source enviada pelo usuário fora do registro.
- Não contornar CAPTCHA, WAF, login ou rate limit.
- Não introduzir execução dinâmica a partir do léxico.
- Ausência do secret de telemetria desabilita coleta de métricas, nunca busca.

## Decisão de segurança

- [ ] Menor privilégio revisado após implementação.
- [ ] Logs, PII, cache e telemetria validados por testes.
- [ ] Abuso, supply chain e limites de rede avaliados.
- [ ] Riscos residuais aceitos antes de release.
