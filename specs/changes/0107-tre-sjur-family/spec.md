# SDD 0107 — família SJUR/TRE opt-in

Status: `verified`  
Owner: Provider Engineering  
Data: `2026-09-10`

## Objetivo

Oferecer um binding de família para as 27 rotas regionais do SJUR/TRE, exigindo
autoridade explícita e mantendo cada UF isolada no adapter existente.

## Escopo

- despacho por `authority=TRE-XX` ou `TREXX`;
- transporte oficial público com limite, rate limit e trace;
- filtragem conservadora de primeiro grau e rótulos desconhecidos;
- janela textual opt-in, sem alegação de paginação exaustiva;
- integração no cliente de candidatos e no catálogo de providers.

## Fora de escopo

- federação padrão;
- contorno de CAPTCHA, WAF, tokens ou controles de acesso;
- inferência de segundo grau para rótulo desconhecido;
- alegação de inteiro teor quando o download não validar PDF;
- deploy, credenciais ou produção.

## Requisitos e aceite

- **REQ-001/AC-001** — a família exige `authority` explícita e aceita apenas uma UF TRE válida.
- **REQ-002/AC-002** — o dispatcher delega para `TreSjurJurisprudenciaProvider` sem duplicar parser/transporte.
- **REQ-003/AC-003** — resultados preservam autoridade, ramo, grau, instância, coleção e `SourceTrace`.
- **REQ-004/AC-004** — páginas diferentes de 1 são rejeitadas até que a fonte prove paginação.
- **REQ-005/AC-005** — a família fica opt-in e não é habilitada na federação padrão.
