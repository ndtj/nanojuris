# Desenho — protocolo de descoberta

## Ordem por tribunal

1. Consultar o diretório oficial do CNJ e o portal do próprio TRF.
2. Ler somente links publicados, documentação, exportações, RSS/sitemap,
   APIs documentadas e scripts públicos necessários à jornada normal.
3. Fazer GET da página inicial e, no máximo, uma consulta POST/GET com o termo
   neutro `responsabilidade civil`, limite de dois registros e timeout de oito
   segundos.
4. Se houver resultado, observar uma página seguinte apenas quando o cursor ou
   offset estiver documentado pela resposta.
5. Registrar campos, conteúdo, grau, documentos, ordenação e filtros.

## Classificação

```text
route_validated       fonte e contrato textual de segundo grau comprovados
route_candidate        superfície oficial alcançável, contrato incompleto
authoritative_empty    vazio explicitamente declarado pela fonte
blocked_external       desafio, autorização, WAF, 403/429 ou timeout
schema_invalid         resposta acessível sem contrato interpretável
not_jurisprudence      rota processual, catálogo ou metadado sem texto decisório
```

## Evidência

Salvar somente URL, método, status, content-type, tamanho, hash, latência,
campos canônicos e pequenos trechos sanitizados. Não persistir cookies,
tokens, ViewState, CAPTCHA, IP ou texto integral desnecessário.

## Segurança

Não resolver desafios, não gerar ou repetir tokens, não usar rotação de IP,
stealth, fingerprint spoofing, endpoint privado, downgrade TLS ou proxy não
autorizado. Uma página seguinte não autoriza contornar a proteção da página
anterior.
