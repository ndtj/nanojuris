# Clarificação — convergência ouro

Mudança: `specs/changes/0070-provider-capability-gold-convergence/spec.md`
Responsável: arquitetura NanoJuris
Status: `resolved_for_planning`

## Decisões

| ID | Pergunta | Decisão recomendada | Estado |
| --- | --- | --- | --- |
| Q-001 | Ouro exige os mesmos filtros em todos os providers? | Não. Exige 100% dos filtros oficiais classificados e todos os suportados implementados. | resolved |
| Q-002 | Fonte sem inteiro teor pode ser ouro? | Pode obter `engineering_gold`, mas não `document_gold`; `not_offered_by_source` deve ser comprovado. | resolved |
| Q-003 | Um portal alternativo pode completar dados ausentes? | Sim, como superfície/provider separado e relacionado; nunca por mistura invisível. | resolved |
| Q-004 | Campos exclusivos devem virar campos canônicos? | Somente quando possuem semântica nacional; os demais ficam em `raw` tipado com provenance. | resolved |
| Q-005 | Filtro sem prova pode ser pós-filtrado localmente? | Apenas se o campo necessário estiver completo nos resultados e a limitação de janela estiver explícita. | resolved |
| Q-006 | Discovery pode usar navegador? | Sim, em fluxo público bounded, para observar requests legítimos; sem resolver desafios de acesso. | resolved |
| Q-007 | Busca deve baixar inteiro teor automaticamente? | Não. Search retorna referência; fetch documental continua explícito e limitado. | resolved |
| Q-008 | Context providers usam a mesma definição de ouro? | Mesmos gates de engenharia, mas conteúdo/documento são avaliados conforme o papel da fonte. | resolved |
| Q-009 | O plano autoriza release/deploy? | Não. Implementação local futura termina antes de qualquer release. | resolved |
| Q-010 | “Todos os dados” inclui consulta processual e timeline? | Não. São inventariados para roteamento, mas recebem `out_of_scope_nanojud`; NanoJuris preserva apenas dados jurisprudenciais necessários. | resolved |

## Hipóteses a validar na execução

| ID | Hipótese | Validação | Gate |
| --- | --- | --- | --- |
| H-001 | O conjunto de 60 fontes ainda é o denominador correto | regenerar catálogo e comparar runtime/candidates | W0 |
| H-002 | Há filtros oficiais ainda não promovidos nos providers | sweep estático + requests diferenciais | W2–W5 |
| H-003 | Parte dos 18 providers sem full text possui detalhe ou documento alternativo | pesquisa oficial por superfície | W6 |
| H-004 | Famílias técnicas permitem reduzir duplicação sem esconder diferenças | piloto por eSAJ, eproc, PJe, API e JSF | W2 |

## Decisão de saída

- [x] Termos “ouro”, “todos os filtros” e “inteiro teor” possuem semântica
  verificável.
- [x] Ausência real de capacidade foi separada de trabalho incompleto.
- [x] O programa pode seguir para implementação local em lotes.
