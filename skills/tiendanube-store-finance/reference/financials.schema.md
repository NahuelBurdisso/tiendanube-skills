# financials.json (schemaVersion 2.0)

Canonical, read-not-recomputed financials from the accounting workbook.

## Version history

| Version | Notes |
|---------|-------|
| 1.0 | Original flat arrays. Money lines were raw scalars. |
| 2.0 | Money lines are `Measure` objects `{nominal, real, source, transforms[]}`. Margins remain scalar ratios. `baseMonth` field added for restatement layer. Consumers MUST check `schemaVersion` and **fail loudly on an unsupported major version**. |

---

## Top-level fields

- `schemaVersion` `"2.0"` — semver string; consumers must reject unknown major versions.
- `source` `"workbook"` | `"tn"` | `"merged"`
- `storeName` string | null
- `currency` string (e.g. `"ARS"`)
- `baseMonth` string (`"YYYY-MM"`) | null — the *moneda de cierre* used for real-peso reexpresion. `null` until the restatement layer fills it in; consumers must treat money `.real` as `null` when `baseMonth` is null.
- `months` array of month names actually present in the workbook (≤ 12)
- `year` int | null — the analysis year selected from a multi-year workbook (latest year with data)
- `warnings` array of strings — data-quality and methodology warnings the report **MUST** surface: statement lines with Excel error cells (e.g. `#REF!`) or non-numeric text coerced to 0, months missing from the IPC series (real degraded to `null`), reexpresión unavailable (`baseMonth` null), fiscal-table vigencia exceeded, fiscal layer skipped, etc.

---

## Measure type

Every money line in `incomeStatement.monthly` and `incomeStatement.annual` is a **Measure** object:

```jsonc
{
  "nominal": 123456.78,      // ARS at the period's own price level (never null if data exists)
  "real": 98765.43,          // ARS at baseMonth price level (null when baseMonth is null)
  "source": "fact",          // origin of the nominal value: "fact" (read from workbook) | "derived"
  "transforms": []           // ordered, deduped transform tags: "restated" | "projected"
}
```

Margin and ratio fields (e.g. `margenBruto`, `margenNeto`) remain **scalar ratios** (0–1), not Measures.

### Consumer API (pseudo-code)

```python
def nom(measure):
    """Return the nominal value; raise if schema is unsupported."""
    return measure["nominal"]

def real_or_nom(measure, base_month):
    """Return real value if available, otherwise fall back to nominal."""
    if base_month is not None and measure.get("real") is not None:
        return measure["real"]
    return measure["nominal"]
```

Consumers **MUST**:
1. Read `schemaVersion`, parse the major component, and raise `UnsupportedSchemaVersion` (or equivalent) when the major version is unknown (e.g. major > 2).
2. Access money values only through `nom()` / `real_or_nom()` — never index `["nominal"]` directly in business logic, so that future measure shapes can be adapted in one place.
3. Treat `real` as unavailable when `baseMonth` is null; never display a `null` real value as if it were zero.

---

## incomeStatement.monthly

Arrays of **Measure** objects, one entry per month in `months` order:

- `ventas` — ventas netas
- `costoReposicion` — costo de la mercadería vendida (CMV)
- `comisiones` — comisiones y gastos variables de venta
- `utilidadBruta` — resultado bruto
- `costosFijos` — costos fijos del período
- `amortizacion` — amortizaciones / depreciaciones
- `utilidadOperativa` — resultado operativo (EBIT)
- `gastosVariables` — otros gastos variables no incluidos en comisiones
- `utilidadNeta` — resultado neto

## incomeStatement.annual

Summed Measure objects for the year + scalar ratio fields:

- All monthly Measure lines summed across the year.
- `margenBruto` — scalar ratio (0–1): `utilidadBruta.nominal / ventas.nominal`
- `margenNeto` — scalar ratio (0–1): `utilidadNeta.nominal / ventas.nominal`

## incomeStatement.annualFromWorkbook

`{lineKey: number}` | null — the workbook's **own TOTAL/Anual column**, captured when the month-header row carries a TOTAL/Anual header right after the last month (and the analyzed window spans the whole block). Used by the tie-out gate as the real reconciliation reference; `null` when the workbook has no such column.

## cashFlow

`cashFlow.monthly` — ingresos / egresos / total arrays of **Measure** objects, restated by the reexpresión layer like the income statement (`real` filled when IPC coverage allows).

## breakEven (planned — Measure migration pending)

`breakEven.margenBrutoMonthly` array (may be empty). Will become Measures in a future plan; currently scalar forward-compatible with schema 1.0.

## balanceSheetPartial

`inventory` / `accountsReceivable` / `accountsPayable` — Measure objects | null if absent from workbook.

## drivers

`drivers.topProducts` — `[{name, units, price}]` — `price` is a Measure.

---

## Upgrade path from 1.0

The adapter layer (`scripts/adapters.py`) is responsible for wrapping 1.0 scalars into Measure objects with `real: null` and `transforms: []` before passing to downstream consumers. Consumers must never receive raw 1.0 payloads.
