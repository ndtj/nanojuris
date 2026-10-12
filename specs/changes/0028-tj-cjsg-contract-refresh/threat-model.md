# Threat model

| Asset | Threat | Mitigation |
| --- | --- | --- |
| Public source access | CAPTCHA/WAF bypass | typed access errors; no bypass code |
| Session state | cookie or token reuse | clean configured sessions |
| Source limits | excessive probing | bounded discovery, robots and delay |
| Search truth | blocked response treated as empty | explicit control/source statuses |
| Contract accuracy | unverified route claimed live | dated evidence and limitation notes |
