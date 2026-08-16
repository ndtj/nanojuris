# QA de navegador do NanoJuris Studio

O Studio possui duas camadas de teste:

- testes unitarios e de API em `tests/test_studio.py`;
- testes de navegador em `tests/e2e/` usando Playwright.

Os testes de navegador usam um cliente em memoria. Isso torna a validacao
deterministica e impede que WAF, timeout ou mudancas nos tribunais alterem os
resultados visuais. As chamadas live devem permanecer em uma rotina separada.

## Instalar

Na raiz do repositorio:

```powershell
python -m pip install -e ".[dev,studio,qa]"
python -m playwright install chromium
```

## Executar

Rodar apenas a auditoria E2E:

```powershell
pytest -m e2e -q
```

Executar com browser visivel:

```powershell
pytest -m e2e --headed -q
```

## Capturar screenshots

Os screenshots sao opt-in para nao criar ruido no repositorio:

```powershell
$env:NANOJURIS_CAPTURE_STUDIO="1"
pytest -m e2e -q
```

Os arquivos serao gravados em `artifacts/studio/`, que e ignorado pelo Git.

## Escopo atual

A primeira suite cobre:

- carregamento do catalogo de fontes;
- busca bem-sucedida;
- falha parcial;
- estado vazio;
- expansao de resultado;
- link documental;
- responsividade mobile;
- ausencia de overflow horizontal;
- alcance dos controles principais por teclado;
- ausencia de erros JavaScript no console.

Em caso de falha, o fixture grava um trace navegavel em `test-results/` para
investigar a sequencia de eventos, requisicoes e estado visual do navegador.

O workflow `.github/workflows/studio-e2e.yml` executa essa suite em Chromium
com fixtures locais e sem consultar tribunais externos.

Uma auditoria manual contra o Studio real, com prints desktop/mobile e uma
validacao live controlada dos 40 providers, esta em
[studio-provider-audit-2026-08-15.md](studio-provider-audit-2026-08-15.md).
