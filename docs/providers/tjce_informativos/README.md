# `tjce_informativos`

## Identidade

- Fonte oficial: Informativos de Jurisprudencia do TJCE.
- Categoria: `curated_jurisprudence`.
- Familia tecnica: `institutional_html_pdf`.
- URL: `https://www.tjce.jus.br/informativo-jurisprudencia/`.
- Status de acesso: `candidate_ready`.
- Status no NanoJuris: candidato, sem provider implementado.

Esta fonte e uma curadoria oficial de decisoes consideradas relevantes pelos
orgaos colegiados do TJCE. Ela nao substitui o repositorio geral de acordaos e
nao deve ser apresentada como se representasse todo o posicionamento do
tribunal.

## Contrato observado

```text
GET https://www.tjce.jus.br/informativo-jurisprudencia/
```

Em 2026-08-11, a rota respondeu em sessao HTTP limpa:

- HTTP 200;
- HTML UTF-8;
- pagina com edicoes de informativos;
- itens com processo, orgao julgador, ramo do direito, assunto e destaque;
- links oficiais para leitura completa e downloads de edicoes.

A interface publica filtros para busca livre, tipo de edicao, ramo do direito,
assunto, orgao julgador, relator, numero/ano da edicao e datas de julgamento ou
publicacao. O HTML inicial tambem continha links PDF oficiais.

## Dados canonicos possiveis

O parser deve extrair, quando presentes:

- identificador e numero da edicao;
- data ou periodo da edicao;
- processo;
- orgao julgador;
- relator ou julgador;
- ramo do direito;
- assunto;
- destaque/entendimento resumido;
- URL oficial do item;
- URL do PDF ou formato de download;
- texto bruto do item.

O tipo canonico recomendado e `CanonicalPrecedent` ou um tipo curado
equivalente, nao `CanonicalDecision` de acordao completo. O provider deve
preservar a indicacao de que o informativo e uma sintese editorial e nao
inventar ementa, tese vinculante ou inteiro teor quando esses campos nao
estiverem presentes.

## Limites e riscos

- A pagina e HTML institucional e pode alterar seletores sem aviso.
- Downloads podem ser gerados por controles da pagina, e nao por links estaticos
  no HTML inicial.
- A curadoria nao representa necessariamente a jurisprudencia prevalente do
  TJCE.
- O conteudo do informativo nao deve ser confundido com o acervo completo do
  CJSG.

## Fixtures necessarias

- [ ] HTML de uma edicao com itens de mais de um ramo.
- [ ] HTML de resultado filtrado por termo ou edicao.
- [ ] Fixture vazia ou sem correspondencias.
- [ ] PDF oficial de uma edicao para teste opt-in do extrator.
- [ ] Parser HTML offline com testes de encoding e links.

## MCP e agentes

O MCP pode oferecer uma ferramenta de consulta aos informativos depois do
parser offline. A descricao deve dizer que a fonte e curada, indicar a edicao e
o link oficial, e evitar respostas que transformem um destaque editorial em
conclusao geral sobre todo o tribunal.

## Validacao live 2026-08-11

- GET do portal de informativos respondeu HTTP 200 com 489 KB de HTML e sinais de jurisprudencia, ementa, relator e processo.
- O contrato e documental/curado; links e PDFs devem ser tratados separadamente da busca geral de acordaos.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/lucmolero/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Proximos passos

1. Salvar fixture HTML pequena e representativa.
2. Implementar parser dos itens, filtros visiveis e links oficiais.
3. Testar download de PDF sob demanda, sem incluir acervo inteiro no CI.
4. Mapear o filtro textual e paginacao, se forem submetidos por AJAX.
5. Criar provider separado do `tjce_cjsg`.
