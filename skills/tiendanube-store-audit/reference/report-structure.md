# Report structure & lever framework

## Two report modes from one dataset
`analysis.json` holds both operative and financial metrics. `build-report.mjs` emits a combined report; to produce a **purely financial** or **purely operative** deck, drop the sections you don't need (each `<div class="page section-open">` is one section).

## Section model (the combined report)
| # | Section | Purpose | Key visuals |
|---|---|---|---|
| — | Cover | Headline: total annual upside | big stat |
| 00 | La tesis | Run-rate vs. upside, framing | 4 stat cards + lever bar chart |
| 01 | El motor | Growth + seasonality + payment mix | year bars, month bars, gateway bars |
| 02 | Las fugas | Quantified leaks | leak bar chart + table |
| 03 | El plan de ingresos | **The core** — levers | lever table with $/año, effort |
| 04 | Operativa y catálogo | Catalog/SEO/stock/categories state | stat cards + table |
| 05 | Letra chica | Data origin + assumptions + risk | assumption/risk table |

## Opportunity-lever framework
Every lever = **value × assumption**, never a bare number. Defaults are deliberately conservative; tune per store and keep them in the report.

| Lever | Formula | Default | Risk |
|---|---|---|---|
| Carrito abandonado | `abandoned_annualized × rate` | 8% | bajo |
| AOV uplift | `runRate × pct` | 10% | medio |
| Recompra | `buyers × +pp × AOV` | +8pp | medio |
| SEO | `runRate × pct` | 5% | medio |
| Vidriera muerta | `deadListings × (runRate/published) × rate` | 40% | bajo |
| Descuento transferencia | `discountGivenYr × (old−new)/old` | 20→15% | **alto** (toca precio) |
| Pedidos sin pagar | `pendingValue × rate` | 10% | bajo |

`discountGivenYr = runRate × offlineShare / (1 − oldPct) × oldPct`.

**Why formula-based:** a hardcoded "$2.5M" is indefensible; `buyers × 8pp × AOV` survives a CFO's questions. Risk column is mandatory — the price lever especially must be flagged and A/B-tested, not shipped blind.

## Run-rate definition
Trailing-twelve-months paid revenue (annualized if <12 months of history). More robust than "last month × 12" against seasonality. Stated explicitly in section 05.

## Data sources (all read-only)
| Metric | Endpoint | Field |
|---|---|---|
| Revenue, gateways, leaks | `/orders` | `payment_status='paid'`, `total`, `gateway`, `status` |
| Abandoned carts | `/checkouts` | rows without `completed_at` (recent window only) |
| Repeat rate | `/orders` | distinct `customer.id` with ≥2 paid orders |
| Catalog/SEO/stock | `/products` | `variants[].price/stock/promotional_price`, `seo_title`, `images`, `attributes` |
| Categories | `/categories` | `parent` tree |
| Coupons | `/coupons` | `used` |

## Page-break discipline (BOTH report types)
A4 print has hard page jumps. Defaults that prevent ugly cuts:
- `tr{page-break-inside:avoid}`, `.callout`/`.chartbox{page-break-inside:avoid}` — already in the CSS; they keep rows and cards whole.
- **`.sec{break-inside:avoid}`** — wrap EVERY section (its `<h3>`/`<h4>` + the table/stats/list/paragraphs that belong to it) in `<div class="sec">…</div>`. This is what stops a *section* (heading + body) from splitting across a page. Without it, a heading orphans at a page bottom and its table flows to the next page.
- If a `.sec` is taller than a page it still must split — then shorten it or break it into two `.sec` blocks (e.g. one table → two).
- **Verify by rasterizing, every time:** `pdftoppm -png -r 90 report.pdf /tmp/pg && open /tmp/pg-*.png`, then eyeball each page. A section split across pages = a `.sec` to add or tighten. Re-render until clean. Near-empty pages where a whole `.callout`/`.sec` jumped (rather than split) are acceptable.

## The strategic (narrative) report
The financial report is fully automatable (`build-report.mjs`). A **strategic/narrative** report (diagnosis + plan + investment, page-by-page redesign scope, institutional-page gaps, plan/Impulso requirements) is store-specific prose — author it by hand.

**Start from `assets/narrative-report-template.html`** (copy → `report.html`, recolor the `:root` tokens, fill with real numbers from `analysis.json`). Same CSS/brand tokens as `build-report.mjs`, so both decks look alike.

**Proven three-informe structure** (keep state and work in *separate* informes — never mix a finding with its action):
| # | Informe | Contains |
|---|---|---|
| 00 | Resumen ejecutivo | headline stats + "la foto en una frase" + how-to-read |
| 01 | **Estado actual** | diagnosis ONLY, no actions — SEO, catálogo, categorías, pagos, clientes, marca (fold shipping in as a fact). Pills used as state flags (`bug`/`bien`), not imperatives. |
| 02 | **Trabajo a realizar** | all the work — **Parte 1** puesta a punto de datos (action table) + **Parte 2** rediseño del theme (A componentes / B home / C ficha / D resto, fases, "qué NO cambia") |
| 03 | **Inversión** | one-time price + included deliverables (each mapping to Informe 02) + recurring platform plan |

Honesty rules: mark anything that depends on client-provided content or paid apps as such — don't list it as a dev deliverable. Every figure traces to data; estimates are stated as estimates.
