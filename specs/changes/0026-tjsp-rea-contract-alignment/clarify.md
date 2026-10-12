# Clarify

- `Q-001`: o SAJ pode funcionar sem CAPTCHA em uma sessão pública válida?
  **Resposta operacional:** sim, quando a fonte entrega resultado; quando a
  fonte entrega CAPTCHA/controle, o provider deve parar e informar o motivo.
- `Q-002`: `casChecked=true` é bypass? **Decisão:** não será usado para superar
  CAPTCHA/login; somente como segunda chamada da sequência pública observada,
  com fail-closed se a fonte não liberar o documento.
- `Q-003`: devemos mapear filtros livres para selects internos do eproc?
  **Decisão:** não sem resolução de opções observada; nomes livres não serão
  enviados como valores arbitrários.
