# Pesquisa e referências

Mudança: `specs/changes/0002-provider-discovery/spec.md`
Data da revisão: `2026-08-20`
Responsável: `NanoJuris engineering`

## Pergunta de pesquisa

Como aproveitar a biblioteca local disponibilizada em
`C:\Users\luciano.finozzi\Downloads\sistema` para acelerar a descoberta de
providers sem transformar exploração em runtime de provider ou perder
proveniência?

## Fontes primárias locais

| Fonte | Achado verificável | Aplicabilidade | Confiança |
| --- | --- | --- | --- |
| `src/nanojuris/route_probe.py` | O NanoJuris já possui probe HTTP bounded com hash, latência, sinais legais e sinais de acesso. | Deve continuar sendo a base HTTP. | alta |
| `specs/contracts/provider-contract.md` | O provider precisa documentar rotas, estados, campos, fixtures e traces. | Define a saída mínima da descoberta. | alta |
| `src/nanojuris/models.py` | Existem `SourceTrace`, `ExtractionTrace`, `AccessStatus` e `ExtractionStatus`. | A evidência de descoberta deve ser compatível. | alta |
| `segunda lib/segunda lib/engines/toolbelt/custom.py` | A resposta unificada preserva corpo, status, headers, redirects e respostas XHR. | Inspira o modelo de evidência. | alta |
| `segunda lib/segunda lib/engines/toolbelt/convertor.py` | Respostas de navegador podem carregar respostas XHR/fetch capturadas. | Inspira o modo dinâmico. | alta |
| `segunda lib/segunda lib/spiders/*` | Há crawler, scheduler, robots, throttle, cache e checkpoint. | Inspira descoberta bounded e replay. | alta |
| `segunda lib/segunda lib/parser.py` | Há relocação adaptativa de seletores. | Deve ser usada somente como sugestão revisável. | alta |
| `segunda lib/segunda lib/core/ai.py` | Há uma superfície MCP de fetch e navegador. | Pode ser uma interface futura do worker, não a autoridade do domínio. | alta |

## Síntese

O maior ganho é combinar o probe HTTP existente com um worker opcional de
navegador que capture rotas dinâmicas e uma camada de evidência normalizada.
Crawler, cache, checkpoint e candidatos de seletores aumentam produtividade,
mas precisam ser subordinados a limites explícitos, fixtures e revisão humana.

A implementação inicial será nativa do NanoJuris e não exigirá a biblioteca
externa em produção. Playwright será uma dependência opcional de descoberta.

## Decisões influenciadas

- Decisão: manter a descoberta em `nanojuris.discovery`, separada dos providers.
  - Evidência: o contrato de provider exige estabilidade e maturidade que uma
    exploração ainda não possui.
  - Impacto: nenhum resultado de descoberta escreve o catálogo gerado ou cria
    provider automaticamente.
- Decisão: gerar artefatos SDD e relatório JSON reproduzível.
  - Evidência: a constituição exige contrato antes do código e evidência antes
    de afirmação.
  - Impacto: cada execução terá request, response, hash, classificação e
    candidatos rastreáveis.
- Decisão: usar seletores adaptativos apenas como candidatos.
  - Evidência: relocação estrutural não prova semântica legal.
  - Impacto: aprovação e testes offline continuam obrigatórios.

## Limitações

- A captura de navegador depende de Playwright instalado localmente.
- A biblioteca externa foi recebida como snapshot sem metadados completos de
  empacotamento; o NanoJuris não dependerá dela para funcionar.
- A descoberta não confirma maturidade de provider; ela produz material para a
  especificação e para a implementação posterior.
