# TJES - Pesquisa De Jurisprudencia

Status atual: `candidate_needs_har` para a superficie legada; o portal atual
permanece `blocked_or_inconclusive` no probe limpo.

## Identidade Da Fonte

- Tribunal: Tribunal de Justica do Estado do Espirito Santo.
- Portal atual observado: `https://sistemas.tjes.jus.br/portaltj/Pesquisa.aspx`.
- Superficie legada com resultados: `https://aplicativos.tjes.jus.br/sistemaspublicos/consulta_jurisprudencia/cons_jurisp.cfm`.
- Detalhe/resultado observado: `https://aplicativos.tjes.jus.br/sistemaspublicos/consulta_jurisprudencia/det_jurisp.cfm`.

## Evidencia De Resultado

Uma pagina oficial de resultado indexada exibiu registros com:

- numero CNJ;
- classe;
- orgao julgador;
- data de julgamento e publicacao;
- relator e origem;
- ementa e conclusao.

Tambem existem ementarios trimestrais oficiais em PDF, que podem formar uma
fonte documental independente da busca interativa.

## Diagnostico E Lacunas

O portal atual `Pesquisa.aspx` sofreu timeout no mapeamento HTTP anterior. A
rota ColdFusion antiga ja foi encontrada em resultados oficiais, mas ainda
falta reproduzir a consulta, a paginacao, o detalhe e o documento em uma sessao
limpa. Nao tratar uma pagina indexada como contrato completo.

Classificacao: `candidate_needs_har`, evidencia `B` para a superficie legada e
`blocked_transport` para o portal atual.

## Promocao Futura

Capturar uma busca publica com filtros de justica, sistema, periodo e termo;
registrar a resposta de resultados e abrir um item real. Criar tambem um
provider documental separado para os ementarios PDF, sem misturar esse acervo
curado com a busca geral de acordaos.

## Validacao live 2026-08-11

- Portal atual sofreu timeout de leitura em 25 segundos; rota ColdFusion legada respondeu HTTP 404.
- Nenhuma busca, paginacao ou detalhe foi promovida. Ementarios PDF continuam sendo superficie documental independente.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/lucmolero/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Fontes Oficiais

- [Consulta de jurisprudencia do TJES](https://sistemas.tjes.jus.br/portaltj/Pesquisa.aspx)
- [Busca legada TJES](https://aplicativos.tjes.jus.br/sistemaspublicos/consulta_jurisprudencia/cons_jurisp.cfm)
- [Ementario trimestral oficial do TJES](https://www.tjes.jus.br/wp-content/uploads/Ementario_Trimestral_TJES_JAS_2024.pdf)
