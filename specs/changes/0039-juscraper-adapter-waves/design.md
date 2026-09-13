# Design — ondas Juscraper

## Onda A — ganho direto

- TJES CJSG, reconciliando 0025;
- TJRN CJSG;
- TJRO jurisprudência textual;
- TJTO detail/ementa lazy.

## Onda B — hardening diferencial

TJPB, TJCE, TJPE, TJGO, TJMT, TJPA, TJSC, TJRS, TJPR, TJRR, eSAJ e demais
overlaps. O relatório compara request, parser, campos, identidade, paginação e
erros. Ausência de ganho encerra como `no_gain`, não força mudança.

## Onda C — primeiro grau

TJES, TJSP e TJTO CJPG recebem source IDs e contratos separados. A turma
recursal TJES recebe outro binding. O parser pode ser compartilhado, mas
fixtures, capabilities, períodos e identidade não.

## Onda D — alto risco

TJAP e TJMG ficam bloqueados. TJRJ ejuris requer confirmação de acesso público
sem depender da alegação de que CAPTCHA não é validado.

## Adaptação

Preferir reimplementação mínima do contrato observado. Cópia substancial exige
NOTICE/cabeçalho e revisão. Fixtures upstream são evidência; a fixture NanoJuris
deve ser minimizada e obtida legitimamente da fonte oficial quando possível.

O plano executável e as reservas de pacotes estão em
`implementation-manifest.md`.
