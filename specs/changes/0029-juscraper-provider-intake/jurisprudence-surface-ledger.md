# Ledger de superfícies jurisprudenciais do Juscraper

Snapshot: `604c1dd70d6f313011cc1079790febe6c71807e2`
Data do snapshot: 2026-08-10
HEAD remoto verificado em 2026-09-01: mesmo commit
Licença do software: MIT

Este ledger é uma triagem estática. Ele não afirma disponibilidade live e não
autoriza copiar código, fixture ou conteúdo.

## Resumo correto do escopo útil

- 25 superfícies `cjsg` de jurisprudência estadual;
- 3 superfícies `cjpg` de decisões/sentenças de primeiro grau;
- 1 superfície de detalhe de ementa do TJTO;
- uma superfície técnica pode expor mais de uma collection: a API TJES também
  revela primeiro grau e turma recursal, que exigem bindings separados;
- métodos `cpopg`, `cposg`, DataJud, PDPJ, Comunica CNJ e JusBR autenticado
  permanecem fora do escopo da NanoJuris.

## CJSG — segundo grau

| Tribunal | Relação com NanoJuris | Decisão de intake | Prioridade |
| --- | --- | --- | --- |
| TJAC | sobrepõe `tjac_cjsg` | teste diferencial de parser, filtros e paginação | hardening |
| TJAL | sobrepõe `tjal_cjsg` | teste diferencial | hardening |
| TJAM | sobrepõe `tjam_cjsg` | teste diferencial | hardening |
| TJAP | candidato `tjap_tucujuris` | manter bloqueado; Turnstile não pode ser contornado | blocked_access |
| TJBA | sobrepõe `tjba_graphql` | comparar contrato GraphQL e campos; não substituir sem ganho | hardening |
| TJCE | sobrepõe `tjce_cjsg` | comparar TLS, retries e parser eSAJ | hardening_p0 |
| TJDFT | sobrepõe `tjdf_juris` | equivalência de JSON, filtros e aliases | hardening |
| TJES | candidato `tjes_jurisprudencia` | adaptar API oficial `/consulta-jurisprudencia/api/search` após 0025/0039 | candidate_p0 |
| TJGO | sobrepõe `tjgo_projudi_jurisprudencia` | comparar a mesma família de rota e campos | hardening |
| TJMG | candidato `tjmg_jurisprudencia` | não adotar OCR de CAPTCHA; parser offline pode servir como evidência | blocked_access |
| TJMS | sobrepõe `tjms_cjsg` | teste diferencial | hardening |
| TJMT | sobrepõe `tjmt_jurisprudencia_api` | comparar payload e identidade | hardening |
| TJPA | sobrepõe `tjpa_jurisprudencia_bff` | comparar campos, total e paginação | hardening |
| TJPB | sobrepõe `tjpb_pje_jurisprudencia` | usar fixtures para fechar lacuna de evidência, sem trocar rota cegamente | hardening_p0 |
| TJPE | sobrepõe `tjpe_jurisprudencia` | avaliar se a implementação externa resolve contrato sem relaxar TLS | hardening_p0 |
| TJPI | sobrepõe `tjpi_juspi` | teste diferencial | hardening |
| TJPR | sobrepõe `tjpr_jurisprudencia` | comparar texto completo e paginação | hardening |
| TJRJ | candidato `tjrj_ejuris` e runtime eproc distinto | alto risco: upstream depende da alegação de CAPTCHA não validado; exigir parecer de acesso | candidate_high_risk |
| TJRN | candidato `tjrn_jurisprudencia` | adaptar API oficial após reprodução bounded | candidate_p0 |
| TJRO | hoje apenas `tjro_liame` contextual | criar candidato separado de jurisprudência textual | candidate_p0 |
| TJRR | sobrepõe `tjrr_juris` | comparar JSF, paginação e estado vazio | hardening |
| TJRS | sobrepõe `tjrs_solr` | comparar URL documental, identidade e robots | hardening |
| TJSC | sobrepõe `tjsc_eproc_jurisprudencia` | comparar a mesma família eproc e filtros | hardening |
| TJSP | sobrepõe `tjsp_cjsg` | importar apenas melhorias comprovadas por testes diferenciais | hardening |
| TJTO | sobrepõe `tjto_jurisprudencia` | corrigir ementa ausente e tipos documentais com composição rastreada | hardening_p0 |

## CJPG — primeiro grau

| Coleção candidata | Evidência no snapshot | Ação no plano |
| --- | --- | --- |
| `tjes_cjpg` | core oficial `pje1g`, mesmo contrato JSON do TJES | pacote próprio; não misturar com acórdãos de segundo grau |
| `tjsp_cjpg` | busca pública CJPG com decisões de primeiro grau | pacote próprio, identidade e redistribuição revisadas |
| `tjto_cjpg` | mesma busca com `tip_criterio_inst=1` | pacote próprio; separar sentenças, decisões e acórdãos |

## Collection adicional na superfície TJES

| Coleção candidata | Evidência no snapshot | Ação no plano |
| --- | --- | --- |
| `tjes_turma_recursal` | core oficial `turma_recursal_legado` | pacote próprio; não contar como segundo grau nem como primeiro grau comum |

TJMA e TJSE não possuem classe CJSG no snapshot observado. Seus providers
NanoJuris existentes continuam no programa normal de qualidade; a ausência no
Juscraper não é evidência de ausência institucional ou de falha.

## Enriquecimento

| Superfície | Ganho | Regra |
| --- | --- | --- |
| `tjto_ementa_detail` | endpoint de ementa por UUID pode preencher cards hoje vazios | modelar como detalhe lazy; trace de cada request; falha de detalhe não apaga resultado base |

## Itens expressamente rejeitados neste programa

| Item upstream | Motivo |
| --- | --- |
| `cpopg` e `cposg` | consulta processual, não coleção de jurisprudência |
| DataJud e PDPJ | metadados, partes e movimentos; domínio NanoJud |
| Comunica CNJ | comunicação processual; domínio NanoJud |
| JusBR autenticado | agregador não oficial primário e dependente de credencial/cookie |
| OCR de CAPTCHA TJMG | contorno de controle de acesso proibido |
| fluxo TJRJ baseado em CAPTCHA não validado | não promover sem confirmação oficial e revisão de conformidade |

## Gate por superfície

Cada linha candidata precisa de source contract próprio, fixture sanitizada,
diff de campos, identidade, paginação, estados de erro, provenance de código,
teste diferencial offline e decisão `adopt`, `hardening_only`, `defer`,
`blocked_access`, `rejected` ou `out_of_scope`.
