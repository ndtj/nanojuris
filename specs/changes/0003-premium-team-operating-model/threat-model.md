# Threat model organizacional

## Riscos

| Risco | Controle |
| --- | --- |
| agente acumular autoridade demais | fases separadas e revisão cruzada |
| conhecimento ficar preso em uma conversa | artefatos SDD e handoff obrigatório |
| provider ser promovido por resposta ocasional | gate de maturidade e fixtures |
| dados canônicos perderem provenance | Data Quality Lead e traces obrigatórios |
| mudança insegura chegar à produção | Security/SRE review e aceite humano |
| métrica incentivar volume em vez de qualidade | scorecard pondera cobertura, completude e regressão |
| responsabilidade ficar ambígua | RACI e dono único por decisão |

## Ativos protegidos

- intenção de produto;
- contratos e dados canônicos;
- evidências de fonte;
- credenciais e configurações operacionais;
- disponibilidade e reputação do serviço;
- histórico de decisões e aprovação.

## Regra de confiança

Agentes produzem análise, código e evidência dentro do escopo concedido. A
autoridade final sobre domínio, risco, publicação e produção permanece com
responsáveis humanos registrados.
