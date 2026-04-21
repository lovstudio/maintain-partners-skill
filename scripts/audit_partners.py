#!/usr/bin/env python3
"""Audit the partners section: dead URLs, missing logos, missing i18n keys.

Walks PARTNERS in WorkshopDispatch.tsx, then for each entry verifies:
  1. logo file exists at the referenced public path
  2. taglineKey exists in all 4 locale JSONs (zh-CN, en, ja, th)
  3. href returns a non-error HTTP status (skipped unless --probe)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


REPO = Path("/Users/mark/lovstudio/coding/web")
DISPATCH = REPO / "app/(main)/(home)/WorkshopDispatch.tsx"
PUBLIC = REPO / "public"
LOCALES = ["zh-CN", "en", "ja", "th"]

PROXY_ENV = {
    "https_proxy": "http://127.0.0.1:7890",
    "http_proxy": "http://127.0.0.1:7890",
    "all_proxy": "socks5://127.0.0.1:7891",
}

PARTNER_RE = re.compile(
    r'\{\s*name:\s*"([^"]+)"\s*,\s*href:\s*"([^"]+)"\s*,\s*logo:\s*"([^"]+)"\s*,\s*taglineKey:\s*"([^"]+)"',
    re.M,
)


def parse_partners(src: str) -> list[dict]:
    return [
        {"name": m[0], "href": m[1], "logo": m[2], "taglineKey": m[3]}
        for m in PARTNER_RE.findall(src)
    ]


def load_tagline_keys(locale: str) -> set[str]:
    p = REPO / "src/i18n/messages" / f"{locale}.json"
    data = json.loads(p.read_text())
    # Tagline keys live under dispatch.partner*Tagline
    dispatch = data.get("dispatch", {})
    return {k for k in dispatch if k.startswith("partner") and k.endswith("Tagline")}


def probe(url: str, timeout: int = 8) -> int:
    cmd = ["curl", "-sL", "-m", str(timeout), "-o", "/dev/null", "-w", "%{http_code}", url]
    r = subprocess.run(cmd, env={**__import__("os").environ, **PROXY_ENV}, capture_output=True)
    try:
        return int(r.stdout.decode().strip() or 0)
    except ValueError:
        return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probe", action="store_true", help="HTTP-probe each href (slow)")
    args = ap.parse_args()

    if not DISPATCH.exists():
        sys.exit(f"Not found: {DISPATCH}")

    partners = parse_partners(DISPATCH.read_text())
    if not partners:
        sys.exit("PARTNERS array empty or unparseable")

    print(f"Parsed {len(partners)} partners")

    locale_keys = {loc: load_tagline_keys(loc) for loc in LOCALES}

    issues: list[str] = []
    for p in partners:
        logo_path = PUBLIC / p["logo"].lstrip("/")
        if not logo_path.exists():
            issues.append(f"  [missing-logo] {p['name']}: {logo_path}")

        for loc in LOCALES:
            if p["taglineKey"] not in locale_keys[loc]:
                issues.append(f"  [missing-i18n:{loc}] {p['name']}: {p['taglineKey']}")

        if args.probe:
            code = probe(p["href"])
            if code == 0 or code >= 400:
                issues.append(f"  [dead-url:{code}] {p['name']}: {p['href']}")

    if issues:
        print(f"\n{len(issues)} issue(s):")
        print("\n".join(issues))
        sys.exit(1)
    print("\n✓ All partners healthy")


if __name__ == "__main__":
    main()
