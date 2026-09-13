# Ações externas necessárias — NanoJuris

Este arquivo transforma os bloqueios restantes em solicitações reproduzíveis.
Não autoriza bypass, automação autenticada, credenciais compartilhadas ou
alteração de regras da fonte.

O índice estruturado deste pacote, atualizado no ciclo de decisões de
2026-09-09, está em `external-action-requests-20260909.json`. Ele não dispara
contatos e preserva as pendências humanas separadas das tarefas técnicas.

## 1. Falcão — Justiça do Trabalho

**Destinatário:** mantenedor indicado pelo TRT9/CSJT.  
**Objetivo:** obter contrato público de consulta, não acesso privilegiado.

Solicitar:

- URL oficial da busca e documentação de endpoints públicos;
- método, payload, paginação, ordenação e limites de frequência;
- filtros por tribunal de origem, grau, classe, tipo documental e datas;
- identificador estável e rota de detalhe/inteiro teor;
- formato de exportação ou API documentada, se existir;
- política de automação, retenção, licença e contato técnico;
- confirmação se uma sessão pública normal pode ser usada em baixa frequência;
- ambiente de homologação ou fixture oficial sanitizada para desenvolvimento.

Evidência atual: a página TRT9 confirma o escopo nacional, mas a aplicação
alternou entre shell HTTP 200 e bloqueio CloudFront 403, sem contrato de
resultados reproduzível. Ver
docs/provider-discovery/falcao-trt2-live-recheck-20260907.json.

## 2. TJAP — Tucujuris

**Destinatário:** suporte técnico/portal oficial do TJAP.  
**Objetivo:** rota pública documentada para jurisprudência textual de segundo
grau e, se existir, primeiro grau.

Solicitar:

- endpoint público de pesquisa e detalhe;
- significado dos campos de grau/instância/coleção;
- modo oficial de paginação e limites;
- política para clientes automatizados de baixa frequência;
- fixture ou exemplo público sanitizado;
- confirmação de alternativa institucional ao Turnstile;
- instruções para integração sem credencial e sem solver.

O estado atual é access_controlled. A aplicação não deve enviar tokens
resolvidos por terceiros nem tentar atravessar o desafio.

## 3. TJMA — JurisConsult

**Destinatário:** suporte técnico/portal oficial do TJMA.  
**Objetivo:** contrato público reproduzível para resultados CJSG/CJPG.

Solicitar:

- documentação das rotas de resultados e dos catálogos públicos;
- payload mínimo, paginação, filtros e enumeração de grau;
- rota de detalhe/documento e MIME esperado;
- limites de frequência e política de acesso automatizado;
- alternativa oficial ao CAPTCHA quando a consulta for pública;
- exemplo/fixture sanitizada ou ambiente de teste.

O shell e os catálogos públicos foram observados; a rota de resultados
permanece captcha_required. Isso não é vazio autoritativo.

## 4. TJRJ/TJSC — superfície CJPG ausente ou não comprovada

As rechecagens bounded não encontraram uma rota pública reproduzível de
jurisprudência textual de primeiro grau:

- TJRJ/eproc devolveu registros de segundo grau mesmo quando a consulta pediu
  `degree=first`; o contrato rejeitou a resposta por identidade incompatível.
- TJRJ EJURIS expôs apenas origens de segunda instância no formulário oficial;
  a evidência está em
  `docs/provider-discovery/tjrj-ejuris-origin-options-live-20260907.json`.
- TJSC/eproc devolveu decisões monocráticas/acórdãos de segundo grau; sua rota
  de detalhe permanece sob controle de acesso e não prova CJPG.

Solicitar aos tribunais, se a cobertura de primeiro grau for necessária:

- URL oficial da busca de sentenças/CJPG;
- enumeração de grau e instância no contrato público;
- rota de detalhe/inteiro teor e limites de uso automatizado;
- fixture ou exemplo sanitizado que identifique sentença de primeiro grau.

Enquanto não houver essa resposta oficial, manter TJRJ e TJSC como lacunas
CJPG, sem classificar as consultas incompatíveis como vazias.

## 5. TJMMG — busca pública sem limite de resposta comprovado

**Destinatário:** suporte técnico de jurisprudência do TJMMG.  
**Objetivo:** obter um contrato público limitado e reproduzível para a busca
de jurisprudência militar, sem token de reCAPTCHA e sem acesso privilegiado.

Solicitar:

- campos aceitos pelo `POST /jurisprudence/search` e semântica de número exato;
- paginação ou limite de resposta no servidor;
- rota de detalhe/arquivo, MIME e identificador estável;
- limites de frequência e política de automação de baixa frequência;
- alternativa oficial caso a busca exija reCAPTCHA.

O endpoint de metadados `GET /jurisprudencia/get` respondeu HTTP 200 e forneceu
classes e relatores. A busca `POST /jurisprudencia/search`, porém, devolveu
18,7 MB em uma sondagem textual e 30,0 MB mesmo para número inexistente; o
transporte seguro encerrou a leitura por limite. A evidência redigida está em
`docs/provider-discovery/tjm-mg-jurisprudencia-api-live-20260909.json`.
Esse estado é contrato pendente, não vazio autoritativo e não é elegível à
federação.

## 6. TJMSP — portal de jurisprudência sob controle de acesso

**Destinatário:** suporte técnico de jurisprudência do TJMSP.  
**Objetivo:** obter uma rota pública documentada para jurisprudência militar de
segundo grau, ou uma alternativa oficial para integração em baixa frequência.

Solicitar:

- URL/API oficial de pesquisa e detalhe para acórdãos e decisões;
- campos de grau, instância, classe, órgão, relator e datas;
- paginação, limites de resposta, ordenação e MIME dos documentos;
- política de automação pública e limite de frequência;
- alternativa institucional ao controle de acesso observado no portal;
- fixture ou exemplo sanitizado que possa ser usado para validar o parser.

A entrada oficial `https://jurisprudencia-client.tjmsp.jus.br/` respondeu HTTP
403 na sondagem bounded de 2026-09-10. Nenhuma credencial, cookie, token ou
técnica de contorno foi usada; o estado é `access_control_required`, não
`authoritative_empty`. A evidência está em
`docs/provider-discovery/tjmsp-jurisprudencia-live-recheck-20260910.json`.

## 7. TRT6 — API ou exportação sem reCAPTCHA

**Destinatário:** mantenedor técnico de jurisprudência do TRT6/CSJT.  
**Objetivo:** obter uma rota oficial de busca textual de segundo grau que possa
ser consultada em baixa frequência sem desafio interativo.

Solicitar:

- API ou exportação pública do Sistema de Jurisprudência PJe;
- fluxo de acesso autorizado sem geração/replay de reCAPTCHA;
- filtros, paginação, ordenação e identificador estável;
- rota de detalhe/inteiro teor, MIME e limites;
- política de automação e retenção;
- fixture ou sandbox sanitizado.

As entradas oficiais PJe e legado responderam HTTP 200, mas a busca PJe
respondeu `Erro na validação do Recaptcha` sem token legítimo. Nenhum desafio
foi resolvido, enviado ou contornado. A evidência está em
`docs/provider-discovery/trt6-jurisprudencia-live-20260910.json`; o provider
permanece diagnóstico/opt-in e não federado.

## 8. Revisão humana do ranking

O revisor deve receber apenas IDs sanitizados e os campos necessários para
julgamento. Para cada consulta, atribuir:

- 0 — irrelevante;
- 1 — relacionado, mas não responde;
- 2 — relevante;
- 3 — altamente relevante.

Procedimento:

1. separar development e holdout antes de ver os scores;
2. usar dois julgadores independentes;
3. abrir terceiro julgamento quando a diferença for pelo menos 2;
4. calibrar pesos somente no development;
5. medir o holdout uma única vez;
6. registrar versão do dataset, julgadores, conflitos e data;
7. não registrar texto de consulta identificável, dados pessoais ou inteiro teor
   fora do material autorizado.

Métricas do gate: nDCG@10, precision@5, MRR@10, irrelevantes no top 5 e p95.
Sem esses rótulos, T62 permanece pendente por desenho.

## 9. Pacote que deve ser anexado a qualquer solicitação

- URL e tribunal;
- data/hora e método da tentativa bounded;
- status HTTP e classificação;
- hash/tamanho do corpo, sem corpo bruto quando houver dados pessoais;
- screenshot ou HAR somente da navegação pública normal, redigido;
- contrato esperado e campos necessários;
- limite de frequência pretendido;
- contato responsável pelo retorno.

Após uma resposta oficial, reexecutar somente a rota autorizada, gerar fixture
sanitizada, testar parser/paginação/filtros e atualizar o SDD correspondente.
## SJUR/TRE — contrato por UF

Solicitar ao mantenedor técnico do TSE/SJUR o contrato oficial de paginação
por TRE e uma rota de detalhe/download que retorne PDF válido ou documente o
inteiro teor inline. A consulta pública já retorna uma janela textual em 26
UFs, mas a segunda página repete a primeira e alguns downloads retornam corpo
de erro; por isso o binding permanece opt-in.
