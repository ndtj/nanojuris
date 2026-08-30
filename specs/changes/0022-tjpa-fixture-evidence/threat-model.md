# Threat model

- Network dependence: mitigated by offline fixture parsing.
- Personal-data retention: mitigated by synthetic identifiers and text.
- Contract drift: detected by the versioned parser assertions.
- False capability claims: mitigated by leaving detail routes explicitly
  unimplemented and documenting the fixture limitation.
