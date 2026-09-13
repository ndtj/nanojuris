# Pesquisa — intake Juscraper

Status: in_progress

## Snapshot

- commit: 604c1dd70d6f313011cc1079790febe6c71807e2;
- data observada: 2026-08-10;
- versão: 0.3.0;
- licença: MIT;
- Python: 3.11+;
- runtime observado: 29 classes de tribunais e 4 agregadores; isso não equivale
  a 33 providers de jurisprudência.

O snapshot foi reproduzido no repositório correto
`https://github.com/jtrecenti/juscraper`, commit
`604c1dd70d6f313011cc1079790febe6c71807e2`, e permanece fixado para esta
rodada. A licença MIT foi conferida no arquivo `LICENSE` (SHA-256
`268966cc8228411db2775fbacf3d91b1a15bcdd99a713892e905b3a541b83c59`). O
inventário reproduzível está em
`docs/provider-discovery/juscraper-intake-20260901.*`.
O inventário tribunal-a-tribunal, que separa equivalência runtime, sobreposição
parcial, lacunas live e superfícies processuais fora de escopo, está em
`docs/provider-discovery/juscraper-court-inventory-20260901.*`.

## Achados

- 25 tribunais estaduais expõem cjsg;
- três expõem cjpg;
- o runtime e a documentação pública divergem;
- DataJud, PDPJ e Comunica CNJ estão fora do limite NanoJuris;
- pandas e recursos de autenticação/browser não são adequados ao núcleo;
- TJAP e TJMG exigem tratamento de risco específico.
- 25 superfícies CJSG, 3 CJPG e 1 detalhe TJTO são relevantes ao domínio;
- o manager e a documentação não refletem toda a árvore runtime;
- TJRJ declara que um CAPTCHA presente não seria validado pelo backend; isso é
  evidência de risco, não autorização de implementação;
- os quatro TRFs do snapshot implementam consulta processual, fora deste intake.
- o transporte upstream retenta `403` em famílias compartilhadas; a NanoJuris
  não herda esse default, pois `403` pode indicar controle de acesso;
- há parser que captura falha de download de detalhe e continua; toda adaptação
  deve converter isso em `partial`/outcome explícito, nunca omitir o erro;
- TJMT descobre um token publicado no `config.json`; sua natureza pública,
  finalidade e rotação precisam de revisão própria, sem persistir o valor;
- TRF6 usa reconhecimento de CAPTCHA em consulta processual, reforçando sua
  exclusão do intake NanoJuris.

### Matriz de cobertura por tribunal

A matriz reproduzível lista os 25 pacotes TJ e os quatro pacotes TRF do
snapshot. Ela identifica 19 tribunais já associados a providers runtime, dois
com sobreposição parcial (TJRJ e TJSC), duas lacunas sem equivalente (TJAP e
TJMG) e duas lacunas com dados públicos observados na rodada (TJES e TJRN).
Os quatro TRFs são classificados como superfícies processuais `cpopg`/`cposg`,
portanto não são candidatos de jurisprudência textual nesta lib. A associação
nominal não é considerada prova de equivalência: cada promoção ainda requer o
contrato e os gates definidos neste SDD.

### Estado da rodada atual

- 25 pacotes TJ brasileiros foram confirmados como candidatos estáticos;
- 3 superfícies `cjpg` (TJES, TJSP e TJTO) e o detalhe `tjto.cjsg_ementa`
  foram confirmados no código e nos schemas;
- nenhum arquivo upstream foi copiado e nenhum source ID foi promovido;
- `cpopg`/`cposg` e os agregadores permanecem fora da jurisprudência textual;
- o inventário é estático: disponibilidade live continua exigindo chamada
  limitada e contrato próprio por tribunal.

Em 2026-09-01 foram feitas chamadas públicas bounded diretamente às superfícies
oficiais referenciadas pelo upstream. TJES respondeu HTTP 200 com um registro
identificável e ementa/acórdão; TJRN respondeu HTTP 200 com dez registros,
identificadores, ementas e inteiro teor. Os metadados e hashes, sem conteúdo
jurídico persistido, estão em
`docs/provider-discovery/juscraper-live-smoke-20260901.*`. As duas superfícies
continuam `candidate_live_valid_data`: disponibilidade não substitui fixtures,
equivalência canônica, revisão de reuso ou promoção runtime.

## Limitação

Análise estática e fixtures não provam disponibilidade live atual.
