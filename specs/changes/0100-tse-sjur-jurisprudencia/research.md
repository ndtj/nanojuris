# Research — TSE SJUR

Fontes oficiais consultadas: `https://www.tse.jus.br/jurisprudencia/decisoes/`,
`https://jurisprudencia.tse.jus.br` e o backend público indicado pelo bundle
oficial do portal. O Juscraper foi usado somente como referência de descoberta;
nenhum código foi copiado.

O endpoint `/public/pesquisa/simples` aceita DSL serializada e devolve JSON com
`content`, `totalRegistros` e `mensagem`. A rota `/public/pesquisa` foi mantida
fora do escopo porque exige validação antirrobô. Não houve tentativa de
contornar CAPTCHA, WAF, login ou rate limit.
