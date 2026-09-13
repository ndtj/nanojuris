# Roadmap de cobertura CJPG/CJSG — 2026-09-02

Este roadmap trata cada combinação `tribunal + grau + coleção` como uma
superfície independente. Ele orienta a expansão de primeiro e segundo grau
sem transformar a existência de um adapter em alegação de cobertura.

## Baseline verificável

Fonte de verdade: [`surface-state-registry-20260902.json`](surface-state-registry-20260902.json),
regenerado no ciclo técnico de 2026-09-05.

| Métrica | Estado atual | Regra de medição |
|---|---:|---|
| Superfícies mapeadas | 150 | matriz nacional, incluindo lacunas |
| Superfícies obrigatórias | 125 | superfícies exigidas pelo escopo nacional |
| CJPG live-validado | 2/27 | contrato + fixture + chamada live válida |
| CJSG live-validado | 5/27 | contrato + fixture + chamada live válida |
| Providers runtime | 52 | registro de runtime, independentemente de grau |
| Fontes no rollout federado técnico | 12 | manifesto de promoção local; fontes adicionais continuam opt-in |

`implemented`, `live_validated`, `federation_enabled` e `legal_approved` são
estados distintos. Uma coleção genérica `JURISPRUDENCIA`, PJE ou EPROC não
credita CJPG/CJSG sem binding de grau comprovado.

## Fases de execução

### Fase A — fechar o contrato e o diagnóstico

1. Manter o registro canônico por superfície e reconciliar catálogo, runtime,
   federação e evidência live.
2. Exigir `degree`, `instance`, `branch`, `authority`, `collection`,
   `document_type`, datas, `access_status`, `extraction_status` e
   `SourceTrace` em todo resultado aceito.
3. Diferenciar `total_zero`, `total_known`, `total_unknown`, bloqueio,
   timeout e schema inválido.
4. Rejeitar promoção quando a resposta for somente consulta processual,
   metadado, tema, DataJud, CAPTCHA/WAF ou conteúdo sem jurisprudência.

**Saída:** registry regenerado, pacote SDD individual e fixtures de sucesso,
vazio, erro, timeout e mudança de schema.

### Fase B — concluir as superfícies já implementadas

Ordem de execução:

1. **CJPG:** TJES e TJSP; validar segunda página, vazio autoritativo,
   parâmetro inválido, schema inválido, identidade de primeiro grau e
   deduplicação.
2. **CJSG:** revalidar TJAC, TJAL, TJAM, TJCE, TJES, TJMS e TJSP. Se uma
   fonte estiver bloqueada, registrar o bloqueio sem convertê-lo em vazio.
3. **TJRN:** fechar contrato do adapter já observado com HTTP 200 e paginação;
   só então sair de `candidate`.
4. **TJTO e TJGO:** confirmar se o grau é explícito por registro/endpoint;
   manter `JURISPRUDENCIA` genérica fora da contagem CJPG/CJSG quando não
   houver prova.

**Critério de saída:** cada superfície possui contrato reproduzível, três
fixtures mínimas (sucesso, vazio e falha/schema), chamada live recente e
qualidade aprovada. Para o escopo local/federado deste ciclo, a decisão do
operador registrada no manifesto substitui uma etapa interna adicional de
revisão; redistribuição e produção continuam fora do escopo.

### Fase C — expansão por família de tecnologia

Executar em lotes pequenos, com um pacote SDD por tribunal:

| Família | Tribunais prioritários | Riscos e técnica |
|---|---|---|
| eSAJ/CJSG | TJRO, TJBA, TJDFT, TJMT, TJPA, TJPB, TJPI, TJPR, TJRS, TJSC | sessão, parâmetros ocultos e paginação; usar transporte compartilhado e parser HTML independente |
| PJe/Projudi | TJGO, TJRN, TJTO, TJPE, TJSE, TJMG | endpoints variáveis; confirmar grau e classe no payload, sem copiar código de terceiros |
| APIs/BFF/GraphQL | TJBA, TJMT, TJPA e equivalentes oficiais | versionamento de schema, limites e filtros; fixtures de contrato alterado |
| Portais próprios | TJAC, TJAL, TJAM, TJES, TJMS e demais TJs | estabilidade, links de documento e identificação canônica |

Em cada lote, ordenar pelo maior ganho de lacunas CJPG/CJSG e menor risco de
acesso. O inventário Juscraper serve apenas para localizar nomes, rotas e
seletores; a implementação NanoJuris deve ser independente e licenciada.

### Fase D — promoção para a federação

Um binding entra no rollout federado técnico somente quando todos os sinais
forem verdadeiros:

```text
runtime
contract_valid
live_validated
fixtures_complete
quality_gate_passed
operator_approved
```

A resposta federada deve incluir, por fonte, páginas consultadas, total
conhecido/desconhecido, filtros remotos/locais/ignorados, completude,
latência, erro, bloqueio, hash e trace. Candidatos e fontes `opt_in` ficam
visíveis no diagnóstico, mas não são roteados por acidente.

### Fase E — cobertura nacional e manutenção

Metas mensuráveis:

* **A:** pelo menos 8 CJPG e 12 CJSG live-validados;
* **B:** metade dos 27 TJs em cada coleção;
* **C:** 27/27 somente com contrato, live check, qualidade e decisão do
  operador para o rollout técnico (sem inferir autorização de redistribuição);
* **D:** revalidação periódica e alerta de schema drift/completude.

Cada execução deve atualizar `last_live_check`, disponibilidade histórica,
latência, páginas sobrepostas, bytes, versão do parser/schema e qualidade por
campo. O histórico não pode apagar bloqueios anteriores nem reclassificar
falha externa como zero resultados.

## Pacote obrigatório por tribunal

```text
spec.md          contrato oficial e escopo CJPG/CJSG
design.md        transporte, parser, normalização e fallback
tasks.md         implementação, fixtures, live check e gates
verification.md  comandos, evidências, limitações e decisão de federação
```

O pacote deve incluir URL oficial, método/payload, paginação, ordenação,
filtros, limites, MIME/documento, retenção/licença, campos `raw`, erros
esperados e amostras sanitizadas. Nenhum segredo, CAPTCHA ou credencial é
armazenado.

## Próximo ciclo executável

1. Abrir workpacks SDD de TJTO, TJRO e TJGO.
2. Revalidar TJES/CJPG, TJSP/CJPG e os sete bindings CJSG.
3. Fechar a promoção técnica do TJRN, mantendo o gate legal separado.
4. Rodar a suíte transversal de filtros, grau, total e deduplicação.
5. Atualizar registry, ledger, catálogo e matriz de cobertura.
6. Promover à federação apenas as superfícies que cumprirem todos os gates.

Este plano é local e incremental. A decisão do operador permite o uso técnico
de fontes públicas no runtime federado local; não autoriza redistribuição,
publicação, deploy ou alteração de produção.
