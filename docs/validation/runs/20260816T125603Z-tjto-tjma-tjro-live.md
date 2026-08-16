# Validacao live: TJTO, TJMA e TJRO

Data: 2026-08-16 12:56 UTC. Execucao pelo cliente NanoJuris, com chamadas
publicas controladas e sem cookies, tokens privados ou bypass de controles.

## TJTO

`POST /consulta.php` retornou HTTP 200 para `transporte aereo dano moral`, com
95.942 resultados reportados e cinco itens na primeira pagina. A segunda pagina
retornou cinco identificadores novos. O primeiro documento foi carregado sob
demanda pelo identificador publico `uuid`.

O documento retornou `text/html`, 3.458.562 bytes e 65.584 caracteres extraidos,
com SHA-256 `9e3275a260aec1be9279c3024819d61074682e061b8d9bb42bebcc6a9c05f948`.
Portanto o provider declara inteiro teor HTML carregado, nao PDF.

## TJMA

Os endpoints publicos de catalogo retornaram HTTP 200. Foram normalizados sete
especies de relatorio, 135 classes e 313 magistrados na rodada. A rota de busca
principal continua explicitamente `access_control_required`: ela exige os
parametros de desafio `tokenG` e `keyId`. Nenhuma tentativa de automacao do
captcha foi feita.

## TJRO

`POST /api/pesquisa/precedentes` retornou HTTP 200 para `empreitada`, com um
precedente qualificado. O provider permanece fora da busca textual unificada,
porque seu escopo e precedentes qualificados e nao o acervo geral de acordaos.
