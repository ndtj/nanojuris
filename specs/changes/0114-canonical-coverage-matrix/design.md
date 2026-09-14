# Design

`authority-registry.yaml` define identidade institucional. `coverage-matrix.yaml`
define superfícies e bindings. Ambos usam YAML compatível com JSON e possuem
JSON Schema, permitindo validação sem dependência de runtime.

O gerador combina essas fontes com `ProviderCapabilities`/catálogo operacional.
Dados técnicos continuam no contrato do provider e são materializados na matriz
com proveniência, sem criar outra declaração manual concorrente.

As projeções públicas são `coverage-matrix.json`, `coverage-matrix.md`, o bloco
marcado do README e executor packets. O modo `--check` compara bytes e falha em
qualquer divergência.
