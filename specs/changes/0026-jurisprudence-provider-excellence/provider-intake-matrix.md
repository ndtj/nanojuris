# Matriz inicial de intake Juscraper

Esta matriz é triagem arquitetural, não prova de funcionamento live.

## Sobreposição com adapters NanoJuris

| Família/fonte | Situação NanoJuris | Uso do Juscraper |
| --- | --- | --- |
| TJAC, TJAL, TJAM, TJCE, TJMS | runtime eSAJ/cjsg | comparar payload, paginação e retries |
| TJSP | runtime cjsg e eproc | comparar cobertura e documentos, sem substituir facade |
| TJDFT | runtime gold | comparar contrato JSON e aliases |
| TJBA | runtime gold GraphQL | comparar paginação e campos canônicos |
| TJPA | runtime gold BFF | comparar contrato e regressões |
| TJPB | runtime gold | usar apenas evidência compatível com a rota atual |
| TJPI, TJPR, TJRR, TJRS | runtime gold | comparar parsers, totais e paginação |
| TJGO, TJMT, TJSC, TJTO | runtime silver | procurar ganhos de campos e falhas |
| TJPE | runtime blocked | usar diagnóstico, não mascarar bloqueio |
| TJRJ | eproc runtime; ejuris candidate | deferir ejuris até confirmação oficial de acesso e revisão Security/Legal |
| TJRO | contexto de precedentes runtime | avaliar jurisprudência textual separadamente |
| TJMG | candidate mapped | manter bloqueado enquanto exigir OCR de CAPTCHA; aproveitar somente parser offline legítimo |
| TJES | candidate mapped; pacote 0025 | cruzar API JSON atual com parser do Juscraper |
| TJRN | candidate mapped | investigar promoção por contrato público |
| TJAP | candidate mapped e bloqueado externamente | manter diagnóstico explícito de Turnstile |

## Lacunas ou superfícies complementares

| Fonte | Ação |
| --- | --- |
| TJRJ ejuris | deferido; só retoma com confirmação oficial de acesso sem ignorar CAPTCHA |
| TJRN jurisprudência | prioridade alta para cobertura estadual |
| TJMG jurisprudência | bloqueado; OCR só pode tratar documento público já obtido, nunca CAPTCHA |
| TJES jurisprudência | continuar pacote 0025, evitando rota legada |
| TJRO jurisprudência textual | separar de precedentes Liame |
| TJAP | documentar bloqueio; não contornar |
| TRFs do snapshot | métodos observados são consulta processual; permanecem no domínio NanoJud |

## Fora do escopo deste programa

| Juscraper | Motivo |
| --- | --- |
| DataJud | metadados processuais; NanoJud |
| PDPJ processo | processos, partes e movimentos; NanoJud |
| Comunica CNJ | comunicações processuais; NanoJud |
| JusBR autenticado | autenticação e cookies; não é fonte oficial primária |

## Gate de intake

Um item só avança quando houver:

1. fonte oficial pública;
2. licença e atribuição resolvidas;
3. rota e payload reproduzíveis;
4. fixture minimizada;
5. equivalência de campos documentada;
6. estados de falha testados;
7. benefício sobre o provider atual;
8. ausência de bypass ou acesso indevido.
