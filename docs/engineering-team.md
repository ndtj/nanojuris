# Modelo da equipe de engenharia

A NanoJuris opera com uma equipe virtual especializada, organizada por
competências e aplicada em células temporárias por provider.

O núcleo é formado por Product/Domain, Architecture, Legal Data/Jurimetry,
Provider Discovery, Provider Engineering, Data Quality, Security/Privacy,
Platform/SRE, QA/Verification e Documentation/SDD.

Cada mudança segue:

```text
inspect → clarify → specify → design → plan → apply
        → verify → cross-review → human acceptance → release
```

O charter completo, competências, RACI, níveis de revisão e pacote de handoff
estão em [`specs/team/elite-engineering-team.md`](../specs/team/elite-engineering-team.md).

Os artefatos complementares são:

- [roster operacional](../specs/team/roster.md);
- [template de célula de provider](../specs/team/provider-cell-template.md);
- [checklist de revisão](../specs/team/review-checklist.md);
- [scorecard de qualidade](../specs/team/quality-scorecard.md).

Para discovery de providers, a equipe usa a camada
[`docs/provider-discovery.md`](provider-discovery.md), que produz evidências,
rotas candidatas, replay e drafts SDD. Nenhum resultado de discovery substitui
contrato, fixture, teste ou revisão de domínio.
