# Pesquisa — programa de excelência de providers

Status: in_progress
Data: 2026-09-01

## Perguntas

1. Qual é a linha de base real da NanoJuris?
2. Quais capacidades do Juscraper são relevantes para jurisprudência?
3. Qual modelo de adoção evita acoplamento e regressão?
4. Como comprovar qualidade sem depender de chamadas live contínuas?

## Evidência local

| Fonte | Achado |
| --- | --- |
| docs/coverage/README.md | 56 fontes documentadas, 46 runtime, 42 na busca unificada, 34 primárias textuais |
| docs/registry/provider-catalog.full.json | catálogo detalha status, maturidade, campos, limitações e interfaces |
| specs/contracts/provider-contract.md | estados operacionais já não podem ser colapsados em zero_results |
| specs/product/extraction-blueprint.md | pipeline canônico e traces já são normativos |
| specs/changes/0006 e 0007 | discovery total e maturação do contrato permanecem parcialmente abertos |
| specs/changes/0011 e 0015 | identidade, quarentena e evidência offline já foram endurecidas |

## Evidência do Juscraper

Snapshot analisado: commit 604c1dd70d6f313011cc1079790febe6c71807e2,
datado de 2026-08-10.

- licença MIT permite uso e modificação com preservação do aviso;
- versão observada 0.3.0 e Python 3.11+;
- registro runtime observado: 29 tribunais e 4 agregadores;
- 25 tribunais estaduais expõem busca de jurisprudência cjsg;
- TJSP, TJES e TJTO possuem superfície de sentenças cjpg;
- TJTO possui detalhe de ementa por UUID, útil para corrigir resultados sem
  ementa na listagem;
- DataJud, PDPJ e Comunica CNJ não são substitutos de jurisprudência textual;
- TJAP documenta bloqueio por Turnstile;
- TJMG usa OCR de CAPTCHA no snapshot e não pode ser adaptado nesse fluxo;
- TRF3 pode sofrer bloqueio de camada de proteção;
- a documentação pública não é totalmente equivalente ao registro runtime.
- o `tribunal_manager.py` observado está divergente da árvore real e não pode
  ser usado como inventário canônico;
- a rota TJRJ descreve um fluxo em que o backend não validaria CAPTCHA; essa
  alegação é risco de conformidade e impede promoção automática;
- as superfícies TRF do snapshot são majoritariamente consulta processual e não
  ampliam jurisprudência textual da NanoJuris.

## Decisões influenciadas

- adotar código ou lógica apenas após diff semântico, licença e teste de
  equivalência;
- não adicionar pandas ao núcleo da NanoJuris por causa do formato externo;
- tratar cada rota como contrato independente, mesmo dentro de família comum;
- manter fontes processuais fora deste programa;
- usar fixtures minimizadas como base primária de regressão;
- usar live apenas como evidência temporal bounded.

## Lacunas a fechar

- revisar termos de uso e política de reutilização de cada fonte promovida;
- produzir matriz campo a campo NanoJuris versus Juscraper;
- confirmar rotas candidatas por evidência oficial atual antes de implementação;
- medir latência, tamanho e estabilidade apenas durante o pacote 0033;
- decidir versão semântica após o impacto real do contrato 0027.
- gerar denominador nacional além do catálogo atual;
- formalizar primeiro grau como coleção distinta;
- definir identidade de decisão e política de deduplicação entre superfícies;
- definir semântica da busca federada e coleta reprodutível.
