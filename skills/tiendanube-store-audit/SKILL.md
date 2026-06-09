---
name: tiendanube-store-audit
description: Use when auditing a Tienda Nube / Nuvemshop store to produce an operative or financial improvement report — quantifying catalog/SEO gaps, abandoned-cart and unpaid-order leaks, revenue trends, customer repeat rate and coupon usage into a branded PDF with charts and money-quantified opportunity levers. Spanish/Portuguese e-commerce, mitiendanube.com / tiendanube.com.
---

# Tienda Nube Store Audit → Improvement Reports

Turn a live Tienda Nube store's real API data into a coherent, **branded PDF report** of operative + financial improvements, with charts and **money-quantified opportunity levers** (each with an explicit, defensible assumption).

**Core principle:** every recommendation carries a number, and every number carries its assumption and risk. Estimates, not promises — stated as such.

**REQUIRED BACKGROUND:** Use **tiendanube-stores** for getting an API token (OAuth flow, scopes, store_id) and the platform model. This skill consumes that token; it does NOT obtain it.

## When to use
- "Analyze / audit this Tienda Nube store and tell me what to improve."
- "Make a report of where the store could make more money."
- Operative review (catalog, SEO, stock, categories) OR financial review (revenue, leaks, AOV, repeat).
- NOT for editing the theme or catalog — that's **tiendanube-stores**. This skill only **reads** and reports.

## Prerequisites
A working dir with a `.env` containing a **full-read** token:
```
TIENDANUBE_ACCESS_TOKEN=...   # needs read_products, read_orders, read_customers, read_coupons (+ read_shipping)
TIENDANUBE_STORE_ID=...
CONTACT_EMAIL=you@example.com  # optional, for User-Agent
```
A `write_products`-only token gives catalog data but **403s on orders/customers/coupons** → re-authorize with read scopes (see tiendanube-stores). Chrome/Edge/Chromium for the PDF step.

## Workflow
The scripts live in **this skill's `scripts/` directory** (the base path is printed as "Base directory for this skill: …" when the skill loads). From your working dir (the one holding `.env`):
```bash
SKILL_DIR="<that base directory>"
cp "$SKILL_DIR"/scripts/{analyze.mjs,build-report.mjs,render.sh} .
chmod +x render.sh
cp "$SKILL_DIR"/scripts/report.config.example.json report.config.json   # then edit brand + assumptions

node analyze.mjs        # store/orders/products/customers/checkouts/coupons → analysis.json (+ summary to stdout)
node build-report.mjs   # analysis.json → report.html (branded, SVG charts)
./render.sh             # report.html → report.pdf (headless Chrome)
```
One run covers operative + financial.

**Two mandatory checks (don't skip):**
1. **Before** building — read `analysis.json` and sanity-check against the store: is `runRate` plausible? Is the `transferGatewayKeys` gateway actually the discounted one? Does `leaks.abandoned.windowDays` look sane (the API returns only a recent window)?
2. **After** rendering — confirm the PDF page count and that the brand/accent landed (the cover shows the store name + headline upside). Then hand it over.

Extra OAuth vars in `.env` (`TIENDANUBE_APP_ID`, `CLIENT_SECRET`) are ignored — only the token + store_id are read.

## Customizing
Copy `scripts/report.config.example.json` → `report.config.json` and edit. Two blocks:
- **`brand`** — `name`, `accent` (hex), `accentWarm`, `preparedFor`, `locale`, `currencySymbol`. Omit the file entirely and it defaults to the store name + a neutral editorial palette.
- **`assumptions`** — the recovery rates and uplift % behind each lever (see table below). Defaults are conservative. Adjust per store; they always print in the report's "letra chica" so they stay defensible.

Money formatting is adaptive: stores under ~$1M/yr render in `k`, larger in `M` — no config needed.

## What the report contains
Cover (headline upside) → **00** thesis (run-rate vs upside) → **01** motor (revenue by year/month, payment mix) → **02** leaks (abandoned/pending/cancelled) → **03** levers table (the core) → **04** operative/catalog state → **05** assumptions & risk. See `reference/report-structure.md` for the section model and the **opportunity-lever framework** (formulas).

## The opportunity levers (formula-based, in analyze.mjs)
| Lever | Formula (conservative) |
|---|---|
| Carrito abandonado | abandoned/año × recovery% |
| AOV +X% | run-rate × upliftPct |
| Recompra | buyers × +pp × AOV |
| SEO | run-rate × upliftPct |
| Vidriera muerta | deadListings × (run-rate/published) × recovery% |
| Descuento transferencia | discountGiven/año × (oldPct−newPct)/oldPct |
| Pedidos sin pagar | pending value × recovery% |

## Common mistakes
- **Hand the PDF without reading `analysis.json`.** Always sanity-check; abandoned-cart windows and gateway names vary per store.
- **Annualizing a tiny checkout window as gospel.** The API returns only recent abandoned checkouts — the builder labels it "anualizado", keep that caveat.
- **Hardcoding the brand.** Use `report.config.json`; the scripts are store-agnostic.
- **Quoting upside as guaranteed.** It's additive estimates with assumptions — never drop the risk column.
- **Treating offline as the transfer channel blindly.** Confirm which `gateway` is the discounted one (`transferGatewayKeys`).
