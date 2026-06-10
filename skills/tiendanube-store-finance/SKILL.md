---
name: tiendanube-store-finance
description: Use when turning a retail client's physical-store accounting workbook (the "Más Orden Más Ganancia" multi-sheet .xlsx) into a contador-grade, Argentina-aware financial report — reads the already-computed statements (Estado de Resultados / Flujos de Dinero / Punto de equilibrio), reexpresses them to moneda de cierre (IPC INDEC), models the fiscal position (Monotributo / Responsable Inscripto), surfaces quantified action levers, and outputs a branded .xlsx + PDF. xlsx-only mode (no Tienda Nube needed). Spanish/AR retail, es-AR contador register.
---

# Tienda Nube Store Finance (xlsx-only, contador-grade, AR-aware)

Turn a client's accounting workbook into a branded financial report a **contador can
audit**. The pipeline **reads** the workbook's already-computed statements and reconciles
to them — never recomputes — then **augments** in four layers, all in es-AR accounting
register:

1. **Reexpresión a moneda de cierre** — deflates the P&L to closing-month pesos via the
   bundled IPC INDEC series (real vs nominal). This homogenizes the income statement; it is
   **not** a full RT 6 ajuste and does **not** compute RECPAM (no balance sheet).
2. **Posición fiscal** (regime-aware) — Monotributo (cuota + nominal techo proximity) or
   Responsable Inscripto (IVA débito/crédito posición, IIBB, Ganancias **estimación**).
   Computed on **nominal** pesos (AFIP basis).
3. **Palancas / Acciones** — quantified, prioritized recommendations, each tied to the
   figure that triggered it, in real terms. **Not additive** — never summed.
4. **Forecast, ratios, variance** — forward projection + ratio suite + period-over-period.

## Prerequisites
- `python3` with **openpyxl** + a PDF renderer (Chrome/Edge/Chromium).
- Install deps from PUBLIC PyPI — this machine's pip is pinned to a private index, so the
  explicit index is REQUIRED:
  `python3 -m pip install --user --index-url https://pypi.org/simple/ openpyxl`

## Workflow
Scripts live in this skill's `scripts/`. From a working dir:
```bash
SKILL_DIR="<base directory printed when this skill loads>"
cp "$SKILL_DIR"/scripts/report.config.example.json report.config.json   # edit brand + finance + fiscal
python3 "$SKILL_DIR"/scripts/analyze_finance.py "<client-workbook>.xlsx" --config report.config.json --out .
"$SKILL_DIR"/scripts/render.sh report.html store-finance.pdf
```
Pipeline order (an invariant — do not reorder): **parse → fiscal (nominal) → reexpresión
(last) → gates → render**. Outputs: `financials.json` (schema 2.0), `store-finance.xlsx`
(tabs: Resumen, Estado de Resultados, Reexpresión, Flujo de Caja, Posición fiscal,
Variación, Palancas, Ratios, Proyección, Supuestos, Advertencias), `report.html` →
`store-finance.pdf`.

**Deep per-store layout** (full project under `~/Desktop/Projects/<store>/reports/` with
`scripts/ data/ sources/ deliverables/` — see the `tiendanube-stores` skill):
`analyze_finance.py` is `--out`-driven and `render.sh` takes `[in] [out]`, so no code
change — just target the subfolders. Keep `report.config.json` + the client workbook at the
`reports/` root and run from there:
```bash
cd ~/Desktop/Projects/<store>/reports
python3 scripts/analyze_finance.py "<client-workbook>.xlsx" --config report.config.json --out data
mv data/store-finance.xlsx deliverables/ ; mv data/report.html sources/
scripts/render.sh sources/report.html deliverables/store-finance.pdf
```

## Configuration (`report.config.json`)
```jsonc
{ "brand": { "name": "...", "accent": "#6B2532", "accentWarm": "#B08858",
             "currencySymbol": "$", "preparedFor": "..." },
  "finance": {
    "baseMonth": "2026-04",            // moneda de cierre; default = closing month of the window
    "projectedMonthlyInflation": 0.03, // forecast months only (real-terms projection)
    "forecastPeriods": 12,
    "umbrales": { "proximidadMonotributo": 0.85, "margenSeguridad": 0.15 },
    "enableDcf": false },
  "fiscal": {
    "regimen": "monotributo" | "responsable_inscripto",
    "categoriaMonotributo": "H",        // monotributo
    "alicuotaIIBB": 0.035, "alicuotaIVAVentas": 0.21,
    "alicuotaEfectivaGanancias": 0.30, "proporcionComprasGravadas": 1.0 } }  // RI
```
If `fiscal` is omitted the fiscal layer is skipped (regimen recorded as null) — the rest
of the report still runs.

## The report
Branded editorial PDF (Bodoni Moda + Archivo, SVG charts), sections:
cover → **00** Resumen ejecutivo → **01** Estado de Resultados (mensual + **YTD Nominal /
YTD Real** + cascada) → **02** Reexpresión a moneda de cierre (dual nominal/real, crecimiento
real vs nominal) → **03** Rentabilidad y costos → **04** Caja y flujo de fondos → **05**
Punto de equilibrio → **06** Posición fiscal → **07** Proyección y escenarios → **08**
Variación mensual → **09** Palancas / Acciones (tornado, no total) → **10** Ratios → **11**
Conclusiones → **12** Supuestos y notas. Every non-`fact` figure carries a **provenance
mark**: `ʳ` reexpresado · `ᵗ` impuesto modelado · `ˢ` supuesto · `ᵖ` inflación proyectada;
the legend is in Supuestos.

## Canonical model (schema 2.0)
Every monetary figure is a **measure** `{nominal, real, source, transforms[]}` — see
`reference/financials.schema.md`. Read money via `measures.nom()` / `real_or_nom()`. `real`
is filled by the restatement layer (`null` until then, or where IPC coverage is missing).

## Bundled reference data (`reference/`, versioned — print/verify before relying on it)
- `ipc-indec.json` — IPC INDEC nivel general mensual (`lastUpdated`, `vigenciaHasta`).
- `tablas-fiscales-ar.json` — Monotributo escalas (techos + cuota) + IIBB defaults.
- `glosario-contable-ar.md` — canonical es-AR terms (CMV, Resultado bruto/operativo/neto…).
If the analyzed/forecast period extends past `vigenciaHasta`, a warning is emitted — refresh
the table from INDEC / ARCA.

## Mandatory gates (`gates.py`, run before render — hard failures raise)
1. **Tie-out** — nominal Estado de Resultados ties to the workbook (≤ $1 / ≤ 0.1%).
2. **Composición** — no figure reexpressed twice (transforms deduped).
3. **Reexpresión** — `baseMonth` present (else warning, report stays nominal).
4. **Fiscal** — `fiscal` block present with a `regimen` key.
Plus restatement degrades any month missing from the IPC series to `real=null` + a warning,
and `apply_fiscal` hard-errors if Monotributo facturación exceeds the máximo techo (excluido).

## Honesty principles (the contador test)
The report never presents an **estimación as a liquidación** (Ganancias is an alícuota-efectiva
estimate), a **nominal gain as a real one** (reexpresión shows both; annual real is withheld
when IPC coverage is incomplete — never a partial sum vs a full-year nominal), a **pass-through
tax as a cost** (IVA posición is a flujo fiscal, not a Resultado line), or a **sum of
overlapping levers as a total** (palancas are non-additive). What the data can't support —
RECPAM, full Ganancias liquidation, Convenio Multilateral IIBB — is named out of scope, not
faked.

## Two mandatory checks (before trusting a report)
1. **Reconcile** `financials.json` annual Ventas to the workbook's selected-year monthly
   Ventas. If they differ, the parser mis-read — fix before trusting the report.
2. The Estado de Resultados tab/section must **tie out** to what the client sees (gate 1
   enforces the nominal column; reexpresión only adds a column, never touches the tie-out).

## Scope
- xlsx-only here. `tn-only`/`merged` (Tienda Nube online data) is a later phase needing
  `tiendanube-store-data`.
- Ratios surface profitability/liquidity/efficiency only — leverage/market suppressed.
- DCF off by default (`finance.enableDcf`); reexpresión is income-statement only (no RECPAM);
  Ganancias is an estimate; IIBB single-jurisdicción (Convenio Multilateral out).

See `reference/financials.schema.md` and `reference/glosario-contable-ar.md`.
