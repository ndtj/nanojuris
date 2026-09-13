# Design — TJAP Banco de Sentenças

O adapter usa `requests.Session` configurada pela política compartilhada. A
busca faz um `GET /` para obter o snapshot do componente `pages.home.lista` e o
CSRF efêmero, seguido de `POST /livewire-53cc04b2/update` com a chamada pública
Livewire `__dispatch/update-filters`. O snapshot retornado é mantido apenas na
instância durante a paginação.

Filtros são traduzidos para a estrutura oficial observada:
`array`, `anos`, `search`, `tipo`, `sistema`, `match_phrase`, `date` e `banco`.
O parser trabalha sobre `effects.html`, identifica cartões por atributos
semânticos e extrai o RTF público do atributo Alpine `textToCopy` quando o
bloco visual de teor estiver recolhido. RTF é convertido de forma conservadora
para texto; conteúdo sigiloso permanece parcial.

O leitor `/reader/TUCUJURIS/<id>?tipo=banco-decisao|banco-sentenca` é buscado
apenas após uma URL observada no resultado. A resposta é um
`CanonicalDocument` com hash, trace e limite de host.

Total exibido como “aproximadamente” é `total_known=false`; a paginação local
continua limitada por `max_remote_page` e por repetição de identificadores.
