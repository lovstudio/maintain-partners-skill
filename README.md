# lovstudio:maintain-partners

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

Maintain the LovStudio website's "Trusted By" partners section: scrape brand
logos, normalize to the 80px canvas, append entries with i18n taglines across
4 locales, and audit for dead URLs / missing assets.

Part of [lovstudio skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
git clone https://github.com/lovstudio/maintain-partners-skill ~/.claude/skills/lovstudio-maintain-partners
pip install Pillow --break-system-packages
# Optional, for SPA scraping:
pip install playwright --break-system-packages && playwright install chromium
```

## What it does

The LovStudio homepage runs a "Trusted By" strip that renders 30+ partner
logos against a `grayscale opacity-60` filter. Maintaining it means three
recurring tasks:

1. **Scraping** — pulling logos out of brand homepages (often JS-gated).
2. **Normalizing** — every logo must trim to its content bbox and resize to
   exactly 80px tall so the strip looks even. White-on-transparent logos must
   be inverted so they show on the light background.
3. **Wiring** — appending the partner to `PARTNERS` in
   `WorkshopDispatch.tsx` and adding a `partner*Tagline` key to all 4 locale
   JSONs (zh-CN / en / ja / th).

This skill is four single-file Python CLIs plus an AI workflow that orchestrates them.

## Scripts

```text
scrape_logo.py      Static + JS scraping (Playwright fallback)
normalize_logo.py   Trim, optional inversion, resize to 80px, write PNG
add_partner.py      Append to PARTNERS array + i18n JSONs (idempotent)
audit_partners.py   Walk PARTNERS; report missing logos / i18n keys / dead URLs
```

## Quick examples

```bash
# Scrape a homepage; falls back to Playwright if static returns nothing
scrape_logo.py --url https://example.com --download /tmp/example.png
scrape_logo.py --url https://spa-example.com --js --download /tmp/spa.png

# Normalize: auto-invert white-on-transparent
normalize_logo.py --src /tmp/example.png \
                  --dst public/partners/example/logo.png

# Add to PARTNERS + i18n
add_partner.py --name "Example" --href "https://example.com" \
               --logo "/partners/example/logo.png" \
               --key partnerExampleTagline \
               --zh "Example · 一句话定位" \
               --en "Example · one-line positioning" \
               --ja "Example · 一行紹介" \
               --th "Example · บรรยายหนึ่งบรรทัด"

# Audit (use --probe to HTTP-check every URL)
audit_partners.py --probe
```

## Repo layout assumed

```
~/lovstudio/coding/web/
├── app/(main)/(home)/WorkshopDispatch.tsx   ← PARTNERS array
├── public/partners/<slug>/logo.png          ← logo files
└── src/i18n/messages/
    ├── zh-CN.json    ← dispatch.partner*Tagline
    ├── en.json
    ├── ja.json
    └── th.json
```

If you fork this for another site, edit the constants at the top of each script.

## License

MIT
