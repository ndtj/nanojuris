# Design

The existing TJPA BFF parser uses the shared `normalize_date` helper and
stores both raw and normalized date values. Extraction status is complete only
when a summary or full text is present; otherwise it is partial. No transport
route or access behavior changes.
