# Design — cobertura estadual

## Unidade de entrega

Um provider por pacote SDD. Cada pacote entrega adapter, parser, capability,
fixtures, golden output, testes, dossier, source contract e decisão de
maturidade.

## Ondas

- onda 1: TJES, TJRJ ejuris, TJRN;
- onda 2: TJMG, TJRO textual;
- observação: TJAP permanece bloqueado enquanto Turnstile impedir automação
  pública responsável;
- onda 3: maturação dos runtime bronze/silver.

## Promoção

candidate -> experimental -> bronze -> silver -> gold.

Promoção não é automática por teste único. Regressão ou acesso controlado pode
reduzir disponibilidade sem apagar o histórico.
