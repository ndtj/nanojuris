# Research

- Live GET of `https://esaj.tjsp.jus.br/cjsg/consultaCompleta.do` returned the
  public form and an action containing a session id.
- A bounded public POST returned HTTP 200 but the form again, with CAPTCHA
  signals and no result container.
- The adjusted example reproduced this state as `access_control_required`.
- The current REA sweep records the same TJSP CJSG control behavior and does
  not authorize the control endpoint as an extraction route.
