# Dossiês de providers

Esta é a coleção canônica de contratos humanos para as fontes de jurisprudência
do NanoJuris. Cada fonte tem um identificador estável e uma página própria:

```text
docs/providers/<source-id>/README.md
```

## Como usar este catálogo

### Para uma pessoa

1. Localize o `source-id` no [registry](../registry/providers.json).
2. Abra o dossiê correspondente nesta pasta.
3. Confirme o status, as capabilities e a data da evidência.
4. Leia limitações, comportamento de erro e contrato de documentos antes de
   usar a fonte em produção.

### Para um agente de IA

1. Carregue `docs/registry/providers.json`.
2. Resolva o campo `human_doc` para o dossiê desta pasta.
3. Trate `implemented` como disponível no pacote e `candidate` como pesquisa
   ou oportunidade, nunca como provider runtime.
4. Preserve no resultado as fontes consultadas, ignoradas, os erros e a
   rastreabilidade de cada resposta.

## O que cada dossiê documenta

Um dossiê completo cobre, mesmo quando algo ainda não foi observado:

- identidade, proprietário oficial e URL pública;
- acesso público e fronteira de uso responsável;
- rotas HTTP, métodos, payloads, parâmetros, filtros e paginação;
- campos disponíveis, normalização e campos instáveis;
- respostas de sucesso, vazio, erro, timeout e controle de acesso;
- fixtures e evidências sem cookies, tokens ou segredos;
- recomendação para CLI, SDK, Studio e MCP;
- lacunas atuais e próximo critério de promoção.

O [template de dossiê](../provider-dossier-template.md) define a estrutura
normativa para novas fontes.

## Status atual

O snapshot atual contém 54 dossiês:

| Status | Quantidade | Interpretação |
| --- | ---: | --- |
| Implementados | 37 | Adapter registrado e disponível no pacote |
| Candidatos | 16 | Fonte mapeada, ainda sem adapter runtime |
| Família | 1 | Especificação compartilhada para futuros adapters |

O [auditório documental](../provider-documentation-audit.md) mostra a
completude estrutural, a paridade com caminhos legados e a prontidão de cada
dossiê.

## Compatibilidade dos caminhos antigos

Os arquivos em `docs/source-contracts/<source-id>.md` continuam preservados para
links, bookmarks e agentes externos. A suíte de testes compara o dossiê
canônico com seu caminho legado enquanto essa camada de compatibilidade estiver
ativa. Alterações de contrato devem manter os dois caminhos sincronizados.

## Evidência não é garantia

Uma rota observada em um frontend ou HAR é diferente de uma resposta pública
reproduzida e diferente de um adapter pronto para runtime. Os relatórios de
validação registram exatamente essa diferença, além da data e do ambiente da
observação. Consulte também o [playbook de mapeamento](../route-mapping-playbook.md)
para entender como uma fonte é promovida.
