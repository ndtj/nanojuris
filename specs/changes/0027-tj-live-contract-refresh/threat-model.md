# Threat model

| Asset | Threat | Mitigation |
| --- | --- | --- |
| Public-source access | CAPTCHA/WAF/login bypass | explicit access errors; no token fabrication |
| Session state | Reuse of captured browser cookies | clean HTTP sessions; no persisted credentials |
| Source limits | Excessive probing | bounded discovery, robots and delay |
| Jurisprudence truth | Blocked response treated as empty | typed access/source errors and traces |
| Generated evidence | Claims exceed observation | dated report with limits and status separation |
