# Validacao De Contratos De Providers 2026-08-12

Rodada tecnica de validacao de fontes publicas de jurisprudencia para
confirmar busca, paginacao, inteiro teor e limites antes de ampliar o
contrato dos providers. As chamadas foram pequenas, com SSL habilitado, sem
login, cookies pessoais, captcha ou mecanismo de contorno.

Os numeros abaixo sao observacoes da rede no momento da execucao. Nao sao
garantia de disponibilidade, SLA ou cobertura integral.

## Resultados live

| Provider | Consulta | Resultado observado |
| --- | --- | --- |
| `tst_jurisprudencia` | `responsabilidade civil`, page size 2 | HTTP 200, total observado de 841870, dois registros; inteiro teor HTML publico recuperado |
| `trf4_eproc_jurisprudencia` | `aposentadoria`, page size 2 | HTTP 200, cards HTML e inteiro teor publico; a pagina tambem expos total remoto e tamanhos 10/25/50/100 |
| `stm_jurisprudencia` | `indulto`, page 1 e 2, page size 2 | HTTP 200, total 1017; paginas diferentes; inteiro teor HTML publico recuperado |
| `tjdf_juris` | `dano moral`, page size 2 | HTTP 200, total observado de 138527 no fluxo HTML existente |

## Consequencias para a arquitetura

### STM

O provider foi corrigido para enviar `start` zero-based e `rows` na propria
consulta, em vez de buscar a primeira pagina e recortar localmente. O parser
tambem reconhece o marcador publico `1 - 2 de N documentos` e preenche o total
remoto. Facetas de classe, assunto, relator, revisor e datas foram observadas e
documentadas, mas ainda nao foram inventadas como filtros do modelo unificado.

### TRF4

O formulario oficial possui contrato mais rico que o adapter atual: origem,
tipo documental, texto integral/ementa, processo, precedente relevante,
agrupamento, classe, duas datas, relator, orgao julgador e assuntos. O resultado
exibe total remoto e a rota AJAX de paginação. A rota foi documentada, mas nao
foi promovida a implementacao porque um replay sem o estado completo do
formulario retornou a moldura de resultados sem cards. Isso e uma lacuna
honesta para fixture e teste, nao uma falha escondida.

### TST e TJDFT

O TST continua sendo o melhor contrato REST implementado para filtros e
inteiro teor. O TJDFT possui uma superficie JSON oficial adicional, com
`query`, pagina zero-based, tamanho e `termosAcessorios`; ela permanece como
trabalho de integracao do provider HTML existente, sem criar um segundo
provider para o mesmo tribunal.

## Proxima etapa tecnica

1. Versionar fixtures pequenas e sem sessao para STM e TRF4.
2. Expor filtros TRF4 de classe, relator, orgao, assunto e precedente somente
   depois de ampliar `JurisprudenceQuery` ou criar filtros especificos por
   provider.
3. Reproduzir `ajax_paginar_resultado` com o formulario completo e testar
   pagina 2, vazio e erro.
4. Descobrir os endpoints dos modais STM de referencia legislativa, notas e
   indexacao antes de adiciona-los ao MCP.
5. Implementar a superficie JSON do TJDFT com comparacao de cobertura contra o
   fluxo HTML.

## Fontes oficiais usadas

- [Jurisprudencia do TRF4](https://www.trf4.jus.br/trf4/controlador.php?acao=pagina_visualizar&id_pagina=3938)
- [Busca publica eproc/TRF4](https://eproc-jur.trf4.jus.br/eproc2trf4/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar)
- [Consulta de Jurisprudencia do STM](https://jurisprudencia.stm.jus.br/consulta.php?search_filter_option=jurisprudencia)
- [Pesquisa de Jurisprudencia do TST](https://jurisprudencia.tst.jus.br/)
- [API de dados abertos do TJDFT](https://www.tjdft.jus.br/transparencia/tecnologia-da-informacao-e-comunicacao/dados-abertos/webservice-ou-api)
