# Análise de respostas HTTP 200 com zero resultados

Auditoria pública limitada, sem credenciais, sem persistir corpos HTML/JSON e
sem contornar CAPTCHA, WAF, login ou limites. O objetivo foi descobrir se o
zero vinha da fonte, do contrato de consulta ou de um bloqueio mascarado.

## Resultado executivo

- **Dois providers runtime entregaram zero explícito da própria fonte:**
  `tjpe_jurisprudencia` (JSF) e `tjac_cjsg` (e-SAJ).
- **Um endpoint candidato revelou um problema de payload:** `tjro_jurisprudencia`.
  Com `fields.tipo=["EMENTA"]` retorna HTTP 200/total 0; omitindo `tipo` ou
  usando lista vazia retorna HTTP 200/total 676011 e registros reais.
- TJCE, TJSP e TRF1 foram excluídos do grupo “zero”: embora haja HTTP 200 em
  algumas aberturas, as páginas contêm CAPTCHA/controle de acesso. A regra é
  reportar bloqueio, nunca lista vazia.

## Casos confirmados

| Fonte/superfície | Evidência live | Diagnóstico | Estado |
|---|---|---|---|
| TJPE JSF | GET/POST 200; `Nenhum documento encontrado`; total 0 em `dano moral` e `habeas corpus` | A fonte devolveu zero explícito. O fluxo e o payload foram reproduzidos com a mesma sequência do Juscraper; o REST separado está bloqueado por TLS | Runtime correto; zero válido |
| TJAC/CJSG | POST 200 e GET 200/352 bytes; `Acórdãos(0)` + `Não foi encontrado nenhum resultado`; total 0 | O zero também aparece com corpo completo do formulário DOM, corpo equivalente do Juscraper e busca vazia. Não há evidência de descarte pelo parser | Runtime correto; zero válido |
| TJRO/CJSG candidato | JSON 200/total 0 com `tipo=["EMENTA"]`; sem `tipo` total 676011 e 1 registro | O filtro `tipo` não é compatível com o backend atual para os valores testados. O default upstream está desatualizado ou semanticamente diferente | Candidato; não promover ainda |

### TJPE

O fallback JSF/RichFaces executa GET de `consulta.xhtml`, mantém ViewState e
cookies, faz o POST da pesquisa e reconhece o marcador explícito. O fluxo
equivalente do [Juscraper TJPE](https://github.com/jtrecenti/juscraper/blob/main/src/juscraper/courts/tjpe/download.py)
produziu a mesma resposta de zero. O parser do [Juscraper TJPE](https://github.com/jtrecenti/juscraper/blob/main/src/juscraper/courts/tjpe/parse.py)
também trata a tela como ausência de documentos, não como erro de transporte.

Conclusão: não corrigir o zero trocando silenciosamente o transporte REST ou
desligando TLS. A próxima prova deve usar um número de processo/registro
conhecido; sem isso, o comportamento atual é coerente com a fonte.

### TJAC/CJSG

A sequência e-SAJ `POST /resultadoCompleta.do` → `GET /trocaDePagina.do` foi
repetida com o payload NanoJuris, com o formulário DOM completo e com a forma
usada pelo [fluxo e-SAJ compartilhado do Juscraper](https://github.com/jtrecenti/juscraper/blob/main/src/juscraper/courts/_esaj/download.py).
Todas deram o mesmo fragmento oficial de zero, inclusive uma pesquisa vazia.

Há uma melhoria de observabilidade pendente: `parse_cjsg_results` reconhece o
marcador, mas ainda não preenche explicitamente `is_complete` e
`completeness_reason`. Isso não causa o zero, mas dificulta distinguir “zero
confirmado” de “página sem linhas”. Deve virar uma pequena mudança SDD com
fixture de `Acórdãos(0)`.

### TJRO/CJSG candidato

O [provider TJRO do Juscraper](https://github.com/jtrecenti/juscraper/blob/main/src/juscraper/courts/tjro/download.py)
envia por padrão `fields.tipo=["EMENTA"]`. No backend público atual, esse
filtro e também os valores não vazios testados (`SENTENÇA`, `ACÓRDÃO`,
`DECISÃO`, `VOTO`) retornam zero. O mesmo endpoint sem o filtro, ou com lista
vazia, devolve total 676011; o único registro inspecionado apenas em metadados
indicou `tipo=SENTENÇA` e `grau_jurisdicao=1`.

Isso caracteriza divergência de contrato, não falha do parser. O endpoint
continua **candidate-only**: o runtime ainda não tem adapter geral
`tjro_jurisprudencia`; `tjro_liame` é uma coleção diferente. Antes de
implementar, é necessário fixture diferencial, contrato de filtros e prova de
paginação/completude.

## O que não é zero

TJCE, TJSP e CJF/TRF1 apresentam HTTP 200 em páginas de entrada, mas os sinais
de CAPTCHA/controle impedem uma consulta pública reproduzível. Esses casos
devem continuar como `blocked_access`. REST TJPE, STF e outras falhas TLS/reset
devem continuar como `blocked_transport`.

## Próximos passos técnicos, em ordem

1. Adicionar fixture e telemetria explícita de zero para o parser e-SAJ.
2. Obter um identificador conhecido do TJPE e do TJAC para validar a hipótese
   “índice sem correspondência” sem aumentar a frequência de chamadas.
3. Fechar o contrato TJRO com fixture sem `tipo` versus filtro restritivo e só
   então criar o adapter geral, incluindo paginação, `raw`, `SourceTrace` e
   completude.
4. Manter todos os bloqueios como erros classificados, nunca como zero.

Produção não foi alterada.
