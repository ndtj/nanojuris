# Threat model

## Riscos

- Um dossier pode conter contrato desatualizado ou uma URL que não está mais
  disponível.
- Uma sugestão estrutural pode ser confundida com parser correto.
- Fixtures podem conter dados pessoais ou conteúdo desnecessário.
- Um relatório de ausência pode ser interpretado como prova de ausência na fonte.

## Controles

- A auditoria é offline-only e não possui caminho de rede.
- A ausência de fixture é um estado explícito.
- Rotas e seletores são hipóteses revisáveis, não alterações de provider.
- O relatório registra bytes, status e amostras limitadas.
- Promoção exige mudança separada, revisão e testes.
