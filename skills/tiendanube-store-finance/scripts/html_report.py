"""Branded HTML for the finance report. Rendered to PDF by render.sh."""
import html as _html

def _money(v, sym="$"):
    try: return f"{sym}{float(v):,.0f}"
    except Exception: return str(v)

def _row(label, cells):
    tds = "".join(f"<td class='r'>{c}</td>" for c in cells)
    return f"<tr><td>{_html.escape(label)}</td>{tds}</tr>"

def build_html(fin, results, cfg):
    brand = cfg.get("brand", {})
    name = brand.get("name", fin.get("storeName") or "Cliente")
    accent = brand.get("accent", "#222")
    sym = brand.get("currencySymbol", "$")
    a = fin["incomeStatement"]["annual"]; m = fin["incomeStatement"]["monthly"]
    months = fin["months"]
    rows = ["ventas","costoReposicion","utilidadBruta","costosFijos",
            "utilidadOperativa","utilidadNeta"]
    label = {"ventas":"Ventas","costoReposicion":"Costo reposición",
             "utilidadBruta":"Utilidad bruta","costosFijos":"Costos fijos",
             "utilidadOperativa":"Utilidad operativa","utilidadNeta":"Utilidad neta"}
    is_rows = "".join(_row(label[k], [_money(x, sym) for x in m.get(k, [])] +
                            [f"<b>{_money(a.get(k,0), sym)}</b>"]) for k in rows)
    ratios = "".join(f"<tr><td>{_html.escape(k)}</td><td class='r'>{v:.2f}</td></tr>"
                     for k, v in (results.get("ratios") or {}).items())
    warns = fin.get("warnings") or []
    warn_html = ("<h2>Advertencias de datos</h2><ul>" +
                 "".join(f"<li class='note'>{_html.escape(w)}</li>" for w in warns) +
                 "</ul>") if warns else ""
    active = fin.get("activeMonths")
    ann = fin.get("annualizedVentas")
    ytd_note = (f"<p class='note'>Período con datos: {active} meses de "
                f"{fin.get('year','')} (YTD). Ventas anualizadas (run-rate): "
                f"{_money(ann, sym)}.</p>") if active else ""
    head_months = "".join(f"<th class='r'>{mo}</th>" for mo in months) + "<th class='r'>Anual</th>"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
      :root {{ --accent: {accent}; }}
      body {{ font-family: -apple-system, Helvetica, Arial, sans-serif; color:#1a1a1a; margin:18mm; }}
      h1 {{ color: var(--accent); }} h2 {{ border-bottom:2px solid var(--accent); padding-bottom:2mm; }}
      table {{ border-collapse:collapse; width:100%; font-size:11px; margin:3mm 0; }}
      td,th {{ border-bottom:1px solid #ddd; padding:2px 5px; }} .r {{ text-align:right; }}
      .note {{ color:#777; font-size:10px; }}
    </style></head><body>
      <h1>{_html.escape(name)} — Informe financiero</h1>
      <p class="note">Estados leídos del workbook del cliente (conciliados). Proyección, ratios y
      variación son agregados de Más Orden Más Ganancia — cifras prospectivas son <b>supuesto</b>.</p>
      <h2>Estado de Resultados</h2>
      <table><tr><th>Concepto</th>{head_months}</tr>{is_rows}</table>
      <p class="note">Margen bruto {a.get('margenBruto',0):.1%} · Margen neto {a.get('margenNeto',0):.1%}</p>
      {ytd_note}
      <h2>Ratios</h2><table><tr><th>Ratio</th><th class="r">Valor</th></tr>{ratios}</table>
      {warn_html}
    </body></html>"""
