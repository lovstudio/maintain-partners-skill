---
name: lovstudio:maintain-partners
description: >
  Maintain the LovStudio website's partners section: scrape brand logos from
  homepages, normalize to the 80px-tall canvas, replace existing logos with
  user-provided files, append new partners to the PARTNERS array with i18n
  taglines across zh-CN/en/ja/th, and audit the section for dead URLs / missing
  files / missing translations. Trigger when the user mentions "合作伙伴",
  "partners", "trusted by", "新增 logo", "标准化 logo", "替换 logo",
  "审计合作伙伴", "维护合作伙伴".
license: MIT
compatibility: >
  Requires Python 3.8+ with Pillow (`pip install Pillow --break-system-packages`).
  Optional: playwright + chromium for JS-rendered SPA scraping.
  Tested on macOS; Linux should work.
metadata:
  author: lovstudio
  version: "0.1.0"
  tags: [lovstudio, web, branding, i18n]
---

# maintain-partners — LovStudio 合作伙伴板块维护

Operates on `/Users/mark/lovstudio/coding/web` (the LovStudio website repo).
The partners strip lives in `app/(main)/(home)/WorkshopDispatch.tsx` as a
`PARTNERS: Partner[]` array; logos in `public/partners/<slug>/logo.png`;
taglines in `src/i18n/messages/{zh-CN,en,ja,th}.json` under `dispatch.partner*Tagline`.

## When to Use

- User asks to **add** one or more new partners (with or without a logo URL).
- User asks to **standardize / normalize** a logo (sizing wrong, white-on-white, etc.).
- User provides a local file and asks to **replace** an existing partner's logo.
- User asks to **audit** the partners section before a release.

## Standards

- Logo canvas: **80px content height**, width auto, optimized PNG.
- For white-on-transparent logos: invert (full or selective) so they show on
  the light grayscale strip.
- For icon-only logos < ~40px wide after normalization: pass `--show-name`
  when adding so the brand name renders next to the icon.
- Tagline format: `<品牌名> · <一句话定位>` in Chinese; mirror style in en/ja/th.

## Workflow

### Op 1: Add a new partner

1. Ask the user for the brand name + homepage URL via `AskUserQuestion`.
2. Try to scrape the logo (static first, JS fallback):
   ```bash
   python3 ~/.claude/skills/lovstudio-maintain-partners/scripts/scrape_logo.py \
     --url <URL> --download /tmp/<slug>.png
   ```
   If empty, retry with `--js`. If still empty, ask the user for a direct logo URL or local file.
3. Visually verify with the Read tool before normalizing.
4. Normalize:
   ```bash
   python3 ~/.claude/skills/lovstudio-maintain-partners/scripts/normalize_logo.py \
     --src /tmp/<slug>.png \
     --dst /Users/mark/lovstudio/coding/web/public/partners/<slug>/logo.png \
     --invert auto
   ```
5. Read the normalized PNG to confirm it's visible (not white-on-white).
6. Append to PARTNERS + all 4 locale JSONs:
   ```bash
   python3 ~/.claude/skills/lovstudio-maintain-partners/scripts/add_partner.py \
     --name "<显示名>" --href "<URL>" \
     --logo "/partners/<slug>/logo.png" \
     --key partner<Slug>Tagline \
     --zh "..." --en "..." --ja "..." --th "..." \
     [--show-name]
   ```

### Op 2: Normalize an existing logo

```bash
python3 ~/.claude/skills/lovstudio-maintain-partners/scripts/normalize_logo.py \
  --src public/partners/<slug>/logo.png \
  --dst public/partners/<slug>/logo.png \
  --invert auto
```

Re-read after to verify.

### Op 3: Replace logo from a user-provided file

User typically provides a path under `~/lovstudio/partners/<品牌>/<file>`.

```bash
python3 ~/.claude/skills/lovstudio-maintain-partners/scripts/normalize_logo.py \
  --src "<user-provided path>" \
  --dst /Users/mark/lovstudio/coding/web/public/partners/<slug>/logo.png \
  --invert auto
```

JPEG inputs auto-strip near-white background to transparent before crop.

### Op 4: Audit

```bash
python3 ~/.claude/skills/lovstudio-maintain-partners/scripts/audit_partners.py
# add --probe to also HTTP-check every href (slow, requires proxy)
```

Reports: missing logo files, missing i18n keys per locale, dead URLs.

## CLI Reference

### normalize_logo.py
| Flag | Default | Notes |
|---|---|---|
| `--src` | required | input image (PNG/JPG/rasterized SVG) |
| `--dst` | required | output PNG path; parent dirs auto-created |
| `--height` | `80` | target content height |
| `--invert` | `auto` | `auto` / `off` / `full` / `selective` (selective preserves colored icons) |

### scrape_logo.py
| Flag | Default | Notes |
|---|---|---|
| `--url` | required | brand homepage |
| `--js` | off | use Playwright headless Chromium for SPAs |
| `--download` | off | save first candidate to this path |

### add_partner.py
| Flag | Notes |
|---|---|
| `--name` | display name (CJK ok) |
| `--href` | brand URL |
| `--logo` | path under `/public`, e.g. `/partners/foo/logo.png` |
| `--key` | i18n key, e.g. `partnerFooTagline` |
| `--zh / --en / --ja / --th` | tagline strings (all required) |
| `--show-name` | render name next to icon for narrow logos |

### audit_partners.py
| Flag | Notes |
|---|---|
| `--probe` | HTTP-probe every href (slow, needs proxy env vars) |

## Network proxy

Sandbox child processes don't inherit the system ClashX proxy. Before
scraping or probing, export:

```bash
export https_proxy=http://127.0.0.1:7890 \
       http_proxy=http://127.0.0.1:7890 \
       all_proxy=socks5://127.0.0.1:7891
```

`scrape_logo.py` and `audit_partners.py` already inject these for `curl` /
Playwright invocations.

## Dependencies

```bash
pip install Pillow --break-system-packages
# Optional, for JS-rendered SPAs:
pip install playwright --break-system-packages && playwright install chromium
```
