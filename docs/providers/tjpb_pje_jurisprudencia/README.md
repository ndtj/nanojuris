# `tjpb_pje_jurisprudencia`

## Identidade

- Fonte oficial: Banco de Jurisprudencia PJe do TJPB.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `pje_jurisprudencia_estadual`.
- URL inicial: `https://pje-jurisprudencia.tjpb.jus.br/`.
- Status de acesso: `public` na busca observada; desafios de acesso continuam classificados.
- Status no NanoJuris: implementado para busca e detalhe HTML publico.

## Contrato HTTP

- Rota observada:
  - `GET /`
- Sinais do formulario:
  - ementa;
  - inteiro teor;
  - numero do processo;
  - classe;
  - orgao julgador;
  - relator;
  - data;
  - origem de documento.
- Busca: `POST /api/jurisprudencia/pesquisar` com `_token`, objeto `jurisprudencia` e `page`.
- Detalhe: `GET /jurisprudencia/view/{id}?words={termos}`.
- Paginacao: pagina baseada em um; a resposta live retornou dez hits por pagina.

## Dados retornados

- Campos esperados:
  - numero do processo;
  - classe;
  - orgao julgador;
  - relator;
  - data;
  - ementa;
  - inteiro teor ou link.
- Campos canonicos esperados: `CanonicalDecision`.
- Inteiro teor: pendente.

## Comportamento observado

- Probe `requests` com User-Agent NanoJuris: HTTP 200 e formulario publico.
- `Invoke-WebRequest`/PowerShell: Cloudflare managed challenge.
- Busca com resultado: ainda precisa fixture.
- Risco: alto enquanto o desafio variar por cliente.

## Fixtures

- [ ] HTML inicial sem desafio.
- [ ] HAR de busca real.
- [ ] Resultado com ementa.
- [ ] Busca vazia.
- [ ] Resposta Cloudflare/challenge para diagnostico.

## MCP e agentes

- Quando usar: somente depois de chamada reproduzivel sem desafio.
- Quando pular: se o ambiente receber Cloudflare, captcha ou desafio.
- Mensagem segura: "A fonte TJPB/PJe mostra formulario publico, mas o acesso
  automatizado deve respeitar eventuais desafios sem bypass."
- Riscos: variacao de WAF por cliente/ambiente.

## Validacao live 2026-08-11

- Catalogos, busca e detalhe responderam HTTP 200; a busca com `dano moral` retornou total 48.534 e 10 hits.
- O bundle confirmou os endpoints de origens, classes, orgaos, relatores, pesquisa e detalhe por `_id`; o POST exige `_token` da sessao publica.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/lucmolero/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Implementacao 2026-08-11

- `TjpbPjeJurisprudenciaProvider` obtem o token CSRF da pagina publica a cada busca.
- A busca normaliza `_id`, ementa, numero de processo, data e URL publica do detalhe.
- `get_document()` remove elementos de navegacao e preserva hash, tamanho, URL e texto HTML.
- O provider nao tenta resolver WAF, captcha ou qualquer validacao humana.

## Proximos passos

- [x] Confirmar que a busca reproduz por `requests` em sessao publica.
- [x] Criar parser e teste offline de busca e detalhe.
- [ ] Adicionar fixture de desafio quando houver uma resposta segura e nao sensivel.
