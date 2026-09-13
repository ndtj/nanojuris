# Design - Paridade de transporte sem bypass

## Estratégia

1. `TjceTlsAdapter` usa contexto urllib3 com `DEFAULT:@SECLEVEL=1`, montado
   apenas na sessão do TJCE. A opção `verify_ssl` continua sendo aplicada pela
   configuração compartilhada.
2. `TjpeJurisprudenciaProvider` mantém REST como contrato estável. O parâmetro
   `transport` aceita `rest`, `jsf` ou `auto`; `auto` tenta JSF somente quando a
   chamada REST falha no transporte antes de receber uma resposta HTTP.
3. O adaptador JSF executa a sequência pública GET consulta, POST consulta,
   POST escolha quando necessário e POST AJAX de paginação. ViewState, IDs e
   cookies ficam exclusivamente na sessão em memória.
4. TJTO/TJSP usam uma função local de retry com no máximo duas repetições para
   429/500/502/503/504 e exceções de conexão. 403 e sinais de controle são
   classificados imediatamente após a política bounded.

## Dados e proveniência

Cada resposta recebe hash SHA-256, status HTTP, URL final, tipo de conteúdo e
bytes. O trace JSF inclui `transport="jsf"` e, em fallback, o motivo resumido
(`rest_transport_failure`) sem registrar URL com credenciais ou valores de
ViewState.

## Compatibilidade

O construtor REST existente continua válido. O modo padrão permanece `rest`
para não alterar latência ou semântica de clientes existentes; consumidores
que desejam resiliência podem escolher `transport="auto"` explicitamente.
