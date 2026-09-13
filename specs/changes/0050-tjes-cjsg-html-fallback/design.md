# Design - Fallback HTML TJES/CJSG

O parser existente continuara sendo a unica porta de entrada. A funcao de
normalizacao de documento escolhera primeiro o texto plano e, apenas quando
vazio, convertera o campo HTML correspondente com BeautifulSoup. O texto
normalizado vai para os campos canonicos; os campos planos e HTML permanecem
intactos em `raw`, junto de `summary_source` e `full_text_source`.

O fallback e puramente local e nao adiciona requisicoes. `SourceTrace` continua
registrando a resposta original, hash, tamanho e URL. Nenhum HTML recebido sera
persistido alem da fixture sanitizada.

## Seguranca e compatibilidade

- BeautifulSoup usa parser local sem rede;
- nenhuma URL e montada a partir do HTML;
- o identificador, `core` e o mapeamento TJES/CJSG nao mudam;
- consumidores que ja recebem texto plano observam o mesmo resultado;
- registros somente-HTML passam de vazio para texto parcial/completo de forma
  deterministica.
