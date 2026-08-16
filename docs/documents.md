# Documentos e inteiro teor

O NanoJuris separa quatro coisas que nao devem ser confundidas:

1. `summary` ou `ementa`: texto apresentado na busca;
2. `full_text`: texto integral embutido no resultado, quando a fonte o fornece;
3. `document_url`: endereco oficial observado, ainda nao prova de carregamento;
4. `CanonicalDocument`: documento efetivamente recuperado e auditado.

## Contrato `CanonicalDocument`

| Campo | Significado |
| --- | --- |
| `id` | identidade estavel do documento no provider |
| `source` | provider que recuperou o documento |
| `document_type` | acordao, decisao, informativo ou tipo declarado pela fonte |
| `content_type` | tipo efetivo detectado ou informado pela resposta |
| `text` | texto extraido para leitura e busca |
| `raw_bytes` | bytes originais preservados no objeto Python |
| `url` | URL final oficial observada |
| `sha256` | hash dos bytes originais, antes da extração |
| `byte_size` | tamanho dos bytes originais |
| `access_status` | estado de acesso observado |
| `extraction_status` | resultado da extração de texto |
| `source_trace` | endpoint, consulta, HTTP, tempo e proveniencia |
| `extraction_trace` | parser, versao, transformacoes e avisos |
| `raw_metadata` | campos especificos da fonte preservados |

Por padrao, `to_dict()` retorna texto e metadados, mas nao transforma bytes
binarios em base64. Isso evita respostas gigantes no Studio, CLI e MCP. O
objeto Python continua contendo `raw_bytes`; consumidores que realmente
precisarem transportar os bytes podem usar `to_dict(include_raw_bytes=True)`.

## Estados

Um provider deve distinguir:

- `loaded`: documento recuperado e texto extraido;
- `document_available`: URL observada, mas documento ainda nao carregado;
- `partial`: resposta incompleta ou texto insuficiente;
- `empty`: resposta acessivel sem texto extraivel;
- `access_control_required`: CAPTCHA, WAF, login ou outro controle observado;
- `source_unavailable`: timeout, TLS ou indisponibilidade da fonte;
- `contract_changed`: resposta incompatível com o parser;
- `unsupported_format`: bytes preservados, formato ainda nao suportado.

Nenhum desses estados deve ser convertido em resultado vazio. O documento
bruto e os metadados de transporte devem ser preservados para auditoria.

## Uso

```python
document = client.get_document(document_id, source="stj_scon")

print(document.text)
print(document.content_type, document.byte_size)
print(document.sha256)
print(document.extraction_status)
```

Para agentes, a ordem recomendada e: carregar o documento, verificar
`access_status` e `extraction_status`, citar `url` e `sha256`, e somente entao
resumir ou produzir analise. Uma URL isolada nunca deve ser apresentada como
inteiro teor carregado.

## Verificacao dos providers

O dossie de cada provider informa se o documento e HTML, PDF, JSON ou texto,
qual rota foi reproduzida, quais fixtures existem e quando houve a ultima
validacao live. Consulte `docs/providers/<source_id>/README.md` e o catalogo
machine-readable antes de assumir que duas fontes possuem o mesmo contrato.
