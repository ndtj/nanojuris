# Modelo nacional de cobertura

## Unidade de contagem

A unidade básica não é “tribunal” nem “endpoint”. É uma **coleção jurídica
pesquisável** publicada por uma autoridade, por exemplo: acórdãos de segundo
grau, decisões monocráticas, sentenças de primeiro grau, súmulas, temas
repetitivos, informativos ou inteiro teor.

Cada coleção pode possuir uma ou mais superfícies técnicas ao longo do tempo.
Uma superfície é identificada por `authority_id`, `collection_id`,
`source_id`, método, host, rota, versão observada e período de validade.

## Ramos e famílias que compõem o denominador

| Família | Cobertura institucional mínima a inventariar | Observação |
| --- | --- | --- |
| Constitucional e superior | STF, STJ, TST, TSE e STM | decisões, precedentes qualificados, súmulas e informativos são coleções separadas |
| Federal | TRF1 a TRF6, TNU e CJF | separar jurisprudência de consulta processual PJe/eproc |
| Estadual | 26 TJs e TJDFT | mapear primeiro e segundo grau quando houver publicação própria |
| Trabalho | TST e TRT1 a TRT24 | hoje a cobertura NanoJuris não possui denominador completo |
| Eleitoral | TSE e 27 TREs | temas/compilações não substituem pesquisa textual primária |
| Militar | STM, TJM-MG, TJM-RS, TJM-SP e competência estadual residual | declarar quando a fonte é coleção própria ou integrada ao TJ |
| Precedentes e governança | CNJ, CJF, NUGEPNACs e bancos nacionais oficiais | contexto/precedente, não decisão primária por equivalência automática |
| Controle externo | TCU, TCEs e TCMs | dimensão administrativa separada da cobertura judicial |

O inventário definitivo deve ser gerado por 0036. Esta tabela define famílias;
não fixa antecipadamente uma cardinalidade sujeita a erro institucional.

## Dimensões obrigatórias de cobertura

- **institucional:** autoridade e ramo;
- **coleção:** tipo documental e grau;
- **temporal:** primeira e última data comprovadas, gaps e freshness;
- **material:** ementa, decisão, tese, inteiro teor e metadados;
- **consulta:** campos pesquisados, filtros, ordenação e limites;
- **paginação:** janela, total, cursor e completude;
- **operacional:** acesso observado, região, timestamp e validade da evidência;
- **interface:** SDK, CLI, MCP, Studio, store e exports;
- **jurídica:** identidade, versão, republicação, relação com processo e
  precedentes;
- **conformidade:** fonte oficial, termos, robots, licença e retenção.

## Estados separados

### Maturidade de engenharia

`mapped`, `contract_confirmed`, `fixture_verified`, `implemented`,
`quality_accepted`, `released`, `retired`.

### Saúde operacional

`not_checked`, `valid`, `empty_confirmed`, `degraded`, `rate_limited`,
`access_controlled`, `tls_error`, `schema_changed`, `unavailable`.

### Disposição do programa

`active`, `accepted`, `accepted_with_limitations`, `rejected`,
`deferred_with_review`, `out_of_scope`.

Os três eixos nunca devem ser colapsados em um único campo `status`.

## Métricas honestas

O dashboard deve publicar numerador, denominador e data para:

- instituições inventariadas;
- coleções mapeadas;
- coleções com contrato confirmado;
- providers com fixture e parser;
- providers aceitos no gate de qualidade;
- coleções com evidência live ainda válida;
- cobertura temporal conhecida;
- disponibilidade de inteiro teor.

Nenhuma dessas métricas, isoladamente, significa “todo o acervo brasileiro”.
