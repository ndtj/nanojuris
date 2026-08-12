# GitHub Transfer Checklist

This checklist prepares the transfer of NanoJuris from `lucmolero` to the
`ndtj` organization while preserving authorship, technical leadership and
release continuity.

## Before Transfer

- [ ] Confirm that `@lucmolero` is an owner of `ndtj` and may create repositories.
- [ ] Confirm that `ndtj/nanojuris` does not already exist.
- [ ] Commit and push the final preparation changes to `lucmolero/nanojuris`.
- [ ] Verify that CI, CodeQL, Dependabot and release workflows are green.
- [ ] Record the current PyPI Trusted Publisher configuration.
- [ ] Save a local clone and verify the current default branch and tags.
- [ ] Confirm that no secrets, cookies, tokens or private HAR files are tracked.

## Transfer

1. Open the repository **Settings** page.
2. In **Danger Zone**, choose **Transfer**.
3. Select the `ndtj` organization.
4. Confirm the repository name and transfer.
5. Accept any organization invitation or confirmation requested by GitHub.

GitHub transfers issues, pull requests, wiki, stars, watchers and commit
information. The original owner is added as a collaborator, but ownership moves
to the organization.

## Immediately After Transfer

- [ ] Confirm the repository URL: `https://github.com/ndtj/nanojuris`.
- [ ] Confirm that `@lucmolero` has `Maintain` or `Admin` access as agreed.
- [ ] Confirm that `@lucmolero` remains listed in `.github/CODEOWNERS`.
- [ ] Update the local remote:

```bash
git remote set-url origin https://github.com/ndtj/nanojuris.git
git remote -v
```

- [ ] Update the PyPI Trusted Publisher owner/repository/environment if needed.
- [ ] Check GitHub Actions secrets, environments and permissions.
- [ ] Check CodeQL, Dependabot, branch rules and required reviews.
- [ ] Check releases, tags, packages and documentation links.
- [ ] Pin the transferred repository on Luciano Molero's GitHub profile.
- [ ] Add NanoJuris to the NDTJ organization profile or projects page.

## Public Attribution

The repository must continue to identify:

- Luciano Molero as principal maintainer and technical lead;
- NDTJ as institutional context and hosting organization;
- contributors through commit history and release notes;
- NanoJuris as an independent open source project, not an official product of
  a court or government body.

See [MAINTAINERS.md](../MAINTAINERS.md), [GOVERNANCE.md](../GOVERNANCE.md) and
[the NDTJ website](https://ndtj.com.br/).
