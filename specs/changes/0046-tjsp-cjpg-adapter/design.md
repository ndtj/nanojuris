# Design - TJSP CJPG

O adapter mantem uma sessao requests configurada pelo contrato NanoJuris. Para
pagina 1, faz `GET /cjpg/pesquisar.do`; para paginas seguintes, repete a busca
inicial para estabelecer a sessao e chama `GET /cjpg/trocarDePagina.do`.

O parser procura `#divDadosResultado` e `tr.fundocinza1`, valida ancora com
identificador tecnico e extrai labels `Classe`, `Assunto`, `Magistrado`,
`Comarca`, `Foro`, `Vara` e `Data de Disponibilizacao`. O texto escondido na
div de decisao e tratado como inteiro teor inline e um prefixo limitado e usado
como resumo, sem chama-lo de ementa.

O contrato declara `collection=first_degree;route=cjpg`, categoria
`specialized_context`, `supports_unified_search=False`, pagina fixa de 10 e
sem detalhe independente. Erros de acesso e de parser interrompem a operacao
com excecao tipada e trace de transporte; jamais retornam lista vazia.
