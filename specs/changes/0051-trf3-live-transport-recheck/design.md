# Design - Rechecagem de transporte TRF3

O ciclo usa três GETs oficiais independentes para evitar que uma única rota
seja tomada como representante de todo o serviço. Cada resultado é um registro
de evidência com timeout explícito, sem persistir HTML, cookies ou tokens.

O estado de produto continua candidato: `blocked_transport` descreve o
ambiente de execução desta rodada e não altera a semântica jurídica da fonte.
Uma futura captura pública normal deverá fornecer action/payload, resposta,
paginação e identificadores antes de qualquer adapter.
