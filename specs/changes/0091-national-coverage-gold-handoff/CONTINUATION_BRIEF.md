# Brief de continuidade para outro modelo

Este brief acompanha o SDD 0091 e transforma o pacote em uma entrada operacional
única. Ele não substitui os documentos normativos nem autoriza release.

## Começo obrigatório

No diretório `repos/nanojuris`, leia `AGENTS.md`, `specs/constitution.md`,
`specs/README.md`, `docs/coverage/README.md` e todos os arquivos deste diretório.
Depois regenere o baseline; o snapshot serve apenas para orientação. O manifesto
`handoff-artifact-manifest.json` enumera os arquivos, gates, estados e comandos
que devem permanecer sincronizados.

## Estado de referência

O último baseline local registrou 71 fontes catalogadas, 66 providers em runtime,
49 fontes declaradas na busca unificada, CJPG comprovado em 7/27, CJSG em 25/27
e 57 tarefas abertas (0 locais, 44 dependentes de fonte externa e 13 humanas).
Esses números não significam disponibilidade nacional, aprovação jurídica ou
conclusão. Execute `tools/audit_open_tasks.py` e os geradores antes de escolher
um lote.

## Ordem de execução

1. **G0/G1:** reconciliar catálogo, runtime, live, qualidade e federação; separar
   `total_zero`, `total_unknown`, bloqueio e schema inválido.
2. **G2:** pesquisar CJPG por tribunal. Só contar jurisprudência textual de
   primeiro grau; processo, DataJud, catálogo e contexto não bastam.
3. **G3:** concluir CJSG dos 27 TJs, preservando TJAP/TJCE/TJPE/TJSP quando
   bloqueados e revisando TJMG/TJMA/TJSE sem inventar endpoints.
4. **G4:** tratar TRT/TST, TSE/TRE, TRF, STJ, STF, STM, CJF e eproc federal
   em contratos próprios.
5. **G5:** validar filtros, paginação, datas, identidade, detalhe, documentos,
   MIME, hash, extração e proveniência.
6. **G6/G7:** executar smoke federado opt-in, promover somente os oito gates,
   configurar drift, TTL, shadow mode e rollback. Sem deploy.
7. **G8:** deixar decisões de relevância, licença, retenção, responsável,
   allowlist, publicação e produção para aprovação humana explícita.

Trabalhe em lotes de um a três providers. Faça uma chamada de descoberta pública
bounded e, somente se válida, uma confirmação. Registre URL, método, payload
sanitizado, status, host final, MIME, bytes, classificação, trace e fixture.
Gere `verification.md` por lote e regenere os inventários no fechamento.

## Fronteira de acesso

Podem ser usados API/export oficial, fluxo anônimo padrão, cookies/CSRF efêmeros
da sessão corrente, redirects allowlisted, paginação publicada, `Retry-After`,
retry transitório, `ETag`/`Last-Modified`, documentos oficiais, egress fixo
aprovado e suporte/allowlist formal. Um desafio pode ser mediado manualmente
sem persistir token ou cookie.

É proibido solver, OCR do desafio, stealth, spoofing, rotação de IP/proxy,
replay de cookies/tokens, fuzzing privado, bypass de login, desativar TLS,
exaustão de rate limit ou alterar termos/robots. CAPTCHA, Turnstile, WAF, 403,
429, timeout, TLS, endpoint privado e schema inesperado são estados explícitos;
nunca `authoritative_empty`. Após bloqueio estável, registre uma evidência,
procure uma alternativa oficial e avance.

## Gate de promoção

Uma superfície só entra na federação quando possui fonte oficial, contrato de
grau/coleção, adapter, fixtures, filtros/paginação, chamada live bounded,
qualidade canônica e smoke federado. `implemented`, `live_validated`,
`federation_enabled` e `legal_status` permanecem dimensões independentes.

## Condição de conclusão honesta

Só afirmar 27/27 com `complete_8_of_8 == 27`, nenhum workpack `pending`, fixtures,
contrato, live e smoke para cada autoridade, e zero bloqueios ou decisões humanas
pendentes. Caso contrário, entregar a tabela de bloqueios e a ação externa
necessária. Não fazer commit, push, tag, release, OCI, Terraform ou deploy.
