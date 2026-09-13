# Design - TRT2 PJe diagnostico

O adapter usa `SharedHttpClient` com allowlist do host `pje.trt2.jus.br`,
`max_bytes=2_000_000`, timeout configurado e sem retry de POST. A rota de
opcoes e a rota de filtros possuem metodos explicitos para diagnostico. A rota
de documentos aceita apenas JSON; envelopes que contenham `tokenDesafio`,
`imagem` ou `audio` terminam em erro de controle de acesso.

Se a fonte futuramente responder com uma lista de documentos, o parser aceita
somente registros com identificador estavel e preserva os campos nativos em
`raw` e `SourceTrace`. O grau de segundo grau vem do escopo oficial da
superficie, nao de uma inferencia de texto.

O adapter e registrado somente quando
`NanoJurisClient(include_candidate_providers=True)` e nunca e incluido no
roteamento federado padrao.
