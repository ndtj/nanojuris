# Live Validation 2026-08-11

> Este documento e um snapshot historico da rodada inicial com 26 providers.
> Para a fotografia atual da release, consulte tambem
> [implementation-live-validation-2026-08-11.md](implementation-live-validation-2026-08-11.md)
> e [unified-search-live-validation-2026-08-11.md](unified-search-live-validation-2026-08-11.md).

Rodada controlada contra os 26 providers implementados, usando consultas
pequenas, `trust_env=False`, SSL habilitado por padrao, sem cookies exportados,
login, captcha, proxy de contorno ou sessao de navegador.

Os totais abaixo sao observacoes desta rodada, nao promessa de estabilidade ou
de completude do acervo. Respostas de acesso, timeout e parser tambem sao
resultados contratuais importantes.

## Resumo

- 26 providers exercitados.
- 23 buscas retornaram dados normalizados.
- BNP retornou 400 sem filtros de orgao/especie, mas 200 com catalogo e filtros
  publicos validos.
- STF Informativo funcionou com SSL desabilitado somente para diagnostico local;
  o padrao continua sendo verificacao SSL habilitada.
- STF Jurisprudencia respondeu desafio AWS WAF no diagnostico sem SSL.
- STJ/SCON e TJSP/CJSG responderam controle de acesso esperado.
- TNU funcionou depois de ampliar o timeout da chamada de descoberta para 60s.
- TRE-SP revelou que os temas apontam diretamente para PDFs oficiais; o parser
  foi ajustado para preservar esses links sem fingir extracao de PDF.

## Matriz De Evidencia

| Provider | Busca live | Documento/inteiro teor | Evidencia observada | Acao |
| --- | --- | --- | --- | --- |
| `bnp_pangea` | 400 sem filtros; 200 filtrada, total 100 | nao repetido | catalogo trouxe STF/STJ e especies RG/RR | exigir filtros de catalogo na busca livre |
| `comunica_pje` | ok, total 1270 | nao aplicavel | `/api/v1/comunicacao` | manter como comunicacoes, nao jurisprudencia |
| `tnu_eproc_jurisprudencia` | ok, total 10 com timeout 60s | publico, HTML, 118582 caracteres | rota eproc e download publico | documentar timeout e rate limit |
| `stf_informativo` | ok, total 394 em diagnostico SSL | nao aplicavel | XLSX oficial | nao desabilitar SSL por padrao |
| `stf_juris` | AWS WAF apos diagnostico SSL | nao promovido | `POST /api/search/search` | manter acesso controlado, sem bypass |
| `stj_informativo` | ok, total 8 | nao aplicavel | HTML oficial | manter como informativo curado |
| `stj_scon` | controle de acesso | nao promovido | verificacao automatica | manter parser offline e erro explicito |
| `stm_jurisprudencia` | ok, total 25 | publico, HTML, 330467 caracteres | busca e eproc STM | manter suporte documental |
| `tst_jurisprudencia` | ok, total 966847 | publico, HTML, 85170 caracteres | REST JSON + documento | ampliar fixtures de filtros |
| `tce_sp_jurisprudencia` | ok, total 13 | nao aplicavel | catalogos de sumulas/boletins | nao prometer busca geral |
| `tjac_cjsg` | ok, total 5 | controle de acesso | busca publica, arquivo protegido | reportar bloqueio do documento |
| `tjac_esaj_cpopg` | ok, total 1 | publico, HTML, 9708 caracteres | numero CNJ | manter consulta processual separada |
| `tjdf_juris` | ok, total 31 | publico, HTML, 12970 caracteres | SISTJ | fonte madura para demonstracao |
| `tjgo_projudi_jurisprudencia` | ok, total 1360550 | texto embutido; download separado nao promovido | POST `/ConsultaJurisprudencia` | limitar pagina e declarar truncamento |
| `tjal_cjsg` | ok, total 12 | controle de acesso | busca publica, arquivo protegido | reportar bloqueio do documento |
| `tjam_cjsg` | ok, total 12 | controle de acesso | busca publica, arquivo protegido | reportar bloqueio do documento |
| `tjms_cjsg` | ok, total 22 | publico, HTML, 30364 caracteres | CJSG + `getArquivo.do` | manter suporte documental |
| `tjpi_juspi` | ok, total 193030 | publico, texto, 6739 caracteres | JusPI | documentar limite do acervo e pagina |
| `tjsp_cjsg` | controle de acesso | nao consultado | captcha/formulario de acesso | nao usar paginacao sem busca valida |
| `tjsp_eproc_jurisprudencia` | ok, total 1 | nao promovido | eproc TJSP | preservar `full_text_url` sem prometer leitura |
| `tjsp_esaj_cpopg` | ok por numero CNJ | numero direto publico; id sintetico inconsistente | `1076539-20.2019.8.26.0100` funcionou | preferir numero CNJ como identificador |
| `tjsp_nugepnac` | ok, total 2 | nao aplicavel | IRDR publico | manter catalogo de precedentes |
| `tre_sp_temas` | ok, total 1 apos ajuste | PDF oficial preservado | `application/pdf` | parser nao interpreta PDF sem extrator |
| `trf2_eproc_jurisprudencia` | ok, total 10 | publico, HTML, 52331 caracteres | eproc federal | manter |
| `trf4_eproc_jurisprudencia` | ok, total 10 | publico, HTML, 278398 caracteres | eproc federal | manter |
| `trf6_eproc_jurisprudencia` | ok, total 10 | publico, HTML, 40597 caracteres | eproc federal | manter |

## Limites Da Rodada

Uma busca valida prova que o contrato funcionou naquele momento, com aquele
termo e naquela rede. Ela nao prova cobertura integral, estabilidade de
seletores, ausencia de rate limit ou disponibilidade futura.

O diagnostico STF com `verify_ssl=False` foi usado somente para separar falha
de cadeia local de resposta da fonte. O projeto continua seguro por padrao com
`verify_ssl=True`; a resposta posterior foi AWS WAF, nao ausencia de dados.

## Reproducao

Para repetir a validacao, use o mesmo conjunto de consultas com timeout pequeno,
`trust_env=False` apenas quando o ambiente tiver proxy local quebrado, e
preserve somente metadados de status, endpoint, total, content type e tamanho.
Nao versionar respostas integrais nem tokens de sessao.
