# Pesquisa e referências

Mudança: `specs/changes/0003-premium-team-operating-model/spec.md`
Data da revisão: `2026-08-20`
Responsável: `NanoJuris engineering`

## Pergunta de pesquisa

Como organizar uma equipe humana e agentes especializados para transformar a
NanoJuris em uma plataforma premium de jurisprudência pública, usando a
descoberta HTTP/browser/XHR, crawler, replay e drafts SDD já implementados?

## Fontes primárias locais

| Fonte | Achado | Aplicabilidade | Confiança |
| --- | --- | --- | --- |
| `AGENTS.md` | Define fronteira do produto, ordem de auditoria de providers e regras de qualidade. | Base de domínio e aceite de providers. | alta |
| `specs/constitution.md` | Exige contrato antes do código, evidência, agentes limitados e aceite humano. | Base de autoridade e gates. | alta |
| `specs/operating-model.md` | Já define papéis humanos, agentes, pareceres e autoridade. | Base para especialização premium. | alta |
| `specs/quality-gates.md` | Define gates de especificação, arquitetura, verificação e operação. | Base para release. | alta |
| `specs/changes/0002-provider-discovery` | Define descoberta bounded, evidência, browser opcional, crawler e replay. | Base técnica da célula de discovery. | alta |
| `src/nanojuris/models.py` | Preserva canonicalidade, source trace e extraction trace. | Base de dados e jurimetria. | alta |
| `src/nanojuris/discovery/*` | Implementa coleta e geração de drafts, sem promoção automática. | Base operacional da equipe. | alta |

## Síntese

O modelo premium precisa separar domínio, arquitetura, descoberta, engenharia
de provider, qualidade de dados, segurança, SRE e release. Agentes aceleram
inspeção, documentação, implementação e verificação; decisões de produto,
domínio, maturidade e produção continuam com responsáveis humanos.

## Decisões influenciadas

- criar uma equipe virtual com papéis estáveis e não uma sequência de prompts;
- exigir pareceres independentes para mudanças de alto impacto;
- usar a descoberta como célula de pesquisa que entrega evidências e drafts;
- separar implementação de revisão e aprovação;
- medir qualidade por contrato, cobertura, provenance, confiabilidade e
  operabilidade, não somente por quantidade de providers.

## Limitações

- A alocação define papéis e responsabilidades; não cria pessoas, contratos de
  trabalho ou autorização de produção.
- A capacidade real depende das ferramentas instaladas, do acesso ao ambiente
  e da revisão do Product/Domain Owner.
