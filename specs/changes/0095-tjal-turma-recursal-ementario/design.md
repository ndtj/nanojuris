# Design — TJAL Turmas Recursais

## Fonte

Indice oficial: `https://aceco.tjal.jus.br/?pag=juizados_jurisprudencias`.
Volumes observados:

- `juizados/relatorios/Ementas-1.pdf` (44 paginas, texto);
- `juizados/relatorios/Ementas-2.pdf` (55 paginas, texto);
- `juizados/relatorios/Ementas-3.pdf` (620 paginas, texto parcial);
- `juizados/relatorios/Ementas-4.pdf` (109 paginas, image-only na verificacao).

O adapter consulta por padrao um volume textual bounded e conserva a lista de
volumes no contrato. Nao ha total autoritativo nem cursor remoto.

## Pipeline

1. validar URL HTTPS e host allowlist;
2. obter o indice oficial para descobrir os links;
3. selecionar o volume configurado, sem seguir hosts externos;
4. validar status, MIME, magic bytes e limite de 8 MiB;
5. extrair texto com `pypdf` dentro do limite de paginas;
6. segmentar blocos por marcadores de processo/ementa;
7. normalizar somente espacos, mantendo `raw` e numero da pagina;
8. aplicar filtros locais de texto, frase, numero e exclusao;
9. retornar `SearchPage` com total desconhecido e escopo recursal.

## Identidade

`degree=recursal` e deliberadamente diferente de `first` e `second`. Turma
Recursal e orgao revisor dos Juizados Especiais, mas nao deve ser contado como
segunda instancia estadual na matriz CJSG.

## Segurança e custo

Uma chamada ao indice e no maximo uma ao volume por consulta, com intervalo de
rate limit compartilhado, timeout e limite de bytes. O corpo nao e persistido
como corpus; fixtures sao sanitizadas. PDF image-only e reportado como
indisponivel para extracao.
