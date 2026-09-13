"""National jurisprudence coverage matrix by collection and legal degree.

The matrix is deliberately more specific than the historical authority catalog:
``CJPG`` and ``CJSG`` are source collections for state courts, while other
branches keep their native surfaces (eproc, PJe, SJUR, and so on).  A provider
that can return mixed document types never satisfies a CJPG/CJSG row without a
separate degree-specific contract.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from nanojuris.brazil import COURTS
from nanojuris.catalog import load_provider_catalog

CoverageBranch = Literal[
    "constitutional",
    "superior",
    "federal",
    "state",
    "labor",
    "electoral",
    "military",
    "national_council",
]
CoverageDegree = Literal["first", "second", "recursal", "superior", "mixed", "unknown"]
CoverageStatus = Literal[
    "implemented",
    "candidate",
    "pending_contract",
    "blocked_access",
    "blocked_transport",
    "source_unavailable",
    "out_of_scope",
]
CoverageScope = Literal["tribunal", "aggregator", "judicial_unit_gap"]

_COLLECTIONS = frozenset(
    {
        "CJPG",
        "CJSG",
        "EPROC",
        "PJE",
        "SJUR",
        "PORTAL",
        "JURISPRUDENCIA",
        "PRECEDENT",
        "INFORMATIVO",
        "TEMAS",
        "CATALOG",
        "AGGREGATE",
        "TURMA_RECURSAL",
        # Curated, official second-degree bulletins published by an
        # institutional repository.  This is intentionally distinct from
        # the TJMG CJSG search surface: it is an aggregator collection and
        # must not inflate the required 27-court CJSG denominator.
        "CJSG_EJEF_BOLETIM",
    }
)
_DEGREES = frozenset({"first", "second", "recursal", "superior", "mixed", "unknown"})
_STATUSES = frozenset(
    {
        "implemented",
        "candidate",
        "pending_contract",
        "blocked_access",
        "blocked_transport",
        "source_unavailable",
        "out_of_scope",
    }
)
_BRANCHES = frozenset(
    {
        "constitutional",
        "superior",
        "federal",
        "state",
        "labor",
        "electoral",
        "military",
        "national_council",
    }
)


class CoverageMatrixValidationError(ValueError):
    """Raised when a coverage row violates a semantic invariant."""


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")


@dataclass(frozen=True, slots=True)
class CoverageSurface:
    """One expected or observed collection surface in the national matrix."""

    authority: str
    branch: str
    degree: str
    collection: str
    status: str
    provider: str | None = None
    queryable: bool = False
    required: bool = False
    scope: str = "tribunal"
    document_types: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    notes: str = ""

    @property
    def surface_id(self) -> str:
        provider = _slug(self.provider or "gap")
        return ":".join(
            ("surface", _slug(self.authority), _slug(self.collection), _slug(self.degree), provider)
        )

    def __post_init__(self) -> None:
        if not self.authority.strip():
            raise CoverageMatrixValidationError("authority nao pode ser vazia")
        if self.branch not in _BRANCHES:
            raise CoverageMatrixValidationError(f"branch invalido: {self.branch!r}")
        if self.degree not in _DEGREES:
            raise CoverageMatrixValidationError(f"degree invalido: {self.degree!r}")
        if self.collection not in _COLLECTIONS:
            raise CoverageMatrixValidationError(f"collection invalida: {self.collection!r}")
        if self.status not in _STATUSES:
            raise CoverageMatrixValidationError(f"status invalido: {self.status!r}")
        if self.scope not in {"tribunal", "aggregator", "judicial_unit_gap"}:
            raise CoverageMatrixValidationError(f"scope invalido: {self.scope!r}")
        if self.collection == "CJPG" and self.degree != "first":
            raise CoverageMatrixValidationError("CJPG exige degree=first")
        if self.collection == "CJSG" and self.degree != "second":
            raise CoverageMatrixValidationError("CJSG exige degree=second")
        if self.status == "implemented" and not self.provider:
            raise CoverageMatrixValidationError("implemented exige provider")
        if self.status == "implemented" and not self.queryable:
            raise CoverageMatrixValidationError("implemented exige queryable=true")
        if self.queryable and self.status != "implemented":
            raise CoverageMatrixValidationError("queryable so pode ser true em implemented")
        if len(set(self.document_types)) != len(self.document_types):
            raise CoverageMatrixValidationError("document_types nao pode conter duplicidades")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise CoverageMatrixValidationError("evidence_ids nao pode conter duplicidades")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["surface_id"] = self.surface_id
        payload["document_types"] = list(self.document_types)
        payload["evidence_ids"] = list(self.evidence_ids)
        return payload


@dataclass(frozen=True, slots=True)
class CoverageMatrix:
    """Validated national matrix and deterministic gap projection."""

    version: str
    generated_at: str
    surfaces: tuple[CoverageSurface, ...]
    source_artifacts: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.version.strip() or not self.generated_at.strip():
            raise CoverageMatrixValidationError("version e generated_at sao obrigatorios")
        ids = [surface.surface_id for surface in self.surfaces]
        if len(ids) != len(set(ids)):
            raise CoverageMatrixValidationError("surface_id duplicado")
        keys = [
            (surface.authority, surface.collection, surface.degree, surface.provider)
            for surface in self.surfaces
        ]
        if len(keys) != len(set(keys)):
            raise CoverageMatrixValidationError("chave autoridade/colecao/grau/provider duplicada")

    def filtered(
        self,
        *,
        authority: str | None = None,
        collection: str | None = None,
        degree: str | None = None,
        branch: str | None = None,
        status: str | None = None,
    ) -> tuple[CoverageSurface, ...]:
        return tuple(
            surface
            for surface in self.surfaces
            if (authority is None or surface.authority == authority)
            and (collection is None or surface.collection == collection)
            and (degree is None or surface.degree == degree)
            and (branch is None or surface.branch == branch)
            and (status is None or surface.status == status)
        )

    @property
    def gaps(self) -> tuple[CoverageSurface, ...]:
        return tuple(
            surface
            for surface in self.surfaces
            if surface.required and surface.status != "implemented"
        )

    def summary(self) -> dict[str, Any]:
        required = tuple(surface for surface in self.surfaces if surface.required)

        def counts(values: Iterable[str]) -> dict[str, int]:
            return dict(sorted(Counter(values).items()))

        by_collection: dict[str, dict[str, int | float]] = {}
        for collection in sorted({surface.collection for surface in required}):
            rows = tuple(surface for surface in required if surface.collection == collection)
            implemented = sum(surface.status == "implemented" for surface in rows)
            by_collection[collection] = {
                "implemented": implemented,
                "expected": len(rows),
                "ratio": implemented / len(rows) if rows else 0.0,
            }
        return {
            "surface_count": len(self.surfaces),
            "required_surface_count": len(required),
            "gap_count": len(self.gaps),
            "by_collection": by_collection,
            "by_degree": counts(surface.degree for surface in required),
            "by_branch": counts(surface.branch for surface in required),
            "by_status": counts(surface.status for surface in self.surfaces),
            "queryable_count": sum(surface.queryable for surface in self.surfaces),
            "scope_note": (
                "Ratios medem linhas esperadas mapeadas; nao afirmam acervo temporal integral "
                "nem disponibilidade live permanente."
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": "national-degree-coverage-matrix-v1",
            "version": self.version,
            "generated_at": self.generated_at,
            "source_artifacts": list(self.source_artifacts),
            "summary": self.summary(),
            "surfaces": [surface.to_dict() for surface in self.surfaces],
            "gaps": [surface.to_dict() for surface in self.gaps],
        }


@dataclass(frozen=True, slots=True)
class _Declaration:
    authority: str
    branch: str
    provider: str
    degree: str
    collection: str
    document_types: tuple[str, ...] = ()
    notes: str = ""
    required: bool = False
    scope: str = "tribunal"


_DIRECT_CJPG = {
    # TJAP's public Banco de Sentenças is a distinct first-degree collection;
    # Tucujuris/CJSG remains separately access-controlled.
    "TJAP": "tjap_banco_sentencas",
    "TJAC": "tjac_banco_sentencas",
    # ESMAL publishes a bounded first-instance sentence bank with explicit
    # CJPG scope and observed official PDF links. It remains opt-in in runtime
    # despite being a valid matrix surface.
    "TJAL": "tjal_esmal_banco_sentencas",
    "TJES": "tjes_cjpg",
    "TJSP": "tjsp_cjpg",
    # TJRO exposes a public PJEPG window on the same JURIS endpoint.  The
    # ``grau_jurisdicao=[1]`` filter and PJEPG source marker are independently
    # validated, including a bounded second page, so it is a distinct CJPG
    # binding rather than an inference from the mixed provider.
    "TJRO": "tjro_jurisprudencia",
    # PROJUDI exposes a separate first-degree instance (Id_Instancia=16).
    # Cards are accepted only when their judicial-unit marker proves CJPG.
    "TJGO": "tjgo_projudi_jurisprudencia",
    # TJMS exposes the public e-SAJ CJPG form with inline first-degree text;
    # its binding is separate from the existing CJSG provider.
    "TJMS": "tjms_cjpg",
    # TJTO's official Jurisprudencia 4.0 route exposes an explicit
    # tip_criterio_inst=1 first-degree contract alongside its CJSG scope.
    "TJTO": "tjto_jurisprudencia",
}
_DIRECT_CJSG = {
    "TJAC": "tjac_cjsg",
    "TJAL": "tjal_cjsg",
    "TJAM": "tjam_cjsg",
    "TJBA": "tjba_graphql",
    "TJCE": "tjce_cjsg",
    "TJDFT": "tjdf_juris",
    "TJGO": "tjgo_projudi_jurisprudencia",
    "TJMS": "tjms_cjsg",
    "TJMT": "tjmt_jurisprudencia_api",
    "TJPA": "tjpa_jurisprudencia_bff",
    "TJPB": "tjpb_pje_jurisprudencia",
    # TJPE's public REST/JSF surface now has an explicit second-degree
    # contract and a bounded live result; keep it distinct from generic
    # jurisprudence metadata.
    "TJPE": "tjpe_jurisprudencia",
    "TJPI": "tjpi_juspi",
    "TJPR": "tjpr_jurisprudencia",
    "TJRS": "tjrs_solr",
    "TJRJ": "tjrj_eproc_jurisprudencia",
    "TJSC": "tjsc_eproc_jurisprudencia",
    "TJTO": "tjto_jurisprudencia",
    # TJMG's official Digital Library exposes searchable individual appellate
    # records and original PDFs through the public DSpace API.  The legacy
    # form remains CAPTCHA-protected; this binding is the independently
    # validated public CJSG surface.
    "TJMG": "tjmg_dspace_jurisprudencia",
    "TJES": "tjes_jurisprudencia",
    "TJSP": "tjsp_cjsg",
    # TJRN's public endpoint is a unified JURISPRUDENCIA route, but bounded
    # live checks show that its returned records are appellate (degree=second)
    # and expose stable canonical fields.  Treat this as an explicit CJSG
    # binding; the first-degree surface remains separate and unproven.
    "TJRN": "tjrn_jurisprudencia",
    # TJRR's public PrimeFaces form identifies the result collection as CJSG
    # and emits degree/instance=second in every bounded live sample.
    "TJRR": "tjrr_juris",
    # The judicial search form is Turnstile-protected, but the official
    # Boletim Jurídico publishes a separate public appellate ementa surface.
    "TJSE": "tjse_boletim_jurisprudencia",
}
# Liame is a precedent/contextual collection. It must never be selected as
# the TJRO general second-degree jurisprudence surface merely because its
# declaration appears first. The textual provider is selected only after its
# explicit degree filter is proven by the live contract.
_CJSG_PROVIDER_OVERRIDES = {"TJRO": "tjro_jurisprudencia"}
_ELECTORAL_REGIONAL_CODES = tuple(
    sorted(court.code for court in COURTS if court.branch == "electoral" and court.code != "TSE")
)
_STATE_EQUIVALENTS: tuple[_Declaration, ...] = (
    _Declaration(
        "TJMG",
        "state",
        "tjmg_ejef_boletim_jurisprudencia",
        "second",
        "CJSG_EJEF_BOLETIM",
        ("acordao", "ementa"),
        "colecao curada de boletins; nao substitui a busca integral do TJMG",
        required=False,
        scope="aggregator",
    ),
    _Declaration(
        "TJBA",
        "state",
        "tjba_graphql",
        "second",
        "JURISPRUDENCIA",
        ("acordao", "decisao_monocratica"),
    ),
    _Declaration(
        "TJCE", "state", "tjce_sjuris", "second", "SJUR", ("acordao", "decisao_monocratica")
    ),
    _Declaration(
        "TJES",
        "state",
        "tjes_turma_recursal",
        "recursal",
        "TURMA_RECURSAL",
        ("acordao", "recurso_inominado"),
        "collection publica separada de CJPG e CJSG",
    ),
    _Declaration("TJDFT", "state", "tjdf_juris", "second", "PORTAL", ("acordao", "turma_recursal")),
    _Declaration(
        "TJGO",
        "state",
        "tjgo_projudi_jurisprudencia",
        "mixed",
        "PJE",
        ("decisao", "sentenca", "acordao"),
    ),
    _Declaration(
        "TJMA",
        "state",
        "tjma_jurisconsult",
        "unknown",
        "CATALOG",
        ("acordao", "sentenca"),
        "catalogo de metadados; sem busca decisoria promovida",
    ),
    _Declaration(
        "TJMT",
        "state",
        "tjmt_jurisprudencia_api",
        "second",
        "JURISPRUDENCIA",
        ("acordao", "decisao_monocratica"),
    ),
    _Declaration(
        "TJPA",
        "state",
        "tjpa_jurisprudencia_bff",
        "second",
        "JURISPRUDENCIA",
        ("acordao", "decisao_monocratica"),
    ),
    _Declaration(
        "TJPB", "state", "tjpb_pje_jurisprudencia", "second", "PJE", ("acordao", "decisao")
    ),
    _Declaration(
        "TJPE", "state", "tjpe_jurisprudencia", "second", "JURISPRUDENCIA", ("acordao", "decisao")
    ),
    _Declaration("TJPI", "state", "tjpi_juspi", "second", "PORTAL", ("acordao", "sumula")),
    _Declaration(
        "TJPR", "state", "tjpr_jurisprudencia", "second", "JURISPRUDENCIA", ("acordao", "decisao")
    ),
    _Declaration(
        "TJRJ", "state", "tjrj_eproc_jurisprudencia", "mixed", "EPROC", ("acordao", "sentenca")
    ),
    _Declaration("TJRO", "state", "tjro_liame", "second", "PRECEDENT", ("irdr", "iac")),
    _Declaration(
        "TJRO",
        "state",
        "tjro_jurisprudencia",
        "mixed",
        "JURISPRUDENCIA",
        ("acordao", "sentenca"),
        "busca textual geral; nao substitui bindings especificos CJPG/CJSG",
    ),
    _Declaration(
        "TJRR", "state", "tjrr_juris", "second", "PORTAL", ("acordao", "decisao_monocratica")
    ),
    _Declaration("TJRS", "state", "tjrs_solr", "second", "PORTAL", ("acordao", "decisao")),
    _Declaration(
        "TJSC", "state", "tjsc_eproc_jurisprudencia", "mixed", "EPROC", ("acordao", "sentenca")
    ),
    _Declaration(
        "TJSP", "state", "tjsp_eproc_jurisprudencia", "mixed", "EPROC", ("sentenca", "acordao")
    ),
    _Declaration(
        "TJTO", "state", "tjto_jurisprudencia", "mixed", "PORTAL", ("acordao", "sentenca")
    ),
    _Declaration(
        "TJMG",
        "state",
        "tjmg_jurisprudencia",
        "second",
        "JURISPRUDENCIA",
        (),
        "rota Juscraper de espelho de acórdão; CAPTCHA impede validação pública",
    ),
    _Declaration(
        "TJRN",
        "state",
        "tjrn_jurisprudencia",
        "mixed",
        "JURISPRUDENCIA",
        (),
        "rota unificada com contrato CJSG separado; primeiro grau não comprovado",
    ),
    _Declaration(
        "TJRJ",
        "state",
        "tjrj_ejuris",
        "mixed",
        "JURISPRUDENCIA",
        ("acordao", "decisao_monocratica"),
        "superficie complementar; a cobertura CJSG e creditada pelo binding eproc",
    ),
)

_OTHER_DECLARATIONS: tuple[_Declaration, ...] = (
    _Declaration(
        "STF",
        "constitutional",
        "stf_juris",
        "superior",
        "PORTAL",
        ("acordao", "decisao"),
        required=True,
    ),
    _Declaration(
        "STJ", "superior", "stj_scon", "superior", "PORTAL", ("acordao", "decisao"), required=True
    ),
    _Declaration(
        "STJ",
        "superior",
        "stj_dados_abertos_jurisprudencia",
        "superior",
        "AGGREGATE",
        ("acordao",),
        required=False,
    ),
    _Declaration(
        "TSE",
        "electoral",
        "tse_sjur_jurisprudencia",
        "superior",
        "SJUR",
        (),
        "catalogo/metadata; busca decisoria pendente",
        required=True,
    ),
    _Declaration(
        "STM", "military", "stm_jurisprudencia", "superior", "PORTAL", ("acordao",), required=True
    ),
    _Declaration(
        "TST",
        "labor",
        "tst_jurisprudencia",
        "superior",
        "PORTAL",
        ("acordao", "decisao"),
        required=True,
    ),
    _Declaration(
        "TRF2",
        "federal",
        "trf2_eproc_jurisprudencia",
        "second",
        "EPROC",
        ("acordao",),
        required=True,
    ),
    _Declaration(
        "TRF4",
        "federal",
        "trf4_eproc_jurisprudencia",
        "second",
        "EPROC",
        ("acordao",),
        required=True,
    ),
    _Declaration(
        "TRF5",
        "federal",
        "trf5_jurisprudencia",
        "second",
        "JURISPRUDENCIA",
        ("acordao",),
        required=True,
    ),
    _Declaration(
        "TRF6",
        "federal",
        "trf6_eproc_jurisprudencia",
        "second",
        "EPROC",
        ("acordao",),
        required=True,
    ),
    _Declaration(
        "TNU",
        "federal",
        "tnu_eproc_jurisprudencia",
        "superior",
        "EPROC",
        ("acordao",),
        required=True,
    ),
    _Declaration(
        "TRESP",
        "electoral",
        "tre_sp_temas",
        "second",
        "TEMAS",
        ("tema",),
        "temas/curadoria; nao e busca geral de decisoes",
    ),
)


def _provider_lifecycle(provider: str) -> str:
    for entry in load_provider_catalog().get("entries", []):
        if entry.get("source_id") == provider:
            return str(entry.get("lifecycle") or entry.get("implementation_status") or "candidate")
    return "candidate"


def _evidence(provider: str) -> tuple[str, ...]:
    evidence = [f"provider-catalog:{provider}", f"docs/providers/{provider}/README.md"]
    live_artifacts = {
        "justica_eleitoral_sjur": (
            "docs/provider-discovery/tre-sjur-route-inventory-live-20260909.json",
            "docs/provider-discovery/tre-sjur-gold-live-20260909.json",
            "docs/provider-discovery/tre-sp-sjur-pagination-live-20260909.json",
        ),
        "tre_sjur_jurisprudencia": (
            "docs/provider-discovery/tre-sjur-route-inventory-live-20260909.json",
            "docs/provider-discovery/tre-sjur-gold-live-20260909.json",
            "docs/provider-discovery/tre-sp-sjur-pagination-live-20260909.json",
            "docs/provider-discovery/tre-sp-sjur-runtime-live-20260910.json",
        ),
        "tse_sjur_jurisprudencia": ("docs/provider-discovery/tse-sjur-search-live-20260909.json",),
        "tjap_banco_sentencas": ("docs/provider-discovery/tjap-banco-sentencas-live-20260907.json"),
        "tjac_banco_sentencas": (
            "docs/provider-discovery/tjac-banco-sentencas-live-20260912.json",
        ),
        "tjal_esmal_banco_sentencas": (
            "docs/provider-discovery/tjal-esmal-banco-sentencas-live-20260908.json",
            "docs/provider-discovery/tjal-esmal-banco-sentencas-live-20260909.json",
        ),
        "tjmg_ejef_boletim_jurisprudencia": (
            "docs/provider-discovery/tjmg-ejef-boletim-live-20260908.json"
        ),
        "tjse_boletim_jurisprudencia": (
            "docs/provider-discovery/tjse-boletim-jurisprudencia-live-20260906.json"
        ),
        "tjes_jurisprudencia": "docs/provider-discovery/tjes-cjsg-live-20260901.json",
        "tjto_jurisprudencia": (
            "docs/provider-discovery/tjto-cjsg-live-20260906-cycle56.json",
            "docs/provider-discovery/tjto-cjpg-live-20260906.json",
            "docs/provider-discovery/tjto-cjpg-live-20260907.json",
        ),
        "tjrj_eproc_jurisprudencia": (
            "docs/provider-discovery/state-eproc-degree-live-20260906.json"
        ),
        "tjsc_eproc_jurisprudencia": (
            "docs/provider-discovery/state-eproc-degree-live-20260906.json"
        ),
        "tjrn_jurisprudencia": ("docs/provider-discovery/tjrn-cjsg-live-20260906.json"),
        "tjrr_juris": "docs/provider-discovery/tjrr-live-20260905-cycle57.json",
        "tjro_jurisprudencia": (
            "docs/provider-discovery/tjro-cjsg-live-20260906.json",
            "docs/provider-discovery/tjro-cjpg-live-20260906.json",
        ),
        "tjgo_projudi_jurisprudencia": (
            "docs/provider-discovery/tjgo-cjsg-live-20260906-cycle58.json",
            "docs/provider-discovery/tjgo-cjpg-live-20260906.json",
        ),
        # Preserve the original DSpace bounded probe alongside newer
        # promotion/recheck evidence so the matrix retains a complete,
        # auditable lineage for the CJSG binding.
        "tjmg_dspace_jurisprudencia": (
            "docs/provider-discovery/tjmg-dspace-jurisprudencia-live-20260906.json",
        ),
    }
    if provider in live_artifacts:
        value = live_artifacts[provider]
        evidence.extend(value if isinstance(value, tuple) else (value,))
    # Keep the matrix linked to the catalog's current bounded evidence.  The
    # static map above covers historical, degree-specific checks; candidate
    # and blocked providers may receive newer diagnostics without a code
    # change.  Never add an absolute path or an empty value to the public
    # matrix.
    for entry in load_provider_catalog().get("entries", []):
        if entry.get("source_id") != provider:
            continue
        for field_name in ("live_validation", "live_evidence"):
            live = entry.get(field_name)
            if not isinstance(live, dict):
                continue
            path = live.get("evidence")
            if isinstance(path, str) and path and path not in evidence:
                evidence.append(path)
        break
    return tuple(evidence)


def _status_for_provider(provider: str) -> tuple[str, bool]:
    catalog = load_provider_catalog().get("entries", [])
    entry = next((item for item in catalog if item.get("source_id") == provider), None)
    lifecycle = str(
        (entry or {}).get("lifecycle") or (entry or {}).get("implementation_status") or "candidate"
    )
    if lifecycle == "implemented":
        live_status = str((entry or {}).get("live_status") or "unknown")
        if live_status in {"blocked_access", "access_controlled", "access_control_required"}:
            return "blocked_access", False
        if live_status in {"blocked_transport", "transport_blocked"}:
            return "blocked_transport", False
        if live_status in {"source_unavailable", "unavailable"}:
            return "source_unavailable", False
        if live_status in {"valid", "implemented"}:
            return "implemented", True
        # Runtime registration without a recent, valid source check is not
        # enough to claim national degree coverage.
        return "pending_contract", False
    return "candidate", False


def _status_for_surface(provider: str, collection: str) -> tuple[str, bool]:
    """Apply degree-specific live gates on top of provider lifecycle status."""

    status = _status_for_provider(provider)
    if provider == "tjto_jurisprudencia" and collection == "CJPG":
        # A newer bounded recheck supersedes the earlier WAF/202 response when
        # it proves two completed pages with distinct records.  Preserve the
        # older evidence for auditability, but do not let it mask reproducible
        # success obtained with the ordinary public browser User-Agent.
        evidence_root = Path(__file__).resolve().parents[2] / "docs" / "provider-discovery"
        current_path = evidence_root / "tjto-cjpg-live-20260907.json"
        legacy_path = evidence_root / "tjto-cjpg-live-20260906.json"
        try:
            payload = json.loads(current_path.read_text(encoding="utf-8"))
            page_two = payload.get("pagination_probe", {}).get("page_2", {})
            if payload.get("classification") == "valid" and page_two.get("status") == "valid":
                return "implemented", True
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            pass
        try:
            payload = json.loads(legacy_path.read_text(encoding="utf-8"))
            page_two = payload.get("pagination_probe", {}).get("page_2", {})
            if page_two.get("classification") == "async_response_without_completed_body":
                return "blocked_access", False
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return "pending_contract", False
    return status


def _make_surface(
    *,
    authority: str,
    branch: str,
    degree: str,
    collection: str,
    status: str,
    provider: str | None,
    required: bool,
    scope: str = "tribunal",
    document_types: tuple[str, ...] = (),
    notes: str = "",
    extra_evidence: tuple[str, ...] = (),
) -> CoverageSurface:
    return CoverageSurface(
        authority=authority,
        branch=branch,
        degree=degree,
        collection=collection,
        status=status,
        provider=provider,
        queryable=status == "implemented",
        required=required,
        scope=scope,
        document_types=document_types,
        evidence_ids=tuple((*(_evidence(provider) if provider else ()), *extra_evidence)),
        notes=notes,
    )


def _expected_state_surface(court: str, collection: str) -> CoverageSurface:
    direct = (_DIRECT_CJPG if collection == "CJPG" else _DIRECT_CJSG).get(court)
    if direct:
        status, _ = _status_for_surface(direct, collection)
        return _make_surface(
            authority=court,
            branch="state",
            degree="first" if collection == "CJPG" else "second",
            collection=collection,
            status=status,
            provider=direct,
            required=True,
            document_types=("sentenca",) if collection == "CJPG" else ("acordao",),
            notes="colecao especifica com contrato proprio",
        )
    if collection == "CJPG" and court == "TJMG":
        # The official legacy first-degree route is discoverable but currently
        # stops at an access-code/CAPTCHA page.  Keep the route evidence on
        # the gap without binding a provider or counting CJPG coverage.
        return _make_surface(
            authority=court,
            branch="state",
            degree="first",
            collection="CJPG",
            status="candidate",
            provider=None,
            required=True,
            document_types=("sentenca",),
            notes="rota oficial localizada; consulta bloqueada por codigo/CAPTCHA",
            extra_evidence=(
                "docs/provider-discovery/tjmg-cjpg-legacy-live-20260909.json",
                "docs/provider-discovery/tjmg-cjpg-sentenca-route-live-20260909.json",
                "docs/provider-discovery/first-degree-route-inventory-20260909.json",
                "docs/provider-discovery/first-degree-route-inventory-20260913.json",
            ),
        )
    if collection == "CJPG" and court == "TJPR":
        # TJPR exposes an official first-degree landing page, but the bounded
        # response is a portal/search shell rather than a reproducible
        # jurisprudence corpus. Keep the discovery evidence visible without
        # binding or counting a provider.
        return _make_surface(
            authority=court,
            branch="state",
            degree="first",
            collection="CJPG",
            status="candidate",
            provider=None,
            required=True,
            document_types=("sentenca",),
            notes="rota oficial de Sentenca Digital localizada; corpus CJPG ainda nao reproduzivel",
            extra_evidence=(
                "docs/provider-discovery/tjpr-cjpg-route-live-20260909.json",
                "docs/provider-discovery/first-degree-route-inventory-20260909.json",
                "docs/provider-discovery/first-degree-route-inventory-20260913.json",
            ),
        )
    if collection == "CJPG" and court == "TJAM":
        # The official TJAM jurisprudence page currently exposes a site-search
        # shell and links to process portals, not a reproducible first-degree
        # decision corpus. Keep the discovery evidence visible without
        # binding a provider or counting CJPG.
        return _make_surface(
            authority=court,
            branch="state",
            degree="first",
            collection="CJPG",
            status="candidate",
            provider=None,
            required=True,
            document_types=("sentenca",),
            notes="pagina oficial localizada; busca decisoria CJPG ainda nao reproduzivel",
            extra_evidence=(
                "docs/provider-discovery/tjam-cjpg-route-live-20260909.json",
                "docs/provider-discovery/tjam-cjpg-route-live-20260913.json",
                "docs/provider-discovery/first-degree-route-inventory-20260909.json",
                "docs/provider-discovery/first-degree-route-inventory-20260913.json",
            ),
        )
    if collection == "CJPG" and court == "TJBA":
        # TJBA's GraphQL catalog distinguishes appellate classes from a
        # recursal group, but the bounded first-degree probe did not return
        # first-instance decisions. Do not turn a recursal response into CJPG.
        return _make_surface(
            authority=court,
            branch="state",
            degree="first",
            collection="CJPG",
            status="candidate",
            provider=None,
            required=True,
            document_types=("sentenca",),
            notes=(
                "GraphQL oficial rechecado; amostra nao prova CJPG, apenas segundo grau "
                "ou turma recursal"
            ),
            extra_evidence=(
                "docs/provider-discovery/tjba-cjpg-recheck-live-20260909.json",
                "docs/provider-discovery/first-degree-route-inventory-20260909.json",
                "docs/provider-discovery/first-degree-route-inventory-20260913.json",
            ),
        )
    if collection == "CJPG" and court == "TJRS":
        # The official TJRS routes currently expose an institutional
        # Sentenca 10 page, a contextual portal search shell, and a legacy
        # endpoint that returns 404.  None exposes a reproducible first-degree
        # jurisprudence corpus, so retain the evidence without counting CJPG.
        return _make_surface(
            authority=court,
            branch="state",
            degree="first",
            collection="CJPG",
            status="candidate",
            provider=None,
            required=True,
            document_types=("sentenca",),
            notes="rotas oficiais de sentencas rechecadas; corpus CJPG ainda nao reproduzivel",
            extra_evidence=(
                "docs/provider-discovery/tjrs-cjpg-route-live-20260909.json",
                "docs/provider-discovery/first-degree-route-inventory-20260909.json",
                "docs/provider-discovery/first-degree-route-inventory-20260913.json",
            ),
        )
    if collection == "CJPG" and court == "TJSC":
        # TJSC's official jurisprudence entries currently expose only a portal
        # shell with an anti-automation marker. No first-instance records,
        # pagination contract or document route was observed in a bounded GET;
        # do not bind the appellate eproc adapter to CJPG.
        return _make_surface(
            authority=court,
            branch="state",
            degree="first",
            collection="CJPG",
            status="candidate",
            provider=None,
            required=True,
            document_types=("sentenca",),
            notes=(
                "entradas oficiais de jurisprudencia sao shell protegido; "
                "corpus CJPG ainda nao reproduzivel"
            ),
            extra_evidence=(
                "docs/provider-discovery/tjsc-cjpg-route-live-20260909.json",
                "docs/provider-discovery/first-degree-route-inventory-20260909.json",
                "docs/provider-discovery/first-degree-route-inventory-20260913.json",
            ),
        )
    if collection == "CJPG" and court == "TJDFT":
        # TJDFT's public jurisprudence pages currently expose a Plone portal
        # search form, not a reproducible first-degree decision corpus.
        return _make_surface(
            authority=court,
            branch="state",
            degree="first",
            collection="CJPG",
            status="candidate",
            provider=None,
            required=True,
            document_types=("sentenca",),
            notes=(
                "entradas oficiais expõem busca contextual do portal; "
                "corpus CJPG ainda não reproduzível"
            ),
            extra_evidence=(
                "docs/provider-discovery/tjdft-cjpg-route-live-20260909.json",
                "docs/provider-discovery/first-degree-route-inventory-20260909.json",
                "docs/provider-discovery/first-degree-route-inventory-20260913.json",
            ),
        )
    if collection in {"CJPG", "CJSG"} and court == "TJMA":
        # JurisConsult exposes public catalogs, but its first/second-degree
        # result routes require tokenG/keyId CAPTCHA values. Keep both degree
        # surfaces explicit and blocked at discovery rather than binding the
        # catalog-only provider or treating the challenge as an empty search.
        tjma_evidence = [
            "docs/provider-discovery/tjma-jurisprudence-route-live-20260908.json",
            "docs/provider-discovery/tjma-official-alternatives-live-20260907.json",
        ]
        if collection == "CJSG":
            # These probes target the appellate results route specifically;
            # do not attach them to the first-degree gap.
            tjma_evidence.extend(
                (
                    "docs/provider-discovery/tjma-jurisprudencia-captcha-live-20260906.json",
                    "docs/provider-discovery/state-cjsg-blocked-recheck-live-20260913.json",
                )
            )
        return _make_surface(
            authority=court,
            branch="state",
            degree="first" if collection == "CJPG" else "second",
            collection=collection,
            status="candidate",
            provider=None,
            required=True,
            document_types=("sentenca",) if collection == "CJPG" else ("acordao",),
            notes=(
                "JurisConsult possui catalogo publico, mas resultados exigem CAPTCHA; "
                "contrato textual nao comprovado"
            ),
            extra_evidence=tuple(tjma_evidence),
        )
    if collection == "CJSG" and court in _CJSG_PROVIDER_OVERRIDES:
        override_provider = _CJSG_PROVIDER_OVERRIDES[court]
        status, _ = _status_for_provider(override_provider)
        return _make_surface(
            authority=court,
            branch="state",
            degree="second",
            collection="CJSG",
            status=status,
            provider=override_provider,
            required=True,
            document_types=("acordao",),
            notes="provider textual separado; contrato especifico CJSG com filtro de grau",
        )
    equivalents = [item for item in _STATE_EQUIVALENTS if item.authority == court]
    matching = [
        item
        for item in equivalents
        if item.degree in {"mixed", "first" if collection == "CJPG" else "second"}
        # A mixed declaration is not enough to bind a first-degree surface
        # when the provider has an explicit appellate-only live contract.
        and not (collection == "CJPG" and court in {"TJRN", "TJMG", "TJRJ", "TJSC"})
    ]
    provider = matching[0].provider if matching else None
    if court == "TJAP" and collection == "CJSG":
        return _make_surface(
            authority=court,
            branch="state",
            degree="first" if collection == "CJPG" else "second",
            collection=collection,
            status="blocked_access",
            provider="tjap_tucujuris",
            required=True,
            document_types=("sentenca",) if collection == "CJPG" else ("acordao",),
            notes="fonte upstream reporta Turnstile/CAPTCHA; sem bypass",
        )
    if provider:
        status, _ = _status_for_provider(provider)
        status = "pending_contract" if status == "implemented" else status
        note = "provider equivalente nao prova contrato especifico de " + collection
    else:
        status = "candidate"
        note = "nenhum provider especifico reconciliado"
    return _make_surface(
        authority=court,
        branch="state",
        degree="first" if collection == "CJPG" else "second",
        collection=collection,
        status=status,
        provider=provider,
        required=True,
        document_types=("sentenca",) if collection == "CJPG" else ("acordao",),
        notes=note,
    )


def _declaration_surface(item: _Declaration) -> CoverageSurface:
    lifecycle_status, queryable = _status_for_provider(item.provider)
    if item.collection == "CATALOG" and lifecycle_status == "implemented":
        lifecycle_status = "pending_contract"
        queryable = False
    # SJUR has a promoted metadata adapter, but the decision-search route is
    # still protected by anti-robot validation. Keep the jurisprudence row
    # visible without inflating national decision coverage.
    if (
        item.provider in {"justica_eleitoral_sjur", "tse_sjur_jurisprudencia"}
        and item.collection == "SJUR"
    ):
        lifecycle_status = "pending_contract"
        queryable = False
    return CoverageSurface(
        authority=item.authority,
        branch=item.branch,
        degree=item.degree,
        collection=item.collection,
        status=lifecycle_status,
        provider=item.provider,
        queryable=queryable and lifecycle_status == "implemented",
        required=item.required,
        scope=item.scope,
        document_types=item.document_types,
        evidence_ids=_evidence(item.provider),
        notes=item.notes,
    )


def build_degree_matrix(
    *, version: str = "2026-09-01", generated_at: str = "2026-09-01"
) -> CoverageMatrix:
    """Build the deterministic matrix from the authority/provider catalogs."""

    surfaces: list[CoverageSurface] = []
    state_codes = sorted(court.code for court in COURTS if court.branch == "state")
    for court in state_codes:
        surfaces.append(_expected_state_surface(court, "CJPG"))
        surfaces.append(_expected_state_surface(court, "CJSG"))

    surfaces.extend(_declaration_surface(item) for item in _STATE_EQUIVALENTS)
    surfaces.extend(_declaration_surface(item) for item in _OTHER_DECLARATIONS)

    # Every TRE is a second-degree electoral authority.  Bounded probes now
    # observe a public route for all 27 UFs and validate one date-partitioned
    # window plus inline document extraction per UF.  Remote page-number
    # pagination remains unverified, so each row stays pending rather than
    # inflating the covered count or hiding the family under the aggregate.
    # Bind rows to the executable family adapter.
    for tre_code in _ELECTORAL_REGIONAL_CODES:
        surfaces.append(
            _make_surface(
                authority=tre_code,
                branch="electoral",
                degree="second",
                collection="SJUR",
                status="pending_contract",
                provider="tre_sjur_jurisprudencia",
                required=True,
                document_types=("acordao", "decisao", "resolucao"),
                extra_evidence=(
                    "docs/provider-discovery/tre-sjur-date-partition-uf-sweep-live-20260913.json",
                    "docs/provider-discovery/tre-sjur-document-uf-sweep-live-20260913.json",
                ),
                notes=(
                    "rota SJUR/TRE publica observada; contrato por UF; janela temporal "
                    "e texto de documento validados por UF; paginação remota geral "
                    "permanece nao comprovada"
                ),
            )
        )
    # Explicit gaps for first-instance units that are not tribunal authorities.
    unit_gaps = (
        ("FEDERAL_FIRST_DEGREE_UNITS", "federal", "first", "EPROC", "varas federais e JEFs"),
        ("LABOR_FIRST_DEGREE_UNITS", "labor", "first", "PORTAL", "varas do trabalho"),
        ("ELECTORAL_FIRST_DEGREE_UNITS", "electoral", "first", "SJUR", "zonas eleitorais"),
        (
            "MILITARY_FIRST_DEGREE_UNITS",
            "military",
            "first",
            "PORTAL",
            "auditorias, varas ou conselhos militares",
        ),
        (
            "TRES_AGGREGATE",
            "electoral",
            "second",
            "SJUR",
            "agregador TREs; busca decisoria ainda pendente",
        ),
    )
    for authority, branch, degree, collection, note in unit_gaps:
        provider = "justica_eleitoral_sjur" if authority == "TRES_AGGREGATE" else None
        status = "pending_contract" if provider else "candidate"
        surfaces.append(
            _make_surface(
                authority=authority,
                branch=branch,
                degree=degree,
                collection=collection,
                status=status,
                provider=provider,
                required=True,
                scope="judicial_unit_gap",
                notes=note,
            )
        )

    # Missing second-degree regional courts remain explicit even if a sibling
    # provider exists elsewhere in the branch.
    for trf_region in ("1", "3"):
        # TRF1 has a real NanoJuris adapter for the public CJF/PrimeFaces
        # surface.  Its current live recheck is access-controlled, so it must
        # remain pending/blocked rather than being represented as a
        # providerless discovery gap.  TRF3 keeps its narrower exact-process
        # adapter and remains a candidate for general jurisprudence.
        provider = "trf3_jurisprudencia" if trf_region == "3" else "cjf_jurisprudencia"
        status, _ = _status_for_provider(provider)
        if trf_region == "3":
            status = "candidate"
        surfaces.append(
            _make_surface(
                authority=f"TRF{trf_region}",
                branch="federal",
                degree="second",
                collection="JURISPRUDENCIA",
                status=status,
                provider=provider,
                required=True,
                notes=(
                    "TRF1/CJF rota publica JSF; rechecagem atual exige controle de acesso"
                    if trf_region == "1"
                    else "TRF regional sem contrato geral de jurisprudencia reconciliado"
                ),
            )
        )
    for trt_region in range(1, 25):
        provider = "trt2_pje_jurisprudencia" if trt_region == 2 else None
        surfaces.append(
            _make_surface(
                authority=f"TRT{trt_region}",
                branch="labor",
                degree="second",
                collection="JURISPRUDENCIA",
                status="candidate" if provider is None else "candidate",
                provider=provider,
                required=True,
                notes="TRT regional; contrato de decisao ainda nao promovido",
            )
        )
    for authority in ("TJMMG", "TJMSP", "TJMRS"):
        # TJMMG now has a bounded public portal adapter.  It is intentionally
        # not a broad federated corpus (the source has no remote pagination),
        # but the native PORTAL surface must still retain its provider binding
        # and explicit pending-contract status instead of appearing as an
        # unmapped military gap.
        provider = "tjmmg_jurisprudencia_api" if authority == "TJMMG" else None
        status, _ = _status_for_provider(provider) if provider else ("candidate", False)
        surfaces.append(
            _make_surface(
                authority=authority,
                branch="military",
                degree="second",
                collection="PORTAL",
                status=status,
                provider=provider,
                required=True,
                notes=(
                    "consulta bounded por numero/data; sem paginacao remota e fora da federacao"
                    if provider
                    else "TJM estadual sem provider runtime"
                ),
            )
        )

    surfaces.sort(
        key=lambda item: (
            item.branch,
            item.authority,
            item.collection,
            item.degree,
            item.provider or "",
        )
    )
    matrix = CoverageMatrix(
        version=version,
        generated_at=generated_at,
        surfaces=tuple(surfaces),
        source_artifacts=(
            "src/nanojuris/brazil.py",
            "docs/registry/providers.json",
            "docs/registry/provider-catalog.full.json",
        ),
    )
    matrix.validate()
    return matrix


__all__ = [
    "CoverageBranch",
    "CoverageDegree",
    "CoverageMatrix",
    "CoverageMatrixValidationError",
    "CoverageScope",
    "CoverageStatus",
    "CoverageSurface",
    "build_degree_matrix",
]
