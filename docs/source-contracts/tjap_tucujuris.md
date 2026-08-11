# TJAP - Tucujuris Jurisprudencia

Status atual: `blocked_or_inconclusive` para busca decisoria automatizada.

## Identidade Da Fonte

- Tribunal: Tribunal de Justica do Estado do Amapa.
- Familia tecnica observada: Tucujuris, com portal institucional e paginas
  publicas de consulta.
- Entrada historica: `https://tucujuris.tjap.jus.br/tucujuris/pages/consultar-jurisprudencia/consultar-jurisprudencia.html`.
- Entrada alternativa observada: `https://services.tjap.jus.br/pages/consultar-jurisprudencia/consultar-jurisprudencia.html`.
- Categoria: jurisprudencia estadual, turmas recursais e sumulas.

## Evidencia Observada

Registro institucional do CNJ descreve uma consulta integrada ao Tucujuris para
decisoes da Turma Recursal, orgaos do tribunal e sumulas, com acesso ao inteiro
teor, copia do acordao e ponte para a movimentacao processual.

O mapeamento tecnico anterior observou:

- o host `services.tjap.jus.br` sem resolucao DNS no ambiente de teste;
- o host `tucujuris.tjap.jus.br` respondendo desafio de JavaScript/Cloudflare;
- nenhum contrato HTTP limpo de busca, detalhe ou documento reproduzivel.

Esses sinais provam a existencia da superficie, mas nao autorizam provider live.

## Decisao De Mapeamento

Classificacao: `blocked_or_inconclusive`, evidencia `B/C`.

O NanoJuris deve preservar o candidato e nao simular ou contornar desafio,
captcha, WAF ou sessao de navegador. O eventual provider deve separar sumulas,
acordaos, detalhe e movimentacao, pois a fonte pode expor contratos distintos.

## Promocao Futura

Exigir HAR publico sem credenciais, resposta de busca com um item real, detalhe,
inteiro teor e comportamento vazio. Depois, reproduzir a chamada por HTTP limpo
com headers minimos e criar fixtures offline.

## Validacao live 2026-08-11

- A entrada Tucujuris respondeu HTTP 200, mas entregou shell HTML de 1.253 bytes sem sinais de resultado ou contrato decisorio.
- O estado permanece bloqueado/inconclusivo; nao foi inferido endpoint a partir do shell.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/lucmolero/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Fontes Oficiais

- [Consulta Tucujuris](https://tucujuris.tjap.jus.br/tucujuris/pages/consultar-jurisprudencia/consultar-jurisprudencia.html)
- [Consulta alternativa](https://services.tjap.jus.br/pages/consultar-jurisprudencia/consultar-jurisprudencia.html)
- [Registro institucional do CNJ](https://www.cnj.jus.br/sistema-moderniza-busca-de-jurisprudencia-em-tribunal-do-amapa/)
