# Playbook de descoberta bounded

Para cada superfície, executar nesta ordem:

1. página oficial de entrada, ajuda e política de uso;
2. formulário, selects, valores, dependências e campos ocultos;
3. request disparado por consulta pequena e genérica;
4. resposta, paginação, total, ordenação e identificador;
5. segunda página e consulta vazia autorizada;
6. detalhe e links documentais;
7. API, export, catálogo ou portal oficial alternativo;
8. comparação com Juscraper sem copiar código;
9. fixture sanitizada e teste diferencial;
10. classificação de sucesso, vazio, bloqueio, timeout ou schema drift.

## Prova de filtro

Executar `Q0` controle, `Q1` com valor válido e `Q2` com valor alternativo
quando necessário. Comparar request normalizado, IDs, total, facets e campos.
Um input encontrado no HTML/JS é hipótese, não capacidade comprovada.

## Prova de documento

Seguir somente URL oficial, revalidar host após redirect, limitar bytes, validar
MIME e magic bytes, calcular hash, extrair texto e preservar a relação com a decisão.

## Prova de bloqueio

Registrar método, data, URL, status, marcadores, evidência redigida e alternativas
avaliadas. Repetição não é permitida quando a mesma proteção permanece estável.

