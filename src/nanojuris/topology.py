"""Versioned topology and coverage claims for Brazilian jurisprudence.

The topology is deliberately independent from provider availability.  A court
or collection can be known while its technical surface is unavailable, and an
unattributed provider is represented explicitly instead of being silently
counted as national coverage.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any, Literal

from nanojuris.brazil import COURTS, CourtInfo
from nanojuris.catalog import load_provider_catalog

TopologyStatus = Literal[
    "unknown",
    "gap",
    "candidate",
    "implemented",
    "blocked",
    "retired",
]
CoverageDimension = Literal[
    "collection",
    "authority",
    "branch",
    "surface",
    "provider",
]

_TOPOLOGY_STATUSES = frozenset({"unknown", "gap", "candidate", "implemented", "blocked", "retired"})


class TopologyValidationError(ValueError):
    """Raised when a topology violates an invariant from SDD 0036."""


def _iso_date(value: str) -> str:
    """Validate and return an ISO calendar date."""

    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"data invalida: {value!r}") from exc
    return parsed.isoformat()


@dataclass(frozen=True, slots=True)
class TopologyCollection:
    """A legal collection, independent of a provider implementation."""

    collection_id: str
    authority_id: str
    branch: str
    degree: str
    document_types: tuple[str, ...] = ()
    period_start: str | None = None
    period_end: str | None = None
    surface_ids: tuple[str, ...] = ()
    provider_ids: tuple[str, ...] = ()
    status: TopologyStatus = "unknown"
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.collection_id.strip():
            raise ValueError("collection_id nao pode ser vazio")
        if not self.authority_id.strip():
            raise ValueError("authority_id nao pode ser vazio")
        if not self.branch.strip() or not self.degree.strip():
            raise ValueError("branch e degree sao obrigatorios; use unknown quando necessario")
        if self.status not in _TOPOLOGY_STATUSES:
            raise ValueError(f"status de topologia invalido: {self.status!r}")
        if self.period_start:
            _iso_date(self.period_start)
        if self.period_end:
            _iso_date(self.period_end)
        if self.period_start and self.period_end and self.period_start > self.period_end:
            raise ValueError("period_start nao pode ser posterior a period_end")
        for field_name in ("document_types", "surface_ids", "provider_ids", "evidence_ids"):
            values = getattr(self, field_name)
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} nao pode conter duplicidades")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        payload = asdict(self)
        for field_name in ("document_types", "surface_ids", "provider_ids", "evidence_ids"):
            payload[field_name] = list(payload[field_name])
        return payload


@dataclass(frozen=True, slots=True)
class CoverageEpoch:
    """Finite, comparable snapshot of the topology used by a claim."""

    epoch_id: str
    topology_version: str
    cutoff_date: str

    def __post_init__(self) -> None:
        if not self.epoch_id.strip() or not self.topology_version.strip():
            raise ValueError("epoch_id e topology_version sao obrigatorios")
        _iso_date(self.cutoff_date)

    @classmethod
    def create(cls, topology_version: str, cutoff_date: str) -> CoverageEpoch:
        """Create a stable epoch ID from version and cutoff date."""

        normalized_date = _iso_date(cutoff_date)
        return cls(
            epoch_id=f"{topology_version}@{normalized_date}",
            topology_version=topology_version,
            cutoff_date=normalized_date,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CoverageClaim:
    """A measured numerator/denominator for one explicit dimension."""

    epoch_id: str
    dimension: CoverageDimension
    numerator: int
    denominator: int
    measured_at: str
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.epoch_id.strip():
            raise ValueError("epoch_id nao pode ser vazio")
        if self.dimension not in {"collection", "authority", "branch", "surface", "provider"}:
            raise ValueError(f"dimensao de cobertura invalida: {self.dimension!r}")
        if self.numerator < 0 or self.denominator <= 0:
            raise ValueError("numerator deve ser >= 0 e denominator deve ser > 0")
        if self.numerator > self.denominator:
            raise ValueError("numerator nao pode exceder denominator")
        _iso_date(self.measured_at)

    @property
    def ratio(self) -> float:
        """Return the measured ratio without presenting it as national completeness."""

        return self.numerator / self.denominator

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["ratio"] = self.ratio
        return payload


@dataclass(frozen=True, slots=True)
class CoverageGap:
    """A collection that is not currently backed by an implemented provider.

    A gap is deliberately emitted at collection granularity.  This keeps an
    authority with multiple degrees or surfaces from being counted as one
    opaque failure and makes the remediation unit actionable.
    """

    collection_id: str
    authority_id: str
    branch: str
    status: TopologyStatus
    reason: str

    def __post_init__(self) -> None:
        if not self.collection_id.strip() or not self.authority_id.strip():
            raise ValueError("collection_id e authority_id sao obrigatorios")
        if not self.branch.strip():
            raise ValueError("branch nao pode ser vazio")
        if self.status not in _TOPOLOGY_STATUSES:
            raise ValueError(f"status de topologia invalido: {self.status!r}")
        if self.status == "implemented":
            raise ValueError("uma collection implementada nao e uma lacuna")
        if not self.reason.strip():
            raise ValueError("reason nao pode ser vazio")

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CoverageProjection:
    """Generated claims, gaps and finite history for one coverage epoch."""

    epoch: CoverageEpoch
    claims: tuple[CoverageClaim, ...]
    gaps: tuple[CoverageGap, ...]
    history: tuple[CoverageEpoch, ...]
    summary: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate epoch references and uniqueness of generated dimensions."""

        if not self.claims:
            raise TopologyValidationError("a projecao precisa de pelo menos um claim")
        claim_dimensions = [claim.dimension for claim in self.claims]
        if len(claim_dimensions) != len(set(claim_dimensions)):
            raise TopologyValidationError("dimension duplicada nos claims")
        if any(claim.epoch_id != self.epoch.epoch_id for claim in self.claims):
            raise TopologyValidationError("claim referencia epoch diferente da projecao")
        history_ids = [item.epoch_id for item in self.history]
        if len(history_ids) != len(set(history_ids)):
            raise TopologyValidationError("epoch duplicada no historico")
        if self.epoch.epoch_id not in history_ids:
            raise TopologyValidationError("epoch atual ausente do historico")
        gap_ids = [gap.collection_id for gap in self.gaps]
        if len(gap_ids) != len(set(gap_ids)):
            raise TopologyValidationError("collection duplicada nas lacunas")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": "national-jurisprudence-coverage-v1",
            "epoch": self.epoch.to_dict(),
            "claims": [claim.to_dict() for claim in self.claims],
            "gaps": [gap.to_dict() for gap in self.gaps],
            "history": [item.to_dict() for item in self.history],
            "summary": dict(self.summary),
        }


@dataclass(frozen=True, slots=True)
class NationalTopology:
    """Machine-readable topology with explicit validation and epochs."""

    schema_version: str
    topology_version: str
    collections: tuple[TopologyCollection, ...] = ()
    epochs: tuple[CoverageEpoch, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate IDs, bindings, and finite epoch history."""

        if not self.schema_version.strip() or not self.topology_version.strip():
            raise TopologyValidationError("schema_version e topology_version sao obrigatorios")
        collection_ids = [item.collection_id for item in self.collections]
        if len(collection_ids) != len(set(collection_ids)):
            raise TopologyValidationError("collection_id duplicado")
        epoch_ids = [item.epoch_id for item in self.epochs]
        if len(epoch_ids) != len(set(epoch_ids)):
            raise TopologyValidationError("epoch_id duplicado")
        for epoch in self.epochs:
            if epoch.topology_version != self.topology_version:
                raise TopologyValidationError(
                    f"epoch {epoch.epoch_id!r} pertence a outra topologia"
                )
        all_surfaces: list[str] = []
        all_providers: list[str] = []
        for collection in self.collections:
            all_surfaces.extend(collection.surface_ids)
            all_providers.extend(collection.provider_ids)
        if any(not value.strip() for value in all_surfaces + all_providers):
            raise TopologyValidationError("bindings nao podem conter IDs vazios")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "topology_version": self.topology_version,
            "collections": [item.to_dict() for item in self.collections],
            "epochs": [item.to_dict() for item in self.epochs],
            "metadata": dict(self.metadata),
        }


def topology_from_courts(
    courts: Iterable[CourtInfo] = COURTS,
    *,
    topology_version: str = "2026-09-01",
    cutoff_date: str | None = None,
    provider_ids: Iterable[str] = (),
) -> NationalTopology:
    """Build a conservative topology from the checked-in court catalog.

    Providers absent from the court catalog are retained in explicit
    ``unknown`` collections.  This makes reconciliation visible while
    preventing an inferred authority or branch from becoming a coverage claim.
    """

    court_rows = tuple(courts)
    known_provider_ids = {
        provider for court in court_rows for provider in court.providers if provider
    }
    catalog_provider_ids = {str(item) for item in provider_ids if str(item).strip()}
    collections: list[TopologyCollection] = []
    for court in court_rows:
        status: TopologyStatus = (
            "implemented" if court.provider_status == "implemented" else "candidate"
        )
        collection_id = f"collection:{court.code.casefold()}:jurisprudence"
        surface_id = f"surface:{court.code.casefold()}:official"
        collections.append(
            TopologyCollection(
                collection_id=collection_id,
                authority_id=f"authority:{court.code.casefold()}",
                branch=court.branch,
                degree="unknown",
                document_types=("jurisprudence",),
                surface_ids=(surface_id,),
                provider_ids=tuple(court.providers),
                status=status,
                evidence_ids=(f"court-catalog:{court.code.casefold()}",),
            )
        )

    unbound = sorted(catalog_provider_ids - known_provider_ids)
    for source_id in unbound:
        collections.append(
            TopologyCollection(
                collection_id=f"collection:unattributed:{source_id}",
                authority_id="authority:unknown",
                branch="unknown",
                degree="unknown",
                document_types=("unknown",),
                provider_ids=(source_id,),
                status="unknown",
                evidence_ids=(f"provider-catalog:{source_id}",),
            )
        )

    epoch_date = cutoff_date or topology_version
    epoch = CoverageEpoch.create(topology_version, epoch_date)
    topology = NationalTopology(
        schema_version="national-jurisprudence-topology-v1",
        topology_version=topology_version,
        collections=tuple(collections),
        epochs=(epoch,),
        metadata={
            "source": "nanojuris.brazil.COURTS",
            "authority_count": len(court_rows),
            "authority_register_evidence": "docs/topology/cnj-tribunal-register-20260901.json",
            "network_access": "not_used",
        },
    )
    topology.validate()
    return topology


def packaged_topology(*, topology_version: str = "2026-09-01") -> NationalTopology:
    """Build the current offline topology and reconcile packaged providers."""

    catalog_ids = (
        str(entry.get("source_id", ""))
        for entry in load_provider_catalog().get("entries", [])
        if entry.get("source_id")
    )
    return topology_from_courts(
        topology_version=topology_version,
        provider_ids=catalog_ids,
    )


def project_coverage(
    topology: NationalTopology,
    *,
    measured_at: str | None = None,
) -> CoverageProjection:
    """Generate deterministic claims and gaps from a validated topology.

    Only collections with a known authority and a jurisprudence document type
    participate in the national denominators.  Providers that are not
    reconciled to an authority remain visible in ``gaps`` and in the summary,
    but cannot inflate an authority or branch claim.
    """

    topology.validate()
    if not topology.epochs:
        raise TopologyValidationError("a topologia precisa de uma coverage epoch")
    epoch = max(topology.epochs, key=lambda item: (item.cutoff_date, item.epoch_id))
    claim_date = measured_at or epoch.cutoff_date
    _iso_date(claim_date)

    known_collections = tuple(
        collection
        for collection in topology.collections
        if collection.authority_id != "authority:unknown"
        and "jurisprudence" in collection.document_types
    )
    implemented = tuple(item for item in known_collections if item.status == "implemented")

    def unique(values: Iterable[str]) -> tuple[str, ...]:
        return tuple(sorted({value for value in values if value.strip()}))

    authorities = unique(item.authority_id for item in known_collections)
    branches = unique(item.branch for item in known_collections if item.branch != "unknown")
    surfaces = unique(surface for item in known_collections for surface in item.surface_ids)
    # Keep every provider binding in this denominator, including source IDs
    # still held in an ``authority:unknown`` collection.  Otherwise a partial
    # reconciliation could manufacture a 100% provider claim.
    providers = unique(provider for item in topology.collections for provider in item.provider_ids)

    def implemented_for(field: str, value: str) -> bool:
        for item in implemented:
            if field == "authority" and item.authority_id == value:
                return True
            if field == "branch" and item.branch == value:
                return True
            if field == "surface" and value in item.surface_ids:
                return True
            if field == "provider" and value in item.provider_ids:
                return True
        return False

    counts: dict[CoverageDimension, tuple[int, int]] = {
        "collection": (len(implemented), len(known_collections)),
        "authority": (
            sum(implemented_for("authority", value) for value in authorities),
            len(authorities),
        ),
        "branch": (
            sum(implemented_for("branch", value) for value in branches),
            len(branches),
        ),
        "surface": (
            sum(implemented_for("surface", value) for value in surfaces),
            len(surfaces),
        ),
        "provider": (
            sum(implemented_for("provider", value) for value in providers),
            len(providers),
        ),
    }
    claims = tuple(
        CoverageClaim(
            epoch_id=epoch.epoch_id,
            dimension=dimension,
            numerator=numerator,
            denominator=denominator,
            measured_at=claim_date,
            notes=(
                "Denominador institucional da topologia; nao representa cobertura "
                "temporal integral nem disponibilidade live."
            ),
        )
        for dimension, (numerator, denominator) in counts.items()
        if denominator > 0
    )

    reason_by_status: dict[TopologyStatus, str] = {
        "unknown": "provider_or_collection_not_reconciled_to_authority",
        "gap": "jurisprudence_collection_without_provider",
        "candidate": "authority_cataloged_without_implemented_provider",
        "blocked": "surface_blocked_or_contract_incomplete",
        "retired": "binding_retired_from_current_topology",
        "implemented": "",
    }
    gaps = tuple(
        CoverageGap(
            collection_id=item.collection_id,
            authority_id=item.authority_id,
            branch=item.branch,
            status=item.status,
            reason=reason_by_status[item.status],
        )
        for item in topology.collections
        if item.status != "implemented"
    )
    status_counts = {
        status: sum(item.status == status for item in topology.collections)
        for status in sorted(_TOPOLOGY_STATUSES)
    }
    gaps_by_branch = {
        branch: sum(gap.branch == branch for gap in gaps)
        for branch in sorted({gap.branch for gap in gaps})
    }
    projection = CoverageProjection(
        epoch=epoch,
        claims=claims,
        gaps=gaps,
        history=tuple(sorted(topology.epochs, key=lambda item: (item.cutoff_date, item.epoch_id))),
        summary={
            "source": "nanojuris.topology.project_coverage",
            "network_access": "not_used",
            "known_collection_count": len(known_collections),
            "unreconciled_collection_count": len(topology.collections) - len(known_collections),
            "unreconciled_provider_count": len(
                {
                    provider
                    for item in topology.collections
                    if item.authority_id == "authority:unknown"
                    for provider in item.provider_ids
                }
            ),
            "status_counts": status_counts,
            "gaps_by_branch": gaps_by_branch,
            "scope_note": (
                "Claims medem bindings institucionais implementados na epoca; "
                "nao afirmam que cada tribunal ou periodo possui acervo integral."
            ),
        },
    )
    projection.validate()
    return projection


__all__ = [
    "CoverageClaim",
    "CoverageGap",
    "CoverageProjection",
    "CoverageDimension",
    "CoverageEpoch",
    "NationalTopology",
    "TopologyCollection",
    "TopologyStatus",
    "TopologyValidationError",
    "packaged_topology",
    "project_coverage",
    "topology_from_courts",
]
