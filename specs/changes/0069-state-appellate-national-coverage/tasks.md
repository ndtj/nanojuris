# Tarefas

- [x] T01 - definir o contrato nacional 27/27 e os oito gates por superficie.
- [x] T02 - implementar o gerador deterministico de workpacks CJSG.
- [x] T03 - adicionar testes de cardinalidade, identidade, estados e tarefas.
- [x] T03A - preparar prompt mestre autocontido para o modelo executor.
- [x] T04 - concluir os workpacks `contract_hardening` gerados (nenhum workpack
  dessa ação permanece no programa regenerado).
- [x] T05 - implementar os workpacks `adapter_discovery` gerados. Adapters
  diagnósticos de TJMA e TJSE foram implementados com estados de acesso
  explícitos; promoção permanece bloqueada quando a fonte exige desafio.
- [x] T06 - revalidar legitimamente os workpacks `blocked_recheck` gerados.
  TJAP e TJMG foram rechecados em 2026-09-06; ambos possuem evidência
  bounded explícita de `access_controlled`, sem conversão para vazio ou
  tentativa de contorno. O estado continua bloqueado até existir rota pública
  reproduzível. A alternativa oficial Ementário Trimestral do TJMG foi
  avaliada; é um repositório de PDFs curatoriais sem consulta geral/filtros
  reproduzíveis, portanto não substitui o CJSG protegido. Evidência estruturada:
  `docs/provider-discovery/tjmg-ementario-alternative-live-20260906.json`.
- [ ] T07 [blocked-external: TJAP/TJMA exigem CAPTCHA/Turnstile ou rota oficial alternativa; rechecagens 2026-09-07 registradas em docs/provider-discovery/legitimate-blocked-techniques-20260907.json e docs/provider-discovery/tjma-public-route-inventory-live-20260907.json]
  Evidencias de rechecagem sem bypass: `docs/provider-discovery/blocked-browser-session-recheck-20260907.json`,
  `docs/provider-discovery/tjap-official-alternatives-live-20260907.json`,
  `docs/provider-discovery/tjap-pje-2g-alternative-live-20260907.json`,
  `docs/provider-discovery/tjma-official-alternatives-live-20260907.json`,
  `docs/provider-discovery/tjap-repository-alternatives-live-20260907.json` e
  `docs/provider-discovery/legitimate-blocked-techniques-20260907.json`.
  O inventario do shell/API publico do TJMA tambem confirmou as superficies
  CJSG e CJPG e o filtro de inteiro teor, mas as rotas de resultados continuam
  `captcha_required`; evidencia:
  `docs/provider-discovery/tjma-public-route-inventory-live-20260907.json`.
  A auditoria de `lib template` confirmou que somente navegacao publica,
  observacao redigida e parsing podem ser reutilizados; stealth, solver,
  fingerprint spoofing e proxy rotation nao sao tecnicas permitidas. Evidencia:
  `docs/provider-discovery/lib-template-technique-audit-20260907.json`.
  O shell publico e catalogos foram avaliados; as rotas de resultados continuam
  condicionadas a desafio validado no servidor. Permanecem fora da federacao.
  - atingir 27/27 superfices live-validas e consultaveis. Permanece
  aberto exclusivamente por bloqueios externos reproduzidos em TJAP (Turnstile),
  TJMA (CAPTCHA da API); TJMG possui superficie DSpace publica alternativa
  integrada e validada nesta rodada; TJSE possui superficie alternativa
  publica de Boletim Juridico integrada nesta rodada. Nenhuma
  tentativa de contorno e permitida. A rechecagem de 2026-09-07 também
  confirmou a página oficial do TJAP (HTTP 200), o envelope de segurança do
  endpoint sem token, a entrada legada (shell Angular) e a falha DNS do host
  alternativo; evidência em
  `docs/provider-discovery/tjap-official-alternatives-live-20260907.json`.
  TJMA também foi rechecado em 2026-09-07 (catálogos públicos, shell oficial e
  rotas documentadas); resultados permanecem protegidos por CAPTCHA, conforme
  `docs/provider-discovery/tjma-official-alternatives-live-20260907.json`.
- [x] T08 - habilitar na federacao apenas as superficies que passarem os oito
  gates, preservando diagnostico das demais.
- [x] T09 - executar revalidacao periodica e tratar regressao/schema drift.
  O workflow semanal `live-validation.yml` mantém a revalidação bounded; a
  rodada de 2026-09-06 consultou as 42 fontes do manifesto, registrou dois
  erros externos (CNJ HTTP 503 e TST HTTP 400) sem convertê-los em vazio e
  preservou a coleção como incompleta. Evidência:
  `docs/provider-discovery/federated-promotion-live-20260906-current.json`.

Dependencias: T01 -> T02 -> T03 -> (T04, T05, T06) -> T07 -> T08 -> T09.

Os itens T04-T09 sao expandidos por tribunal no artefato gerado; este arquivo
nao duplica manualmente 216 linhas de tarefas.
