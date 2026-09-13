# Plano de implementação por ondas

## Onda 0 — reconciliação (local)

1. Regenerar catálogo, quality, capability ledger, document inventory, degree,
   surface registry, state program e promotion manifest com `PYTHONPATH=src`.
2. Verificar que contagens derivam dos artefatos gerados.
3. Separar tarefas locais, externas e humanas; não simular as duas últimas.

Saída: baseline imutável e fila ordenada.

## Onda 1 — contrato transversal

1. Fechar semântica de `SearchPage` e estados de acesso.
2. Expor `total_known`, `total_unknown` e `authoritative_empty` separadamente.
3. Fechar campos de autoridade, grau, instância, coleção, classe, órgão,
   tipo documental e datas.
4. Aplicar `SourceTrace` e matriz de filtros em todos os providers elegíveis.

## Onda 2 — primeiro grau estadual

Priorizar fontes oficiais de sentenças/ementários selecionados. Cada rota deve
ser classificada como geral, curada ou contextual; coleções selecionadas não
devem ser promovidas como acervo completo. A ordem sugerida é TJRJ/TJSP/TJMG,
depois TJES/TJRN/TJTO e, em seguida, as demais lacunas CJPG.

## Onda 3 — segundo grau estadual

Revalidar cinco completos, fechar APIs B1, portais B2, eproc B3 e somente então
reavaliar bloqueados. TJRO/Liame não conta como jurisprudência geral sem prova
textual e de segundo grau.

## Onda 4 — trabalhista, eleitoral, federal e superior

Separar autoridade e grau em TRT/TST, TSE/TRE, TRF/STJ/STF/STM. Informativos,
precedentes qualificados e SJUR são coleções próprias; não contam como CJSG.

## Onda 5 — documentos e filtros

Para cada provider aprovado, provar filtros um por vez, duas páginas quando
existirem, detalhe e documento. Criar fixtures sanitizadas e validar MIME,
hash, tamanho, texto e OCR permitido.

## Onda 6 — federação e busca web

Executar smoke opt-in, medir completude/latência, habilitar apenas providers
com os oito gates e preservar diagnóstico por fonte. O planner adaptativo do
SDD 0077 pode selecionar 8–12 fontes, mas “todos os tribunais” permanece modo
explícito.

## Onda 7 — operação contínua

Smoke de baixa frequência, TTL, schema drift, alerta de queda de completude,
shadow mode e rollback por versão do parser. Sem deploy nesta execução.

## Ordem de parada

Se uma fonte exigir desafio humano, login, acesso controlado ou rota privada,
registrar evidência única, classificar bloqueio e passar à próxima fonte. Só
retomar após mudança externa legítima, não por repetição automática.
