# Roadmap revisado por gates

## Onda 0A — verdade de cobertura

Pacote: 0036.

Saída: topologia nacional por ramo, autoridade e coleção; baseline atual
reclassificado sem confundir provider, tribunal, coleção e disponibilidade.

## Onda 0B — identidade, contrato e qualidade

Pacotes: 0037, 0027, 0028 e 0031.

Saída: identidade jurídica conservadora, contrato v2 compatível, runtime
compartilhado medido e scorecard executável. Nenhum provider novo é necessário.

## Onda 0C — federação honesta

Pacote: 0038.

Saída: query plan por fonte, filtros com semântica declarada, ranking não
enganoso, paginação global determinística e completude por fonte.

## Onda 1 — intake Juscraper sem código runtime

Pacote: 0029.

Saída: inventário de 25 CJSG, 3 CJPG e 1 detalhe, ledger de licença, diff
semântico e decisão por superfície. Rotas processuais permanecem fora de escopo.

## Onda 2 — ganhos externos de baixo risco

Pacote: 0039.

Ordem inicial:

1. TJES segundo grau, reconciliado com 0025;
2. TJRN segundo grau;
3. TJRO jurisprudência textual;
4. enriquecimento lazy de ementa do TJTO;
5. hardening diferencial de TJPB, TJCE, TJPE e demais overlaps.

TJRJ ejuris depende de revisão de acesso. TJMG e TJAP não avançam enquanto
dependerem de CAPTCHA/Turnstile. Nenhum adapter entra default nesta onda.

## Onda 3 — collections de primeiro grau

Alvos: `tjes_cjpg`, `tjsp_cjpg` e `tjto_cjpg`.

Cada collection recebe source ID, identidade, categoria documental, período,
parser, fixtures e source contract próprios. Consulta processual não entra.

## Onda 4 — cobertura por ramo e lacuna

O pacote 0030 fecha o ramo estadual, alimentado por 0036. Para Federal,
Trabalho, Eleitoral, Militar e superiores, 0036 deve abrir pacotes próprios por
ramo antes de implementação; eles não são escondidos dentro do pacote estadual.

Executar lotes independentes:

- estaduais restantes e maturação bronze/silver via 0030;
- TRFs/TNU/CJF;
- TST e TRT1–TRT24;
- TSE e TREs;
- STM e Justiça Militar estadual;
- superiores, súmulas, temas, repetitivos e informativos;
- controle externo como dimensão administrativa separada.

## Onda 5 — documentos e coleta reprodutível

Pacotes: 0032 e 0040.

Saída: referências documentais lazy, download seguro, manifests, checkpoints,
versionamento, freshness e retomada local. Nenhuma coleta em massa é default.

## Onda 6 — observabilidade e release

Pacotes: 0033 e 0034.

Comparar baseline e candidato em shadow mode, usar canários bounded e publicar
somente após autorização humana. Rollback é independente por provider.

## Priorização multicritério

Nenhuma soma simples decide promoção. A fila usa primeiro gates eliminatórios:

1. fonte oficial e coleção dentro do escopo;
2. acesso permitido sem bypass;
3. contrato reproduzível e fixture sanitizável;
4. identidade e texto decisório suficientes;
5. custo e risco operacional aceitáveis.

Depois dos gates, a pontuação orientativa considera cobertura jurisdicional,
lacuna de ramo, ganho textual, estabilidade, qualidade de campos, manutenção,
risco jurídico, risco de acesso e valor para pesquisa. Domain Owner e Security
podem vetar; pontuação nunca promove automaticamente.
