# Design

## Runtime flow

```text
GET consultaCompleta.do
  -> collect current form fields and action
POST resultadoCompleta.do (same ephemeral session)
  -> result fragment: parse
  -> control/form response: stop with explicit state
  -> safe intermediate response: GET trocaDePagina.do page 1
```

The standalone example shares the public contract but not the provider's
internal session. It is intentionally conservative when the source returns
HTTP 200 with a CAPTCHA page, because status code alone is not a success signal.

## Security

The control endpoint is documented but never invoked. No token, cookie or
browser state is persisted. The form action must resolve to the official TJSP
host before submission.

## Compatibility

The example is additive and does not alter provider behavior. It uses only
`requests` and `beautifulsoup4`, matching the pasted user script's dependencies.
