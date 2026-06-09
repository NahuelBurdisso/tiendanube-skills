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

## A note on the strategic (narrative) report
The financial report is fully automatable. A **strategic/narrative** report (page-by-page redesign scope, institutional-page gaps, plan/Impulso requirements) is store-specific prose — author it by hand using `analysis.json` as the factual spine, reusing the same CSS/brand tokens from `build-report.mjs` for visual consistency. Mark anything that depends on client-provided content or paid apps as such; don't list it as a dev deliverable.
