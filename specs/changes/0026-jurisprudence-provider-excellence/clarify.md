# Clarificação — programa de excelência de providers

Status: in_progress

## Perguntas críticas

| ID | Pergunta | Decisão provisória | Aprovador | Estado |
| --- | --- | --- | --- | --- |
| Q-001 | O objetivo é quantidade ou cobertura comprovada? | cobertura comprovada prevalece | Domain Owner | resolved |
| Q-002 | Juscraper será dependência runtime? | não; intake por adaptação seletiva | Architecture | resolved |
| Q-003 | Consulta processual entra na NanoJuris? | não; pertence à NanoJud | Domain Owner | resolved |
| Q-004 | Todo provider precisa de inteiro teor? | não; capacidade deve ser explícita | Data/Domain | resolved |
| Q-005 | Gold exige teste live permanente? | não; tier de engenharia e saúde live são dimensões separadas | QA/SRE | resolved |
| Q-006 | Qual versão pública carregará as mudanças? | decidir após análise de compatibilidade de 0027 | Release Owner | pending |
| Q-007 | Código MIT copiado será atribuído como? | NOTICE/changelog e cabeçalho quando substancial | Legal/Owner | pending |
| Q-008 | Qual orçamento de rede por host? | definido por fonte no pacote 0028/0033 | SRE | pending |
| Q-009 | 56 fontes representam o universo nacional? | não; são somente o baseline conhecido | Domain/Architecture | resolved |
| Q-010 | primeiro grau entra em jurisprudência? | sim quando a autoridade publica coleção decisória pesquisável; separado de consulta processual | Domain | resolved |
| Q-011 | OCR pode resolver CAPTCHA? | não; OCR somente em documento público já obtido legitimamente | Security | resolved |
| Q-012 | TJRJ upstream pode ser adotado porque o CAPTCHA não é validado? | não sem confirmação oficial e revisão de conformidade | Security/Legal | resolved |
| Q-013 | o projeto será um espelho integral nacional? | não; busca federada e coleções locais reprodutíveis, com limites explícitos | Product | resolved |
| Q-014 | o que invalida um aceite anterior? | mudança de fingerprint em contrato, parser, fixture, capability ou evidência | QA | resolved |

## Hipóteses temporárias

| ID | Hipótese | Validação | Gate |
| --- | --- | --- | --- |
| H-001 | o contrato público atual pode evoluir sem breaking change | testes de compatibilidade | 0027 |
| H-002 | famílias eSAJ/eproc compartilham transporte, não necessariamente schema | fixtures por tribunal | 0028/0030 |
| H-003 | cinco candidatos prioritários trazem ganho real | pesquisa e chamadas bounded | 0029/0030 |
| H-004 | scorecard atual pode ser tornado executável | protótipo offline | 0031 |

## Condição para implementação

Pacotes de topologia, inventário, testes offline e decisões reversíveis podem
avançar. Mudança de API pública, política de rede, cópia substancial de código,
chamada live ou release não avança enquanto sua pergunta de alto impacto
específica estiver pendente.
