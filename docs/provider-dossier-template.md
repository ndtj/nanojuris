# Provider Dossier Template

Este e o contrato editorial e tecnico para qualquer fonte do NanoJuris. O
dossie deve ser especifico para uma fonte, mesmo quando o parser compartilha
uma familia tecnica com outros tribunais.

O texto pode declarar `nao observado`, `nao aplicavel` ou `pendente`, mas nunca
deve deixar um campo importante em branco. Uma observacao pendente precisa
indicar a evidencia que falta e o criterio para fechar o contrato.

## 1. Controle Do Documento

- `source_id`:
- Status do ciclo de vida: `implemented`, `candidate`, `family` ou `retired`.
- Nivel de evidencia: `A` (replay HTTP e fixture), `B` (interface oficial e
  chamada parcial), `C` (evidencia institucional) ou `D` (hipotese).
- Ultima verificacao: `YYYY-MM-DD`.
- Responsavel pela verificacao:
- Documento canonico: `docs/providers/<source_id>/README.md`.
- Compatibilidade: `docs/source-contracts/<source_id>.md`.

## 2. Identidade E Escopo

- Fonte oficial, orgao mantenedor e URL de entrada.
- Categoria: jurisprudencia, precedente, informativo, comunicacao ou consulta
  processual.
- Familia tecnica.
- O que a fonte cobre.
- O que a fonte nao cobre e nao deve ser inferido.
- Regra de separacao entre jurisprudencia, comunicacoes e processos.

## 3. Contrato HTTP Observado

Use uma tabela por rota. Rotas apenas encontradas em JavaScript ou HAR devem
ser marcadas como `observada`, e nao como `operacional`, ate haver replay.

| Rota | Metodo | Finalidade | Entrada | Saida | Estado | Evidencia |
| --- | --- | --- | --- | --- | --- | --- |
| `/...` | `GET`/`POST` | busca/detalhe/documento/catalogo | parametros/payload | JSON/HTML/PDF | operacional/observada/bloqueada | fixture/HAR/live |

Documente tambem:

- base URL, headers realmente necessarios e content types;
- parametros obrigatorios, opcionais, tipos e exemplos;
- paginacao, ordenacao, filtros, limites tecnicos e janela temporal;
- tokens de sessao publicos, ViewState ou CSRF quando forem parte normal do
  fluxo; nunca versionar cookies, credenciais ou tokens pessoais;
- formato de data, codificacao, charset e comportamento de consultas vazias.

## 4. Modelo De Dados

Mapeie cada campo observado para o modelo canonico, sem preencher lacunas por
heuristica juridica.

| Campo de origem | Tipo | Cardinalidade | Campo canonico | Presenca | Evidencia | Observacao |
| --- | --- | --- | --- | --- | --- | --- |
| `campo` | string/date/list | 0..1/1 | `summary` | observado/ausente/variavel | fixture/live | regra |

Liste explicitamente tipos documentais, identificadores, ementa, datas,
relator, orgao, origem, URL, inteiro teor e metadados brutos. Diferencie
ementa, resumo editorial, trecho de resultado e texto integral.

## 5. Estados E Falhas

| Estado | Sinal verificavel | Tratamento | Pode rotear automaticamente? |
| --- | --- | --- | --- |
| Sucesso | status e estrutura | normalizar e preservar trace | sim, se maduro |
| Vazio | resposta valida sem itens | retornar pagina vazia | sim |
| Parametro invalido | 400/validacao | erro acionavel | nao |
| Acesso controlado | captcha/login/WAF | `AccessControlRequiredError` | nao |
| Rate limit | 429/Retry-After | `RateLimitDetectedError` | somente politica explicita |
| Indisponivel | 5xx/timeout/TLS | `SourceUnavailableError` | nao |
| Contrato alterado | markup/schema inesperado | `ParserContractChangedError` | nao |

Nao classifique bloqueio como zero resultados e nao trate timeout como prova de
que a fonte nao existe.

## 6. Evidencias, Fixtures E Testes

Registre o arquivo, a data, o tipo de resposta e o que ele prova. Fixtures
devem ser pequenas, publicas, reproduziveis e livres de cookies, credenciais,
headers pessoais e dados desnecessarios.

| Evidencia | Arquivo/URL | Prova | Teste |
| --- | --- | --- | --- |
| sucesso | `tests/fixtures/...` | resultado e campos | `test_...` |
| vazio | `tests/fixtures/...` | zero resultados | `test_...` |
| erro/acesso | `tests/fixtures/...` | classificacao | `test_...` |
| documento | `tests/fixtures/...` | inteiro teor publico | `test_...` |

Separe testes offline, testes com respostas mockadas e testes `live` opt-in.

## 7. Implementacao E Capacidades

- Modulo e classe do provider.
- `ProviderCapabilities` declaradas.
- Modos de busca e tipos documentais.
- Mapeamento canonico (`CanonicalDecision`, `CanonicalPrecedent` ou
  `CanonicalDocument`).
- Suporte a `get_document`, catalogo, sugestoes e MCP.
- Limites de pagina, timeout, retries e rate limit.
- Campos preservados em `raw`, `SourceTrace` e `ExtractionTrace`.

## 8. MCP E Agentes

- Quando usar a fonte.
- Quando pular a fonte.
- Preflight obrigatorio (`list_sources` e `source_contracts`).
- Como reportar `searched_sources`, `skipped_sources` e `errors`.
- Mensagem operacional segura para acesso controlado, truncamento e documento
  indisponivel.
- Perguntas naturais suportadas e perguntas fora do escopo.

O agente deve retornar dados e rastreabilidade, nao conclusao juridica
inventada. O provider extrai; a revisao profissional interpreta.

## 9. Promocao Para Codigo

Uma fonte candidata so pode virar provider depois de:

- contrato de rota reproduzido sem credenciais ou bypass;
- fixture de sucesso e vazio;
- erro ou bloqueio classificado;
- parser offline e teste de contrato;
- campos canonicos e limites documentados;
- dossie, registry, capabilities e testes atualizados;
- decisao explicita sobre documento, MCP, rate limit e uso responsavel.

## 10. Lacunas E Historico

Use checklist para cada pendencia. Toda pendencia deve ser verificavel:

- [ ] lacuna objetiva, evidencia que falta e proximo experimento;
- [ ] contrato revisado apos mudanca da fonte;
- [ ] changelog atualizado quando houver alteracao publica.

O auditor em `tools/audit_provider_docs.py` gera a matriz consolidada. O
relatorio nao substitui o dossie: ele mostra se o dossie esta pronto para
pesquisa, implementacao ou roteamento por agente.
