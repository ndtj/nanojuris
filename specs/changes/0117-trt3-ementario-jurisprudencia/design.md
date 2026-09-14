# Design - TRT3 ementario

O provider consulta a pesquisa avancada DSpace da colecao oficial, abre no
maximo tres itens de volume por chamada, valida os PDFs, extrai texto bounded
com `pypdf` e separa registros por identificadores CNJ do TRT3. O resultado e
uma janela local de ementas dos volumes observados, nao uma afirmacao de
completude do acervo do tribunal. URLs apontam para o bitstream oficial do
volume; nao sao geradas rotas de detalhe.

A colecao e marcada como `curated_jurisprudence`, `degree=second` e
`collection=TRT3_EMENTARIO`. O cliente expoe o provider para uso explicito,
mas a federacao nao o roteia automaticamente.
