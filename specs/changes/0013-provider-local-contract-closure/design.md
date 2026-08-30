# Design

O inventário será derivado do catálogo e do runtime, cruzado com dossiês,
contratos, fixtures e testes. Cada adapter será exercitado com entradas
determinísticas e sua saída será validada pelo contrato canônico. Falhas serão
classificadas por tipo; ausência de fixture será uma lacuna explícita.

Mudanças de provider seguirão a ordem documental definida em `AGENTS.md` e
atualizarão o catálogo somente via gerador. O relatório final conterá contagens
por estado, fontes da evidência e limitações.
