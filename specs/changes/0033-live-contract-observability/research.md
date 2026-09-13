# Pesquisa — observabilidade live

Status: in_progress

## Evidência atual

Mudanças 0006 e 0007 já executam discovery bounded e distinguem estados. O novo
pacote deve transformar a prática em operação repetível, sem criar load test ou
dependência de rede na CI.

## Decisão orientada

Separar qualidade offline, última evidência live e disponibilidade do serviço
externo. Toda observação tem validade temporal.

## Lacunas

- orçamento por host;
- frequência por tier;
- destino e retenção de artefatos;
- dono e escalonamento de alertas.
