# Clarificações e decisões pendentes

## Decisões já fechadas

- A fonte de verdade é gerada; catálogos em `docs/coverage` não são editados à
  mão.
- O produto cobre jurisprudência pública, precedentes, informativos e decisões;
  consulta processual pertence ao NanoJud.
- Falha de acesso jamais equivale a vazio.
- Não haverá solver de CAPTCHA, evasão de WAF, replay de token, stealth,
  rotação de IP ou endpoint privado.
- Não haverá índice documental próprio, embeddings, LLM ou reranking pago por
  consulta.
- Nenhum deploy, publicação ou alteração de produção ocorrerá neste pacote.

## Decisões que o responsável humano deve registrar

1. Termos de uso, licença, retenção e responsável por cada fonte.
2. Promoção padrão de cada provider tecnicamente aprovado.
3. Rótulos de relevância do benchmark (0–3) e conjunto de holdout.
4. Frequência de smoke live por família e orçamento de requests.
5. Tratamento de conteúdo que contém dados pessoais públicos.
6. Abertura de chamados aos tribunais para allowlist ou documentação de API.
7. Autorização formal de release/deploy, fora deste plano.

Uma tarefa `human_review` não pode ser marcada como concluída por inferência do
agente.
