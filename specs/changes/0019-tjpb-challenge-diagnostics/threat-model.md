# Threat model

The response is untrusted public HTML. Marker matching is bounded and local;
the implementation never submits challenge data, stores tokens, or bypasses
WAF/CAPTCHA.
