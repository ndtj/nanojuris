# `falcao_jt`

## Identidade

- Fonte institucional: Sistema Falcao da Justica do Trabalho.
- Gestao/normalizacao: TRT9 em parceria com CSJT.
- Categoria: `court_jurisprudence`.
- URL publica conhecida: `https://jurisprudencia.jt.jus.br/`.
- Status de acesso no probe NanoJuris: bloqueado/inconclusivo.
- Status no NanoJuris: candidato de alta prioridade, sem provider.

O Falcao deve ser investigado como uma fonte nacional da Justica do Trabalho,
e nao como um provider isolado do TRT9. A comunicacao institucional informa
que o repositorio reune documentos de primeiro e segundo graus, TST e
precedentes qualificados. A cobertura efetiva e o contrato tecnico precisam
ser confirmados na interface e nas respostas reais.

## Evidencia institucional

As paginas oficiais do TRT9 e do CNJ descrevem o Falcao como repositorio
oficial/nacional da jurisprudencia trabalhista, com consulta para o publico em
geral. Os tipos mencionados incluem sentencas, acordaos, decisoes de
admissibilidade de recurso de revista, decisoes monocraticas e precedentes.

## Probe tecnico

Em 2026-08-10, uma requisicao GET limpa para a raiz publica respondeu:

- HTTP 403;
- pagina de bloqueio CloudFront;
- nenhum resultado ou contrato de API observavel;
- sem login ou captcha visivel, mas com `request_blocked`.

Esse resultado pode ser especifico do ambiente, da rede ou de uma politica
temporaria da distribuicao. Nao e evidencia suficiente para afirmar que a
fonte exige autenticacao, nem autoriza contornar o bloqueio.

## Contrato pendente

Ainda precisam ser descobertos e validados:

- rota de entrada e arquivos JavaScript publicos;
- endpoint de pesquisa, metodo e payload;
- filtros por tribunal, classe, tipo documental e datas;
- paginacao, ordenacao e total de resultados;
- identificador e URL de detalhe/inteiro teor;
- limites de requisicao e politica de acesso automatizado;
- formato de exportacao, se houver.

## Decisao de engenharia

- Nao implementar parser ou bypass com base apenas em pagina institucional.
- Nao reutilizar cookies, tokens ou sessao de navegador para contornar 403.
- Priorizar um HAR obtido por consulta publica normal, sem credenciais, para
  fechar o contrato.
- Se o bloqueio persistir, registrar a fonte como indisponivel para o provider
  e manter TST como fonte independente.

## Proximos passos

1. Repetir um GET de baixa frequencia em outra janela controlada.
2. Capturar HAR de uma busca publica curta, se o acesso normal estiver
   disponivel no navegador do mantenedor.
3. Inspecionar somente assets e chamadas publicas do proprio fluxo.
4. Criar fixtures de sucesso, vazio e bloqueio antes de qualquer provider.
5. Avaliar se o Falcao pode substituir parte da coleta individual de TRTs,
   preservando `SourceTrace` com a origem tribunal/documento.

## Validacao live 2026-08-11

- GET da raiz respondeu HTTP 403 com pagina CloudFront; nenhuma rota de busca foi chamada com bypass.
- O candidato permanece bloqueado/inconclusivo e depende de nova evidencia publica normal ou HAR sem credenciais.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Referencias oficiais

- https://www.trt9.jus.br/portal/pagina.xhtml?pagina=FALCAO&secao=168
- https://www.cnj.jus.br/conheca-o-falcao-o-repositorio-oficial-de-jurisprudencia-da-justica-do-trabalho/
- https://jurisprudencia.jt.jus.br/
## Dados E Campos Do Contrato

Nenhum payload decisorio foi obtido na janela validada. Os campos esperados, a confirmar, sao tribunal de origem, grau, classe, tipo documental, numero, relator, orgao, data, ementa, texto e URL de documento. A cobertura anunciada inclui sentencas, acordaos, decisoes monocraticas, admissibilidade de recurso de revista e precedentes, mas isso e escopo institucional, nao resposta tecnica reproduzida.

## MCP

O MCP deve omitir o Falcao da busca executavel enquanto a raiz responder 403 ou nao houver contrato de resultados. Pode expor a fonte como blocked_or_inconclusive, com o motivo e a data da verificacao. Nunca reutilizar cookies, tokens ou contornar CloudFront.
