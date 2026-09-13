# Design - detalhe lazy TJTO

## Estrategia de merge

O resultado da busca permanece a fonte de identidade inicial. O detalhe e uma
segunda observacao opcional, ligada por identificador estavel e URL oficial.
Campos vazios podem ser preenchidos somente quando o detalhe validar o mesmo
identificador; nenhum campo nao confirmado e inferido. O retorno carrega uma
marca de completude que distingue `base_only`, `enriched` e `partial`.

## Evidencia e contrato

O inventario Juscraper aponta a superficie `cjsg_ementa` no TJTO. Antes de
implementar, a rota, metodo, payload e resposta precisam ser reproduzidos em
HTTP publico limitado e registrados em fixture NanoJuris; a referencia upstream
nao e suficiente.

## Falhas e seguranca

Falha de detalhe nao invalida a busca: retorna base + outcome de enriquecimento.
403, CAPTCHA, WAF, TLS e timeout sao observaveis e nao sao retentados como
zero resultados.
