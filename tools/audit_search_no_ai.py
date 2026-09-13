"""Static gate for the deterministic live-search ranking contract.

The v1 live ranker is intentionally lexical and CPU-only.  This audit is a
small, dependency-free guard that prevents an accidental import of an LLM,
embedding model, vector store, or paid reranking client in the search path.
It is not a security boundary and does not inspect runtime network traffic.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOTS = (ROOT / "src" / "nanojuris", ROOT.parent / "nanojuris-platform" / "src")

# Keep this list deliberately focused on providers that would change the
# stated product contract.  Ordinary HTTP, Unicode and lexical libraries are
# allowed and are not treated as AI dependencies.
FORBIDDEN_MODULES = frozenset(
    {
        "openai",
        "anthropic",
        "cohere",
        "google.generativeai",
        "vertexai",
        "boto3",
        "sentence_transformers",
        "transformers",
        "torch",
        "tensorflow",
        "faiss",
        "chromadb",
        "pinecone",
        "weaviate",
        "qdrant_client",
    }
)
FORBIDDEN_CALL_MARKERS = frozenset(
    {
        "embeddings.create",
        "chat.completions.create",
        "responses.create",
        "rerank",
        "vector_search",
        "similarity_search",
    }
)


def _module_forbidden(module: str) -> bool:
    return any(module == item or module.startswith(f"{item}.") for item in FORBIDDEN_MODULES)


def _call_name(node: ast.Call) -> str:
    function = node.func
    if isinstance(function, ast.Attribute):
        parent = _call_name(ast.Call(func=function.value, args=[], keywords=[]))
        return f"{parent}.{function.attr}" if parent else function.attr
    if isinstance(function, ast.Name):
        return function.id
    return ""


def audit(roots: tuple[Path, ...] = DEFAULT_ROOTS) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    files_scanned = 0
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.py")):
            files_scanned += 1
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (OSError, SyntaxError, UnicodeDecodeError) as exc:
                violations.append({"kind": "parse_error", "path": str(path), "error": str(exc)})
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if _module_forbidden(alias.name):
                            violations.append(
                                {
                                    "kind": "forbidden_import",
                                    "path": str(path),
                                    "line": node.lineno,
                                    "module": alias.name,
                                }
                            )
                elif isinstance(node, ast.ImportFrom) and _module_forbidden(node.module or ""):
                    violations.append(
                        {
                            "kind": "forbidden_import",
                            "path": str(path),
                            "line": node.lineno,
                            "module": node.module,
                        }
                    )
                elif isinstance(node, ast.Call):
                    name = _call_name(node)
                    if name in FORBIDDEN_CALL_MARKERS or any(
                        name.endswith(f".{marker}") for marker in FORBIDDEN_CALL_MARKERS
                    ):
                        violations.append(
                            {
                                "kind": "forbidden_call",
                                "path": str(path),
                                "line": node.lineno,
                                "call": name,
                            }
                        )
    return {
        "schema_version": 1,
        "contract": "legal-live-v1-deterministic-no-ai",
        "files_scanned": files_scanned,
        "forbidden_modules": sorted(FORBIDDEN_MODULES),
        "violations": violations,
        "status": "pass" if not violations else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit the audit as JSON")
    args = parser.parse_args()
    result = audit()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"search no-AI gate: {result['status']} ({result['files_scanned']} files)")
        for violation in result["violations"]:
            print(json.dumps(violation, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
