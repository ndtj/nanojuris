# Tarefas

- [x] T01 - inventariar modelos e facades publicas atuais.
- [x] T02 - publicar esquema e matriz de compatibilidade v1/v2.
- [x] T03 - implementar capabilities e outcomes tipados, alem de metadados de pagina.
- [x] T04 - implementar um compatibility adapter de ponta a ponta.
- [x] T05 - migrar dois providers representativos sem alterar a saida publica.
- [x] T06 - criar testes de serializacao, erro, unknown e regressao.
- [x] T07 - atualizar contrato e documentacao de adocao incremental.
- [x] T08 - executar gates completos apos a integracao do ciclo.

Dependencia: T01 -> T02 -> T03 -> T04 -> T05 -> T06 -> T07 -> T08.

Evidencia T05: `bnp_pangea` preserva a lista v1 de filtros e declara
semantica v2 nativa; o fixture `bnp_precedentes_species.json` contem seis
identificadores nativos estaveis e a canonicalizacao preserva
`CanonicalPrecedent`. `stj_scon` preserva os filtros v1 e declara ordenacao e
detalhe v2; `stj_scon_acordaos_result.html` contem dois registros nativos
estaveis, ambos mapeados para `CanonicalDecision`. As assinaturas e os campos
legados nao foram removidos. Nenhuma promocao live e inferida apenas por uma
chamada: a evidencia combinada e fixture + testes offline + smoke live
opt-in.
