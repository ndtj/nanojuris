"""Regenerate ``src/nanojuris/data/selector_fingerprints.json``.

Each wired provider records a structural fingerprint of the element its result
selector matches on a known-good fixture. ``adaptive_selectors.SelectorMemory``
ships this file as the cold-start baseline for relocation; a successful live run
overwrites the fingerprint with the real page.

Run ``python tools/build_selector_fingerprints.py --write`` after wiring a new
selector or updating a fixture. ``tests/test_selector_fingerprints.py`` asserts
the file matches this registry.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = str(ROOT / "src")
if SOURCE_ROOT in sys.path:
    sys.path.remove(SOURCE_ROOT)
sys.path.insert(0, SOURCE_ROOT)

from bs4 import BeautifulSoup  # noqa: E402

from nanojuris.adaptive_selectors import _bs4_fingerprint, element_fingerprint  # noqa: E402
from nanojuris.parsing import parse_html  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"
OUTPUT = ROOT / "src" / "nanojuris" / "data" / "selector_fingerprints.json"

# (source, selector name, fixture file, css selector, backend)
#   backend: "bs4" -> _bs4_fingerprint, "document" -> element_fingerprint
REGISTRY: list[tuple[str, str, str, str, str]] = [
    (
        "tjdf_juris",
        "acordao_link",
        "tjdf_juris_results.html",
        "#id_link_abrir_dados_acordao, [id*=id_link_abrir_dados_acordao]",
        "document",
    ),
    (
        "stj_informativo",
        "result_item",
        "stj_informativo_infanticidio.html",
        ".clsInformativoBlocoItem",
        "document",
    ),
    (
        "tjgo_projudi_jurisprudencia",
        "result_card",
        "tjgo_projudi_dano_moral.html",
        "div.search-result",
        "document",
    ),
    ("tjpi_juspi", "result_card", "tjpi_juspi_dano_moral.html", "div.callout", "bs4"),
    ("trf5_jurisprudencia", "result_row", "trf5_jurisprudencia_results.html", "td.grid", "bs4"),
    (
        "stm_jurisprudencia",
        "result_panel",
        "stm_jurisprudencia_results.html",
        "div.panel.panel-default",
        "bs4",
    ),
    (
        "tjsp_eproc_jurisprudencia",
        "result_card",
        "tjsp_eproc_jurisprudencia_result.html",
        ".resultadoItem",
        "bs4",
    ),
]

# CJSG and eproc share one parser across several sources; the same anchor
# fingerprint seeds each of them.
_CJSG_SOURCES = ("tjsp_cjsg", "tjac_cjsg", "tjal_cjsg", "tjam_cjsg", "tjms_cjsg", "tjce_cjsg")
for _source in _CJSG_SOURCES:
    REGISTRY.append((_source, "ementa_anchor", "tjsp_cjsg_result.html", "a.downloadEmenta", "bs4"))

_EPROC_SOURCES = (
    "trf2_eproc_jurisprudencia",
    "trf4_eproc_jurisprudencia",
    "tjrj_eproc_jurisprudencia",
    "tjsc_eproc_jurisprudencia",
    "eproc_jurisprudencia_federal",
)
for _source in _EPROC_SOURCES:
    REGISTRY.append(
        (_source, "result_card", "tjsp_eproc_jurisprudencia_result.html", ".resultadoItem", "bs4")
    )


def build() -> dict[str, dict[str, dict]]:
    catalog: dict[str, dict[str, dict]] = {}
    for source, name, fixture, selector, backend in REGISTRY:
        html = (FIXTURES / fixture).read_text(encoding="utf-8", errors="replace")
        if backend == "bs4":
            soup = BeautifulSoup(html, "html.parser")
            hits = soup.select(selector)
            if not hits:
                raise SystemExit(f"{source}: selector {selector!r} matched nothing in {fixture}")
            fingerprint = _bs4_fingerprint(hits[0])
        else:
            hits = parse_html(html).select(selector)
            if not hits:
                raise SystemExit(f"{source}: selector {selector!r} matched nothing in {fixture}")
            fingerprint = element_fingerprint(hits.first)
        catalog.setdefault(source, {})[name] = fingerprint
    return catalog


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the JSON file")
    args = parser.parse_args()
    catalog = build()
    payload = json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.write:
        OUTPUT.write_text(payload, encoding="utf-8")
        print(f"wrote {OUTPUT.relative_to(ROOT)} ({len(catalog)} sources)")
    else:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.is_file() else ""
        if current == payload:
            print("selector_fingerprints.json is current")
        else:
            print("selector_fingerprints.json is STALE - run with --write")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
