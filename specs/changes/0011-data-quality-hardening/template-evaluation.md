# Avaliação do template externo

## Resultado

A pasta `C:\Users\admin\Downloads\lib template` foi identificada como um
snapshot do projeto Scrapling, de Karim Shoair/D4Vinci (versão 0.4.15). O
snapshot local não contém o arquivo de licença, mas o projeto upstream declara
BSD-3-Clause. Ainda assim, nenhum código foi copiado literalmente para a
NanoJuris; somente um padrão genérico foi reimplementado, mantendo a
atribuição registrada nesta avaliação.

Foram comparados os padrões de fetchers, limites, throttle, cache, checkpoint,
parser e observabilidade. O único padrão incorporado nesta mudança é
independente e de baixo risco: persistir o cache em um arquivo temporário no
mesmo diretório e publicá-lo com replace atômico. Um envelope corrompido agora é
tratado como cache miss, permitindo uma coleta nova sem interromper a operação.

Não foram incorporados stealth, rotação de proxy, fingerprinting, bypass de
CAPTCHA/WAF, automação de login ou qualquer técnica para contornar controles da
fonte.

## Evidência

- `src/nanojuris/discovery/cache.py`: gravação atômica e leitura tolerante a
  corrupção.
- `tests/test_provider_discovery.py`: regressão para envelope JSON corrompido.
- `pytest -q tests/test_provider_discovery.py tests/test_discovery_http.py`:
  33 testes aprovados.
