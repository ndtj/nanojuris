# Design

O parser eproc compartilhado valida identidade depois de extrair o ID técnico
e o número do processo. Se ambos faltarem, lança `ParserContractChangedError`.
Isso protege TJRJ, TJSC e demais membros da família sem duplicar lógica nos
adapters.

A auditoria é um artefato offline que lista a fonte da evidência por provider.
Fixtures de outro tribunal não são promovidas como prova específica de TJRJ ou
TJSC. Nenhum catálogo gerado é editado manualmente.
