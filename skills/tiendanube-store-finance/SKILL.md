---
name: tiendanube-store-finance
description: Use when turning a retail client's physical-store accounting workbook (the "Más Orden Más Ganancia" multi-sheet .xlsx) into a financial-analyst report — reads the already-computed statements (Estado de Resultados / Flujos de Dinero / Punto de equilibrio), adds a forward forecast, full ratio suite, and period-over-period variance, and outputs a branded .xlsx + PDF. xlsx-only mode (no Tienda Nube needed). Spanish/AR retail.
---

# Tienda Nube Store Finance (xlsx-only)

Turn a client's accounting workbook into a branded financial report. **Reads** the
workbook's already-computed statements and reconciles to them — never recomputes.
The vendored borghei/financial-analyst scripts AUGMENT the statements: forward
forecast, ratio suite, period-over-period variance. DCF is opt-in (`finance.enableDcf`).

## Prerequisites
- `python3` with **openpyxl** + a PDF renderer (Chrome/Edge/Chromium).
- Install deps from PUBLIC PyPI — this machine's pip is pinned to a private index, so the
  explicit index is REQUIRED:
  `python3 -m pip install --user --index-url https://pypi.org/simple/ openpyxl`

## Workflow
Scripts live in this skill's `scripts/`. From a working dir:
```bash
SKILL_DIR="<base directory printed when this skill loads>"
cp "$SKILL_DIR"/scripts/report.config.example.json report.config.json   # edit brand + finance
python3 "$SKILL_DIR"/scripts/analyze_finance.py "<client-workbook>.xlsx" --config report.config.json --out .
"$SKILL_DIR"/scripts/render.sh report.html store-finance.pdf
```
Outputs: `financials.json`, `store-finance.xlsx` (tabs: Estado de Resultados, Ratios,
Forecast, Variance período, Advertencias), `report.html` → `store-finance.pdf`.

The PDF is a branded editorial-financial report (Bodoni Moda + Archivo, SVG charts):
cover → **00** Resumen ejecutivo (KPIs + computed "lecturas clave") → **01** Estado de
resultados (tabla mensual + barras + cascada P&L) → **02** Rentabilidad y costos
(evolución de márgenes + estructura de costos) → **03** Punto de equilibrio (+ margen de
seguridad) → **04** Proyección y escenarios (base/optimista/conservador + tendencia) →
**05** Variación mensual → **06** Supuestos. Charts live in `scripts/charts.py`; the
narrative is computed in `scripts/html_report.py`. Edit brand/period in `report.config.json`.

## How the parser works
Label-anchored: it finds `ESTADO DE RESULTADOS` / `FLUJOS DE DINERO` /
`PUNTO DE EQUILIBRIO` in column A, detects the month-header row and the **year row**
above it. Templates with two years (24 month columns) are handled — it selects the
**latest year that has data** and analyzes that 12-month window. Extra/missing sheets are
tolerated; a missing statement degrades that feature. Core sheets: Resultados, Ventas,
Compras, Gastos, Costos fijos.

## Two mandatory checks
1. **Reconcile** `financials.json` annual Ventas to the workbook's selected-year monthly
   Ventas. If they differ, the parser mis-read — fix it before trusting the report.
2. The Estado de Resultados tab/section must **tie out** to what the client sees, and the
   Ratios `gross_margin` must equal the statement `margenBruto` (the adapter feeds COGS as
   `Ventas − Utilidad bruta` precisely so these reconcile).

## Data warnings
If a statement line has Excel error cells (`#REF!`, `#DIV/0!`), they're coerced to 0 and a
warning is emitted into `financials.json#warnings` and rendered in the report under
"Advertencias de datos" — so a misleading zero is never shown silently. Always read them.

## Scope
- xlsx-only here. `tn-only`/`merged` (Tienda Nube online data) is a later phase needing
  `tiendanube-store-data`.
- Ratios surface profitability/liquidity/efficiency only — leverage/market are suppressed
  (a private retailer has no debt/equity/market data). DCF off by default.
- Variance is period-over-period (the template carries no budget).

## Known limitations
- Error-cell (`#REF!`) warnings are detected on the **income statement** block only, and
  rely on openpyxl's cached values (`data_only=True`); a workbook saved without cached
  error strings may read those cells as blank → 0 with no warning. Eyeball the statement.
- Forecast scenario deltas use built-in base/bull/bear defaults; the `finance.scenarios`
  config knob is not yet wired through. `forecastPeriods` and cost inputs are honored.

See `reference/financials.schema.md` for the canonical data contract.
