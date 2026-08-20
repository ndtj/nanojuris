# Gates de qualidade premium

Este documento define o mínimo operacional para tratar uma mudança como pronta
para revisão ou release. Os gates são cumulativos; passar no CI não equivale a
aceite de produto ou autorização de produção.

## Gate de especificação

- objetivo, fora de escopo, atores, falhas e compatibilidade estão explícitos;
- requisitos, critérios de aceite e tarefas possuem IDs estáveis;
- perguntas críticas e hipóteses têm resposta, prazo ou aprovador;
- mudanças grandes estão decompostas em pacotes menores;
- fontes externas e decisões relevantes estão registradas.

## Gate de arquitetura e segurança

- contexto, containers, integrações e implantação estão descritos de forma
  consistente com o runtime;
- limites de confiança, ativos, menor privilégio, secrets, logs e supply chain
  foram revisados;
- rollback, backup, restauração e comportamento sob falha estão definidos;
- nenhuma decisão presume bypass de CAPTCHA, WAF, login, rate limit ou controle
  de acesso.

## Gate de verificação

- cada requisito tem teste, comando ou evidência reproduzível;
- testes incluem caminho feliz, vazio, timeout, bloqueio e mudança de fonte;
- lint, tipos, segurança, build e documentação passam quando aplicáveis;
- divergências e riscos residuais estão explícitos, sem esconder `pending`.

## Gate operacional

- SLIs/SLOs são mensuráveis e honestos para o estágio atual;
- alertas acionáveis, runbook e dono operacional existem;
- o error budget influencia a decisão de release;
- produção, publicação e operações irreversíveis exigem aceite humano registrado.
