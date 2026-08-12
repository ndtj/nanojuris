"""Probe a public source route before implementing a NanoJuris provider.

This script intentionally uses a clean requests session. Do not pass browser
cookies, captcha tokens, HAR secrets or authenticated headers.
"""

from __future__ import annotations

import argparse
import json

from nanojuris.route_probe import probe_route

DEFAULT_USER_AGENT = "NanoJuris/route-probe (+https://github.com/lucmolero/nanojuris)"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe a public route with a clean HTTP session before provider work."
    )
    parser.add_argument("url", help="Absolute public URL to test")
    parser.add_argument(
        "--expect",
        action="append",
        default=[],
        help="Text that must appear in the response body. Can be repeated.",
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    args = parser.parse_args()

    result = probe_route(
        args.url,
        expected_texts=args.expect,
        timeout=args.timeout,
        user_agent=args.user_agent,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
