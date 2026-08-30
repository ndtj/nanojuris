# Design

Token acquisition continues to use the existing public GET request. If the
CSRF token is absent, a small marker detector distinguishes known CAPTCHA/WAF
challenge pages from an otherwise changed HTML contract. Only the former is
classified as `AccessControlRequiredError`; no retry or bypass is introduced.
