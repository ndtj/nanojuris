# Threat model

Only public read-only HTML is requested. No credentials, CAPTCHA solving,
proxy, or access-control bypass is used. The existing parser remains the
boundary for untrusted HTML and contract changes remain visible.
