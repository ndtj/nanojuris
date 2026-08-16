# Changelog

Todas as mudancas relevantes deste projeto serao documentadas aqui.

## Unreleased

- Corrigido o descarte silencioso de filtros de refinamento na busca unificada,
  com avisos de contrato por fonte.
- Corrigido o mapeamento de datas e booleanos no TJDFT/SISTJ, incluindo
  `DataPublicacao`, `DataJulgamento` e a opcao `fetch_details` sem N+1.
- MCP agora expoe data, frase exata e relator, usa TJDFT como default operacional
  e permite paginar consultas locais com `total`, `has_more` e `next_offset`.
- Consultas MCP sem registro retornam `found=false` em vez de excecao esperada;
  o teto de pagina foi alinhado ao limite publico de 100 do core.
- Corrigida a serializacao do formulario AJAX eproc: selects multivalorados sem
  selecao nao adicionam filtros artificiais, e checkbox marcado sem valor usa
  o valor HTML padrao `on`.
- Corrigido o parser TJPR para aceitar os links publicos de acordaos e decisoes;
  a busca agora preserva a janela de resultados e a paginação observadas.
- Declarado o limite remoto de 10 itens por pagina do TJAM e TJRR; a repeticao
  de pagina no postback TJRR continua sendo erro explicito de contrato.
- Implementado o provider REST publico do TJPE, com paginacao zero-based,
  `X-Total-Count`, datas separadas, texto de ementa/acordao/decisao, hash da
  resposta e classificacao explicita de erros HTTP.
- Implementado o provider publico do TJCE/CJSG, reutilizando o contrato e-SAJ
  compartilhado e mantendo barreiras de acesso observaveis.
- Implementado o provider publico do TJCE/SJURIS, com busca REST zero-based,
  texto integral inline, preservacao do payload PDF quando presente, limite
  remoto observado de 20 itens e classificacao explicita de erros HTTP.
- Implementado o provider publico do TJMT, lendo a configuracao publica em
  runtime, paginando a API de acordaos, separando datas e extraindo o inteiro
  teor HTML inline sem persistir o token de aplicacao.
- Implementado o provider publico do TJTO/Jurisprudencia 4.0, com paginacao por
  offset, ementas estruturadas e inteiro teor HTML sob demanda preservado com
  hash, tamanho e content-type.
- Implementado o provider de catalogo publico do TJMA/JurisConsult. A busca
  decisoria permanece explicitamente protegida por captcha e fora da federacao.
- Implementado o provider do LIAME/TJRO para precedentes qualificados, fora da
  busca textual geral e com processos paradigma preservados.

## 0.3.0 - 2026-08-13

- Provider publico de jurisprudencia do TJPR com busca HTML, filtros observados,
  metadados de decisao, ementa e links oficiais.
- Provider de Informativos de Jurisprudencia do CNJ com filtros, catalogo curado,
  links oficiais e preservacao de PDF sob demanda com SHA-256.
- Provider de Informativos de Jurisprudencia do TJCE com edicoes, itens,
  metadados processuais, filtros publicos e links oficiais.
- Fixtures, testes de contrato, validacoes live e dossies canonicos/legados para
  os tres novos providers.
- Registro, fila de desenvolvimento e auditoria documental atualizados para
  37 providers implementados e 19 fontes candidatas.

## 0.2.0 - 2026-08-11

- Provider TST com fixtures e contrato REST publico documentado.
- Providers adicionais para TJPB, TJPA, TJRS, TJRJ, TJSC, TRF5, CJF/TRF1 e TCU.
- Busca unificada ampliada para todas as categorias jurisprudenciais, com
  roteamento por filtros declarados e diagnostico por fonte.
- Probe de rotas com timeout de conexao/leitura, limite de bytes e diagnosticos
  de resposta parcial.
- Registro central de fontes e dossies individuais para humanos e agentes de IA.
- Validacao de paridade entre dossies canonicos e caminhos legados.

## 0.1.0 - 2026-08-02

- Fundacao inicial do NanoJuris.
- Provider BNP/Pangea com API publica de precedentes.
- Modelos tipados para precedentes, casos paradigma, decisoes e pagina de busca.
- Cliente Python, CLI, exportadores JSONL/Markdown e testes automatizados.
- Catalogo normalizado do BNP/Pangea para orgaos e especies.
- Sugestoes publicas de busca expostas no provider, cliente e CLI.
- Fixtures cobrindo RG, RR, IAC, IRDR, SUM e SV.
- Testes live opcionais controlados por `NANOJURIS_RUN_LIVE=1`.
- Provider TJSP/CJSG com parser HTML, fixture sanitizada e deteccao de captcha.
- Providers publicos adicionados para Comunica PJe/DJEN, TJDFT/SISTJ,
  TJAC/TJAL/TJAM/TJMS CJSG, STM/JMU, TJSP/eproc, TJSP/e-SAJ CPOPg,
  TRF4/eproc e STJ/SCON.
- Modelos canonicos, store SQLite, exportacao CSV/JSONL/Markdown, CLI expandida
  e tools MCP locais.
- Fluxo de descoberta documentado para promover somente rotas reproduzidas com
  `requests` limpo, sem login, captcha, cookies ou bypass.
