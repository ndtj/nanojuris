# Nivel Ouro de Pesquisa

O nivel Ouro do NanoJuris nao e uma contagem de providers. E um contrato de
qualidade para uma pesquisa publica que um advogado, pesquisador ou agente de
IA consegue auditar.

## Portao Ouro

Um provider so pode ser promovido quando todos os itens abaixo estiverem
comprovados no codigo, nos testes e no dossie:

1. rota publica reproduzivel sem cookie pessoal, login, captcha ou bypass;
2. payload, paginacao, limites e formato de resposta documentados;
3. sucesso, vazio, contrato alterado, rate limit e controle de acesso separados;
4. identificador estavel e campos canonicos com significado preservado;
5. inteiro teor somente quando a rota publica e o formato forem comprovados;
6. `SearchPage.pagination_mode`, `is_complete` e `completeness_reason` preenchidos
   de forma conservadora;
7. fixture de sucesso e vazio, testes de parser e teste live opcional controlado;
8. dossie canonico e copia legada sincronizados.

`is_complete=true` significa apenas que a janela retornada alcanca o total
autoritativo informado pela propria fonte. `false` significa que ha uma janela
parcial. `null` significa que a fonte nao ofereceu evidencia suficiente. Nunca
se deve inferir completude porque uma resposta veio curta.

## Frente atual

| Provider | Paginacao declarada | Inteiro teor | Estado Ouro |
| --- | --- | --- | --- |
| `tjdf_juris` | pagina | sim, por detalhe publico | busca pronta; detalhe em monitoramento |
| `tjpb_pje_jurisprudencia` | pagina | sim, rota publica testada | busca pronta; fixture/live a ampliar |
| `tjpa_jurisprudencia_bff` | pagina | texto no resultado; detalhe pendente | busca pronta; detalhe pendente |
| `tjrs_solr` | offset | detalhe pendente | busca pronta; detalhe pendente |
| `tjpi_juspi` | pagina | detalhe publico | busca pronta; contrato HTML monitorado |
| `tjgo_projudi_jurisprudencia` | pagina | texto embutido; download separado pendente | busca pronta; documento parcial |
| `tst_jurisprudencia` | offset | documento publico | busca pronta; HTML de detalhe monitorado |
| `stm_jurisprudencia` | offset | inteiro teor publico por UUID | busca pronta; HTML monitorado |
| `stj_informativo` | janela local observada | nota curada; acordao relacionado pode exigir outra rota | busca curada pronta |

Esta matriz e deliberadamente diferente de uma promessa de disponibilidade
permanente. Um tribunal pode mudar o contrato, ativar WAF ou ficar indisponivel;
nesse caso o resultado deve preservar o erro e reduzir a completude declarada.

## Como promover

Antes de chamar uma fonte de Ouro em release, rode:

```bash
python -m pytest -q tests/test_pagination.py tests/test_tjdf_juris.py \
  tests/test_initial_json_providers.py tests/test_tjpi_juspi.py \
  tests/test_tjgo_projudi_jurisprudencia.py tests/test_tst_jurisprudencia.py \
  tests/test_stm_jurisprudencia.py tests/test_stj_informativo.py
```

Depois registre uma validacao live com data, termo, status de cada fonte,
numero de resultados, `source_completeness`, latencia e erros. O relatorio nao
deve esconder fontes que falharam ou que foram ignoradas por capacidade.
