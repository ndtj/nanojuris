# TJSE Boletim Jurídico (CJSG)

## Identity

- Tribunal: Tribunal de Justiça do Estado de Sergipe (TJSE).
- Fonte oficial: https://www.tjse.jus.br/portal/publicacoes
- Pesquisa: https://diario.tjse.jus.br/revista/internet/pesquisar.wsp
- Escopo: ementas publicadas de órgãos de segundo grau.

## Dados

O formulário aceita palavra-chave e intervalo de publicação. A resposta lista
edições e seções; principal.wsp fornece linhas de classe e ementas com
processo, acórdão e relator quando publicados. A data da edição é normalizada
como publication_date.

## Rotas

1. GET /revista/internet/pesquisar.wsp para carregar o formulário e token
   efêmero.
2. POST /revista/internet/pesquisar.wsp com datas e palavra-chave; a resposta
   contém verSecao(edição,caderno,seção) para cada publicação.
3. POST /revista/internet/principal.wsp com edição e seção; a tabela contém
   linhas de classe e linhas de ementa com links respnumprocesso.wsp e
   jurisprudencia/relatorio.wsp.
4. O link público de jurisprudencia/relatorio.wsp é consultado sob demanda
   por get_decisions/get_document; o relatório visível é preservado quando
   disponível e a ementa permanece como fallback.

## Semântica

As linhas com processo/acórdão são decisões textuais de segundo grau. O título
da classe anterior é preservado em case_class; a data do Boletim é
publication_date. A consulta é limitada a uma edição/seção e o total entre
edições permanece desconhecido.

## Estados

HTTP 401/403/407/451 e 429 são estados explícitos; timeout, TLS e HTML sem
tabela geram erro de fonte/contrato. Nenhum estado é convertido em vazio.

## Fixtures

As fixtures sanitizadas estão em:
tests/fixtures/tjse_boletim_search.html,
tests/fixtures/tjse_boletim_principal.html e
tests/fixtures/tjse_boletim_detail.html e
tests/fixtures/tjse_boletim_empty.html — elas cobrem formulário, seção com
resultado e resposta sem seções.

## MCP

O provider está habilitado tecnicamente na federação para a superfície bounded
de CJSG. O total entre edições continua desconhecido e é reportado no trace;
isso não é uma afirmação de completude nacional. Não são enviados tokens
pessoais e não há bypass de Turnstile.

## Proximos passos

Validar uma política bounded para percorrer múltiplas edições, mantendo
total_known=false enquanto a fonte não informar total global. O formulário
judicial Turnstile permanece no provider diagnóstico separado.
