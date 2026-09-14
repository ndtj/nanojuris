# Verification

Implementação local concluída. A validação live bounded foi executada em
`https://diario.tjse.jus.br/revista/internet/pesquisar.wsp` e
`principal.wsp`, com termo `responsabilidade`, edição 159 e seção 2ª Câmara
Cível. O retorno foi HTTP 200 e continha ementas, processos, acórdãos e
relatores. O total global entre edições permanece desconhecido; por isso a
promoção federada padrão não é inferida neste pacote.

## Resultados

- Fixtures e parser: testes focados aprovados.
- Live: adapter retornou ementa pública de segundo grau (HTTP 200).
- Promoção técnica: habilitada; sem commit, push ou deploy.

## Rastreabilidade

- REQ-001/AC-003: `tests/test_tjse_boletim_jurisprudencia.py`.
- REQ-002/REQ-003/AC-001: parser e fixture principal.
- REQ-004/AC-002: fixture de schema alterado e erros explícitos.

## Evidência live adicional — 2026-09-07

Uma nova chamada pública bounded foi executada com `responsabilidade`,
`degree=second`, `instance=second`, `branch=state` e `authority=TJSE`. A fonte
retornou HTTP 200 e 10 ementas textuais da seção recursal, cada uma com
`degree=second`, `instance=second`, `collection=CJSG`, tipo `acordao` e link
público de documento. O artefato redigido é
`docs/provider-discovery/tjse-boletim-jurisprudencia-live-20260907.json`.

O corpo principal teve 6.788.554 bytes e a chamada de busca mais detalhe levou
aproximadamente 16,8 s; isso fica registrado para a decisão de orçamento e
latência da federação. O detalhe oficial foi recuperado por HTTPS, HTTP 200,
com 59.565 caracteres e hash SHA-256 redigido no artefato. O provider preserva
`total_known=false`, pois a fonte organiza o resultado por edição/seção e não
fornece total global entre edições. Nenhum CAPTCHA, token, cookie, WAF ou
controle de acesso foi contornado. A evidência confirma a superfície CJSG
pública, mas não fecha os gates nacionais de primeiro grau nem o total global
do TJSE.
