# financials.json (schemaVersion 1.0)

Canonical, read-not-recomputed financials from the accounting workbook.

- `schemaVersion` "1.0"
- `source` "workbook" | "tn" | "merged"
- `storeName` string | null
- `currency` string (e.g. "ARS")
- `months` array of month names actually present (≤12)
- `incomeStatement.monthly` arrays (one per month) for: ventas, costoReposicion,
  comisiones, utilidadBruta, costosFijos, amortizacion, utilidadOperativa,
  gastosVariables, utilidadNeta
- `incomeStatement.annual` summed lines + `margenBruto`, `margenNeto` (ratios)
- `cashFlow.monthly` ingresos / egresos / total arrays
- `breakEven.margenBrutoMonthly` array (may be empty)
- `balanceSheetPartial` inventory / accountsReceivable / accountsPayable (null if absent)
- `drivers.topProducts` [{name, units, price}]
- `warnings` array of strings — statement lines that had Excel error cells (e.g. `#REF!`)
  and were coerced to 0; the report MUST surface these so a misleading zero isn't shown silently

Consumers MUST check `schemaVersion` and fail loudly on an unsupported major.
