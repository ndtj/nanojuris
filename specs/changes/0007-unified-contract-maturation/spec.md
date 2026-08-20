# Spec — maturação premium do contrato de busca unificada

ID: `0007-unified-contract-maturation`
Status: `in_progress`
Owner: `NanoJuris engineering`
Data: `2026-08-20`

## Problema

A busca federada aceita uma interface comum, mas os providers não aplicam os mesmos filtros nem entregam o mesmo perfil de registro. Sem uma matriz semântica, consumidores podem interpretar ausência de filtro como filtro aplicado, misturar precedentes com decisões e tratar janela parcial como corpus completo.

## Requisitos funcionais

- RF-001: gerar matriz estruturada de todos os providers runtime com perfil semântico, canônicos, filtros, paginação, completude, texto integral e evidência live.
- RF-002: distinguir filtro nativo, traduzido, pós-filtro local comprovado, não suportado e ainda não comprovado.
- RF-003: distinguir decisões, precedentes, jurisprudência curada, documentos de apoio e fontes fora do escopo como perfis de dados.
- RF-004: preservar por fonte total reportado, janela coletada, modo de paginação, estado de completude e limitações no resultado federado.
- RF-005: impedir promoção de rota/filtro apenas por observação de discovery; exigir contrato, fixture, parser e teste.
- RF-006: registrar lacunas priorizadas por provider e por dimensão de qualidade.
- RF-007: manter estados de acesso, indisponibilidade, query rejeitada, timeout e vazio semanticamente distintos.
- RF-008: permitir revisão e replay offline da matriz sem chamadas de rede.

## Critérios de aceitação

- AC-001: o relatório inclui 44 providers runtime e identifica os 41 participantes da busca unificada.
- AC-002: a matriz exibe a cobertura dos filtros comuns por provider e não os apresenta como equivalentes quando não declarados.
- AC-003: cada provider tem perfil semântico e canônicos declarados, ou uma lacuna explícita.
- AC-004: paginação e completude `unknown` são reportadas como lacuna e não como sucesso completo.
- AC-005: o resultado federado mantém `source_completeness`, `routing_warnings` e `errors` por fonte.
- AC-006: o snapshot live atual é ligado ao provider sem confundir indisponibilidade com vazio.
- AC-007: há testes offline da matriz, dos agregados e do contrato do relatório.
- AC-008: gates locais e o smoke live bounded são registrados em `verification.md`.

## Não objetivos

- Prometer que todos os tribunais possuem o mesmo acervo, filtros ou texto integral.
- Promover automaticamente campos HTML/JSON observados para filtros de produção.
- Remover provedores por falhas operacionais temporárias ou contornar controles de acesso.
