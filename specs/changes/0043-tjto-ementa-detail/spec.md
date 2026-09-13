# 0043 - detalhe lazy de ementa do TJTO

Status: verified
Owner: Provider Engineering, Legal Data, Security e QA

## Intencao

Enriquecer resultados do provider TJTO com detalhe publico de ementa quando a
listagem nao trouxer conteudo, sem apagar o resultado base nem transformar uma
falha parcial em vazio.

## Requisitos

- REQ-001: identificar a rota de detalhe e seu contrato sem depender de login;
- REQ-002: executar detalhe somente sob demanda (lazy), com budget e timeout;
- REQ-003: preservar documento base, detalhe, hashes e `SourceTrace` separados;
- REQ-004: erro do detalhe retorna resultado base com estado parcial observavel;
- REQ-005: identidade 0037 evita duplicacao e registra a origem de cada campo;
- REQ-006: nao importar Juscraper, cookies ou controles de acesso em runtime.

## Criterios de aceite

- AC-001: fixture contem listagem sem ementa e detalhe correspondente;
- AC-002: sucesso, 404, timeout, 403 e schema drift do detalhe tem outcomes distintos;
- AC-003: o parser nunca inventa ementa e nunca remove campos da listagem;
- AC-004: testes de merge, completude e provenance passam;
- AC-005: feature fica opt-in ate revisao de reuso e release.

## Fora de escopo

Coleta em massa, consulta processual, bypass de CAPTCHA/WAF e alteracao de
provider default ou producao.
