# Design

O adapter baixa uma única vez o PDF oficial por consulta, limita bytes/páginas,
extrai páginas em memória, associa números CNJ por página às anotações `.doc`/
`.docx` e executa pós-filtro local. A lista não é persistida como índice.

`get_document` só aceita URLs `https://www4.tjrj.jus.br/AtosOficiais/` observadas
no PDF e delega a validação de MIME, magic bytes, tamanho, hash e extração ao
pipeline compartilhado. O estado de completude é sempre `total_unknown` e a
federação padrão permanece desligada.
