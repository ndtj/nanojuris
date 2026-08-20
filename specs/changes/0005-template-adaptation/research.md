# Pesquisa local e comparação

Status: `in_progress`

## Fontes locais

- Template: `C:\Users\luciano.finozzi\Downloads\sistema\segunda lib`.
- Produto: repositório NanoJuris atual.
- Evidências: código Python, testes, fixtures, catálogo e contratos versionados.

## Achados

O template oferece um parser lxml com CSS/XPath, geração de seletores,
similaridade e storage adaptativo; um engine de spiders com scheduler, limite,
robots, cache e checkpoint; e uma camada de exportação/estatísticas. O NanoJuris
já possui SourceTrace, ExtractionTrace, providers normalizados, SQLiteStore e
discovery bounded, mas essas capacidades ainda não formam um pipeline único.

## Hipótese de ganho

As maiores melhorias de produto vêm de reduzir duplicação nos parsers, aumentar
a tolerância controlada a mudanças de HTML e permitir coletas longas que possam
ser retomadas sem duplicar registros.

## Limites

Não serão incorporadas capacidades de stealth, rotação de proxy, perfis pessoais,
cookies privados ou resolução de desafios. Também não será feita cópia literal
da biblioteca externa; o código será reescrito/adaptado aos contratos locais.
