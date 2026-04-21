#!/usr/bin/env python3
"""Append a partner to PARTNERS in WorkshopDispatch.tsx + add tagline keys to all 4 locale JSONs.

Idempotent: if the partner name or taglineKey already exists, exits with an error
rather than duplicating. Logo file must already exist (use normalize_logo.py first).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REPO = Path("/Users/mark/lovstudio/coding/web")
DISPATCH = REPO / "app/(main)/(home)/WorkshopDispatch.tsx"
PUBLIC = REPO / "public"
LOCALES_DIR = REPO / "src/i18n/messages"
LOCALES = ["zh-CN", "en", "ja", "th"]


def insert_partner_entry(src: str, name: str, href: str, logo: str, key: str, show_name: bool) -> str:
    if f'name: "{name}"' in src:
        sys.exit(f"Partner '{name}' already exists in PARTNERS")

    show_suffix = ", showName: true" if show_name else ""
    line = (
        f'  {{ name: "{name}", '
        f'href: "{href}", '
        f'logo: "{logo}", '
        f'taglineKey: "{key}"{show_suffix} }},\n'
    )

    # Insert before the array's closing "]" — the line that is exactly "]"
    # right after the last partner entry.
    pattern = re.compile(r"(\n)(\]\nexport function WorkshopDispatch)", re.M)
    new_src, n = pattern.subn(rf"\1{re.escape(line).replace(chr(92), '')}\2", src, count=1)
    if n == 0:
        # Fallback: try simpler "\n]\n" close
        new_src, n = re.subn(r"(\n)(\]\n)", rf"\1{line}\2", src, count=1)
    if n == 0:
        sys.exit("Could not find PARTNERS closing bracket — manual edit required")
    return new_src


def insert_tagline(locale_path: Path, key: str, value: str):
    text = locale_path.read_text()
    if f'"{key}"' in text:
        return  # idempotent
    # Insert as the new last entry inside the dispatch block (before its closing "}").
    # Strategy: find the last `partner...Tagline` entry and append after it.
    matches = list(re.finditer(r'(\n\s*"partner\w+Tagline":\s*"[^"]*")(,?)\n', text))
    if not matches:
        sys.exit(f"Could not find any partner*Tagline entries in {locale_path.name}")
    last = matches[-1]
    insertion = f'{last.group(1)},\n    "{key}": "{value}"\n'
    new_text = text[: last.start()] + insertion + text[last.end():]
    locale_path.write_text(new_text)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", required=True, help="Display name (CJK ok)")
    ap.add_argument("--href", required=True, help="Brand homepage URL")
    ap.add_argument(
        "--logo",
        required=True,
        help="Logo path under /public, e.g. /partners/foo/logo.png",
    )
    ap.add_argument(
        "--key",
        required=True,
        help="Tagline i18n key, e.g. partnerFooTagline",
    )
    ap.add_argument("--zh", required=True, help="Tagline in Simplified Chinese")
    ap.add_argument("--en", required=True, help="Tagline in English")
    ap.add_argument("--ja", required=True, help="Tagline in Japanese")
    ap.add_argument("--th", required=True, help="Tagline in Thai")
    ap.add_argument(
        "--show-name",
        action="store_true",
        help="Render the name next to the logo (use for icon-only logos < 32px wide)",
    )
    args = ap.parse_args()

    logo_file = PUBLIC / args.logo.lstrip("/")
    if not logo_file.exists():
        sys.exit(f"Logo file missing: {logo_file}\nRun normalize_logo.py first.")

    src = DISPATCH.read_text()
    new_src = insert_partner_entry(src, args.name, args.href, args.logo, args.key, args.show_name)
    DISPATCH.write_text(new_src)
    print(f"✓ Added '{args.name}' to PARTNERS")

    taglines = {"zh-CN": args.zh, "en": args.en, "ja": args.ja, "th": args.th}
    for loc, txt in taglines.items():
        insert_tagline(LOCALES_DIR / f"{loc}.json", args.key, txt)
        print(f"✓ Added {args.key} to {loc}.json")


if __name__ == "__main__":
    main()
