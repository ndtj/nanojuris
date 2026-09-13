# Design — governança de release

## Gates

    spec accepted
      -> implementation reviewed
      -> offline verification
      -> security/data review
      -> bounded live evidence when applicable
      -> compatibility report
      -> release candidate
      -> human authorization
      -> publish/deploy
      -> post-release observation

## Rollout

- feature flag por provider;
- shadow comparison quando houver adapter anterior;
- canary de interface;
- rollback para versão e capability anteriores;
- catálogo registra estado real, não intenção.

## Evidência de release

Commit, pacote, versão, artefato, hash, SBOM, testes, docs, riscos, aprovadores,
rollback e observação pós-release.
