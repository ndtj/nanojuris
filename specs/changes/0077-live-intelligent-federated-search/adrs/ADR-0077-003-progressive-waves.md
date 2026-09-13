# ADR — atualização progressiva com congelamento por interação

ID: `ADR-0077-003`
Status: `accepted`
Data: `2026-09-07`

## Contexto

Fontes live terminam em tempos diferentes. Esperar todas piora tempo percebido;
reordenar depois que o usuário começou a ler pode causar erro de interação.

## Decisão

Renderizar ondas concluídas e recalcular o ranking enquanto não houver interação
intencional. Depois disso, congelar a ordem e oferecer aplicação manual do novo
ranking. Não depender de SSE na primeira versão.

## Alternativas consideradas

- esperar consolidação: estável, mas lento;
- reordenar indefinidamente: rápido, mas inseguro para leitura/clique;
- SSE/WebSocket: complexidade desnecessária no runtime Functions atual;
- concatenação de lotes: rápido, mas incorreto por relevância.

## Consequências

### Positivas

- primeiro resultado mais cedo;
- ordem final globalmente comparável;
- foco e leitor protegidos após interação.

### Negativas

- exige estado de geração/freeze no navegador;
- resultados podem se mover antes da interação;
- modo all continua sujeito a múltiplas chamadas.

## Evidência e revisão

- Browser acceptance deve provar respostas fora de ordem, cancelamento, freeze,
  seleção e atualização manual.
