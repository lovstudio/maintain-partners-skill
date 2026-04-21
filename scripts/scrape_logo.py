#!/usr/bin/env python3
"""Scrape a logo from a brand homepage.

Two strategies:
  1. Static HTML — fetch with curl, regex-match img src containing "logo".
  2. JS-rendered — Playwright headless Chromium, extract img + CSS background-image.

Use strategy 2 (--js) when strategy 1 returns nothing useful (SPA, Wix, etc.).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urljoin


PROXY_ENV = {
    "https_proxy": "http://127.0.0.1:7890",
    "http_proxy": "http://127.0.0.1:7890",
    "all_proxy": "socks5://127.0.0.1:7891",
}


def curl_fetch(url: str, dst: Path | None = None, timeout: int = 15) -> str:
    """Fetch URL with system proxy. Returns text or saves to dst (binary)."""
    cmd = ["curl", "-sL", "-m", str(timeout), url]
    if dst:
        cmd += ["-o", str(dst)]
    r = subprocess.run(cmd, env={**__import__("os").environ, **PROXY_ENV}, capture_output=True)
    if dst:
        return ""
    return r.stdout.decode("utf-8", errors="replace")


def scan_static(html: str, base_url: str) -> list[dict]:
    """Return logo-ish image candidates from static HTML."""
    out = []
    # img with src containing logo/brand
    for m in re.finditer(
        r'<img[^>]*\b(?:src|data-src)=["\']([^"\']+)["\'][^>]*>',
        html,
        re.I,
    ):
        src = m.group(1)
        full = m.group(0).lower()
        if any(k in src.lower() or k in full for k in ("logo", "brand", "header")):
            out.append({"kind": "img", "src": urljoin(base_url, src)})
    return out


def scan_js(url: str, timeout_ms: int = 30000) -> list[dict]:
    """Render with Playwright and extract images + CSS bg-image URLs."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit(
            "Missing dependency: pip install playwright --break-system-packages "
            "&& playwright install chromium"
        )

    items = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            proxy={"server": "http://127.0.0.1:7890"},
        )
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        page = ctx.new_page()
        try:
            page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            raw = page.evaluate(
                """() => {
                    const items = [];
                    document.querySelectorAll('img').forEach(el => {
                      const src = el.src || el.getAttribute('data-src') || '';
                      if (src) items.push({kind:'img', src, alt: el.alt||'', cls: el.className||''});
                    });
                    document.querySelectorAll('*').forEach(el => {
                      const bg = window.getComputedStyle(el).backgroundImage;
                      if (bg && bg !== 'none' && bg.includes('url(')) {
                        const m = bg.match(/url\\(["']?([^"')]+)/);
                        if (m) items.push({kind:'bg', src: m[1], cls: el.className||''});
                      }
                    });
                    return items;
                }"""
            )
            for c in raw:
                hay = (c["src"] + c.get("alt", "") + c.get("cls", "")).lower()
                if any(k in hay for k in ("logo", "brand", "mark", "header", "nav")):
                    items.append(c)
        finally:
            browser.close()
    return items


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", required=True, help="Brand homepage URL")
    ap.add_argument("--js", action="store_true", help="Use Playwright (for JS-rendered SPAs)")
    ap.add_argument(
        "--download",
        help="Pick the first candidate and save to this path (otherwise just prints candidates)",
    )
    args = ap.parse_args()

    if args.js:
        candidates = scan_js(args.url)
    else:
        html = curl_fetch(args.url)
        candidates = scan_static(html, args.url)

    if not candidates:
        sys.exit("No logo candidates found. Try --js, or pick a URL manually.")

    print(json.dumps(candidates, indent=2, ensure_ascii=False))

    if args.download:
        pick = candidates[0]["src"]
        dst = Path(args.download).expanduser()
        dst.parent.mkdir(parents=True, exist_ok=True)
        curl_fetch(pick, dst=dst)
        print(f"\nDownloaded {pick} → {dst}")


if __name__ == "__main__":
    main()
