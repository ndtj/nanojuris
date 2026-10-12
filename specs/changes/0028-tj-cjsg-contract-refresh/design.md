# Design

## Evidence

The REA-backed sweep observed `GET /cjsg/consultaCompleta.do` for TJAC, TJAL,
TJMS and TJSP. TJCE was robots-disallowed in the same bounded run; TJAM and
TJCE therefore remain unverified for live route discovery.

## Decision

Add the relative route `GET /consultaCompleta.do` to the four observed
capability declarations. TJCE inherits the family metadata, so its dossier
explicitly states that the inherited route is not live-confirmed. TJAM is left
unchanged.

## Safety

Only declared public GET routes are discovered. No POST is submitted without a
provider contract and no response containing CAPTCHA or another control is
converted into a result.

## Compatibility

This is additive capability metadata. Search payloads, pagination, document
requests and access-control behavior are unchanged. Catalogs are regenerated.
