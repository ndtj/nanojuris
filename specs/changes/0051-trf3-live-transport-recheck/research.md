# Pesquisa - Rechecagem live TRF3

Em 2026-09-01 foram testadas, sem credenciais e com timeout de 6 segundos:

- `GET https://web.trf3.jus.br/acordaos/Acordao`;
- `GET https://web.trf3.jus.br/jurisprudencia/Home/ResultadoTotais`;
- `GET https://web.trf3.jus.br/jurisprudencia/Home/BuscarSugestao?term=dano`.

As três expiraram com `ReadTimeout`. A página inicial já havia sido observada
com HTTP 200 em uma varredura bounded anterior, mas isso não fechou o contrato
de submissão nem provou uma resposta de decisão. O artefato atual preserva as
duas evidências sem afirmar disponibilidade permanente.
