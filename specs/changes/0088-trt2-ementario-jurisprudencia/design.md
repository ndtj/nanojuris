# Design

```text
índice oficial -> seleção determinística de tópicos -> HTML da ementa
             -> CanonicalDecision -> link PDF observado -> CanonicalDocument
```

O índice e os tópicos são consultados live por chamada bounded; nenhum corpus
é persistido nem pesquisado localmente. A seleção prioriza termos presentes no
label oficial e limita a 32 páginas. A resposta usa `local_window`,
`total_known=false` e `is_complete=false`.

Redirects são aceitos somente no host oficial `trt2.jus.br`. O transporte
compartilhado mantém TLS, rate limit, timeout e classificação de bloqueio.

