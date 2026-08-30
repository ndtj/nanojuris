# Provider Development Guide

Este guia define o padrao minimo para adicionar novas fontes publicas ao
NanoJuris. O objetivo e permitir expansao nacional com qualidade, sem transformar
cada tribunal em uma excecao acoplada ao core.

Escopo permitido: extracao objetiva de dados publicos, rastreabilidade,
normalizacao, persistencia e exportacao. O provider nao deve interpretar merito,
recomendar tese, redigir argumento ou contornar captcha, login, segredo de
justica ou qualquer controle de acesso.

## Checklist antes de implementar

Antes de escrever codigo, a equipe deve reproduzir a entrada publica com uma
sessao HTTP limpa, usando o fluxo de [source-discovery.md](source-discovery.md).
Isso evita alterar o core enquanto a rota ainda e hipotese.

A ficha de fonte deve registrar:

- nome publico da fonte;
- URL inicial e endpoints observados;
- tipo de conteudo: API JSON, HTML, PDF publico, catalogo ou misto;
- parametros de busca;
- paginacao;
- campos juridicos objetivos disponiveis;
- tipos documentais;
- status de acesso esperado;
- exemplos publicos representativos;
- limites de uso responsavel;
- riscos conhecidos: captcha, instabilidade, rate limit, mudanca frequente.

Uma rota so deve virar provider quando o probe confirmar status, URL final,
texto esperado e ausencia de bloqueio exclusivo por captcha/login/Turnstile. Se
a reproducao exigir estado de navegador, a descoberta deve ser registrada como
bloqueada e nao promovida para fetch automatico.

Responsabilidades de revisao:

- pesquisa e ficha da fonte;
- acesso responsavel;
- viabilidade tecnica;
- campos juridicos objetivos;
- criterios de fixture e teste.

## Contrato minimo do provider

Todo provider deve implementar `JurisprudenceProvider`:

```python
from nanojuris.models import DecisionBundle, JurisprudenceQuery, SearchPage
from nanojuris.providers.base import JurisprudenceProvider


class ExampleProvider(JurisprudenceProvider):
    name = "example"

    def search(self, query: JurisprudenceQuery) -> SearchPage: ...

    def get_decisions(self, precedent_id: str) -> DecisionBundle: ...
```

Tambem deve declarar `ProviderCapabilities`:

```python
def get_capabilities(self) -> ProviderCapabilities:
    return ProviderCapabilities(
        source=self.name,
        display_name="Fonte Exemplo",
        source_url="https://example.test",
        category="court_jurisprudence",
        search_modes=["text", "case_number"],
        document_types=["acordao"],
        content_formats=["html"],
        canonical_records=["CanonicalDecision"],
        extracted_fields=["case_number", "summary", "document_url"],
        access_statuses=[AccessStatus.PUBLIC, AccessStatus.ACCESS_CONTROL_REQUIRED],
        limitations=["A fonte pode exigir controle de acesso."],
        responsible_use=["Nao tentar contornar captcha ou login."],
    )
```

## Separacao obrigatoria

O provider deve separar responsabilidades sempre que possivel:

- fetch: aquisicao HTTP e status de acesso;
- parse: conversao de HTML/JSON/PDF em estrutura intermediaria;
- map: conversao para `JurisprudenceResult`;
- canonical: mapeamento para `CanonicalDecision`, `CanonicalPrecedent` ou
  `CanonicalDocument` quando aplicavel;
- diagnostics: capabilities e limites da fonte.

Essa separacao facilita testes offline, benchmark, correcao de layout e
reprocessamento futuro.

## SourceTrace e ExtractionTrace

Cada resultado normalizado deve preservar origem:

- `SourceTrace.provider`;
- endpoint ou URL;
- payload de consulta quando seguro;
- timestamp quando aplicavel.

Quando houver parsing/canonicalizacao, o registro canonico deve preservar:

- parser;
- parser_version;
- access_status;
- extraction_status;
- hash do conteudo bruto quando disponivel.

## Erros e acesso

Providers devem transformar problemas de fonte em erros claros:

- fonte indisponivel;
- HTTP inesperado;
- contrato alterado;
- captcha ou controle de acesso;
- resposta vazia;
- parametros invalidos.

Controle de acesso nao e desafio tecnico a ser vencido. E um estado da fonte que
deve ser declarado ao usuario.

## Fixtures e testes

Cada provider novo deve incluir:

- fixture offline publica representativa;
- teste de parser;
- teste de busca com cliente fake ou resposta mockada;
- teste de `get_capabilities`;
- teste live opcional, desligado por padrao;
- teste para captcha/controle de acesso quando a fonte tiver esse comportamento.

Padrao de live test:

```python
pytestmark = pytest.mark.skipif(
    os.environ.get("NANOJURIS_RUN_EXAMPLE_LIVE") != "1",
    reason="Set NANOJURIS_RUN_EXAMPLE_LIVE=1 to query live public source",
)
```

## Criterios de aceite para PR

Um provider so deve entrar no core quando:

- passa em testes offline;
- declara capabilities completas;
- documenta fonte, parametros e limitacoes;
- nao faz bypass;
- inclui fixtures publicas representativas;
- retorna erros acionaveis;
- preserva `SourceTrace`;
- gera modelos canonicos quando houver mapeamento confiavel;
- atualiza roadmap, providers docs e matriz de casos se necessario.

## Ordem recomendada para novas fontes

1. Registrar entrada manual feita no navegador.
2. Reproduzir a rota com `examples/source_route_probe.py` e sessao limpa.
3. Classificar a rota como validada, bloqueada ou inconclusiva.
4. Pesquisar fonte e preencher ficha.
5. Criar fixture offline.
6. Implementar parser da fixture.
7. Implementar provider com fetch responsavel.
8. Declarar capabilities.
9. Mapear para modelos normalizados.
10. Adicionar canonical mapper quando seguro.
11. Cobrir CLI/client/export/store quando aplicavel.
12. Rodar benchmark offline.
13. Documentar limitacoes.
