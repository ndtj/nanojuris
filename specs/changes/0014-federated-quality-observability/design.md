# Design

O cliente federado canonicalizará resultados individualmente, agregando erros
por fonte sem interromper itens válidos. Uma função central limitará mensagens
de exceção e removerá padrões de segredo. A métrica de persistência será
explicitamente nomeada/documentada conforme o contrato existente, evitando
mudança silenciosa de semântica.

A rastreabilidade de fixtures será derivada de caminhos e referências reais;
nenhuma rota ou fixture será criada por inferência.
