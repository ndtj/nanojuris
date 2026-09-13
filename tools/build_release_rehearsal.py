"""Validate local distribution artifacts without publishing them."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DISTRIBUTION = ROOT / ".artifacts" / "release-rehearsal-20260902"
DEFAULT_OUTPUT = ROOT / "docs" / "operations" / "release-rehearsal-20260902.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "docs" / "operations" / "release-rehearsal-20260902.md"
# The expanded 0.6 provider registry is intentionally public runtime payload.
WHEEL_LIMIT = 1_100_000
SDIST_LIMIT = 1_500_000
WHEEL_RE = re.compile(r"^nanojuris-(?P<version>[^-]+)-.*\.whl$")
SDIST_RE = re.compile(r"^nanojuris-(?P<version>[^-]+)\.tar\.gz$")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _twine_check(artifacts: list[Path]) -> tuple[str, str | None]:
    try:
        result = subprocess.run(
            ["python", "-m", "twine", "check", *(str(path) for path in artifacts)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return "not_run", type(exc).__name__
    return ("passed", None) if result.returncode == 0 else ("failed", result.stderr[-500:])


def build(
    distribution: Path = DEFAULT_DISTRIBUTION, *, generated_at: str | None = None
) -> dict[str, Any]:
    artifacts = sorted([*distribution.glob("*.whl"), *distribution.glob("*.tar.gz")])
    wheel = next((path for path in artifacts if WHEEL_RE.match(path.name)), None)
    sdist = next((path for path in artifacts if SDIST_RE.match(path.name)), None)
    twine_status, twine_error = (
        _twine_check(artifacts) if artifacts else ("not_run", "no_artifacts")
    )
    files = []
    for path in artifacts:
        limit = WHEEL_LIMIT if path.suffix == ".whl" else SDIST_LIMIT
        files.append(
            {
                "name": path.name,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
                "size_limit": limit,
                "size_status": "passed" if path.stat().st_size <= limit else "failed",
            }
        )
    version = None
    if wheel:
        version = WHEEL_RE.match(wheel.name).group("version")  # type: ignore[union-attr]
    elif sdist:
        version = SDIST_RE.match(sdist.name).group("version")  # type: ignore[union-attr]
    checks = {
        "wheel_present": wheel is not None,
        "sdist_present": sdist is not None,
        "twine_check": twine_status == "passed",
        "size_budgets": bool(files) and all(item["size_status"] == "passed" for item in files),
    }
    timestamp = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "schema_version": 1,
        "generated_at": timestamp,
        "audit_mode": "local_release_rehearsal",
        "production_action_performed": False,
        "distribution": distribution.as_posix(),
        "version": version,
        "artifacts": files,
        "checks": checks,
        "twine": {"status": twine_status, "error": twine_error},
        "status": "passed" if all(checks.values()) else "failed",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Release rehearsal local",
        "",
        "Validação de wheel/sdist sem publicação ou alteração de produção.",
        "",
        f"Versão: **{payload['version'] or 'unknown'}**; resultado: **{payload['status']}**.",
        "",
        "| Artefato | Bytes | Limite | SHA-256 | Tamanho |",
        "|---|---:|---:|---|---|",
    ]
    for item in payload["artifacts"]:
        lines.append(
            f"| `{item['name']}` | {item['bytes']:,} | {item['size_limit']:,} | "
            f"`{item['sha256']}` | `{item['size_status']}` |"
        )
    lines += [
        "",
        f"Twine check: **{payload['twine']['status']}**.",
        "Produção/publicação: **não executadas**.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--distribution", type=Path, default=DEFAULT_DISTRIBUTION)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    distribution = (
        args.distribution if args.distribution.is_absolute() else ROOT / args.distribution
    )
    output = args.output if args.output.is_absolute() else ROOT / args.output
    markdown_output = (
        args.markdown_output if args.markdown_output.is_absolute() else ROOT / args.markdown_output
    )
    payload = build(distribution, generated_at=args.generated_at)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {"output": str(output), **payload["checks"], "status": payload["status"]},
            sort_keys=True,
        )
    )
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
