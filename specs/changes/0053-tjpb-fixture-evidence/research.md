# Pesquisa - Evidencia local TJPB/PJe

O dossie registra uma observacao live anterior de busca publica com HTTP 200 e
10 hits, mas o corpo nao foi persistido. O teste existente reproduzia o
envelope apenas em memoria, o que impedia replay e auditoria de proveniencia.

Foi escolhida uma fixture sintetica, sem nomes reais e sem copiar resposta live.
Ela cobre apenas o contrato estrutural observado (`total`, `hits`, `_id`,
`dt_ementa`, `ementa` e `numero_processo`). A disponibilidade atual continua
dependente de nova chamada publica bounded.
