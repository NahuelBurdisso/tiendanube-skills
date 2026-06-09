"""Expert financial report (Spanish, editorial-financial) rendered to PDF by render.sh.
Reads the workbook's statements (reconciled) and layers forecast/ratios/variance
analysis with charts and a computed narrative. build_html(fin, results, cfg) -> HTML."""
import html as _html
import charts as ch

_CSS = """
:root{--bg:#F4EFE6;--surface:#FBF8F2;--deep:#EAE2D4;--text:#2A211A;--ink:#1A1512;
--muted:#61574A;--accent:__ACCENT__;--warm:__WARM__;--line:#D9CFBE;
--good:#3F6B4A;--warn:#9A6B1E;--bad:#8C2D2D}
*{box-sizing:border-box;margin:0;padding:0}@page{size:A4;margin:18mm 0 15mm 0}
html{-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{font-family:'Archivo',sans-serif;color:var(--text);background:var(--bg);font-size:10.2px;line-height:1.55}
.page{padding:0 18mm}
h1,h2,h3,h4{font-family:'Bodoni Moda',serif;font-weight:500;letter-spacing:-.01em;color:var(--ink)}
.label{text-transform:uppercase;letter-spacing:.22em;font-size:8px;font-weight:600;color:var(--muted)}
.accent{color:var(--accent)}.warm{color:var(--warm)}
.cover{height:261mm;display:flex;flex-direction:column;justify-content:space-between;padding:24mm 18mm;page-break-after:always;position:relative}
.cover .wordmark{font-family:'Bodoni Moda';font-weight:600;font-size:13px;letter-spacing:.5em;text-transform:uppercase}
.cover .rule{height:1px;background:var(--line);margin:6mm 0}
.cover h1{font-size:50px;line-height:1.05;margin-top:auto}.cover h1 .it{font-style:italic;color:var(--accent)}
.cover .sub{font-size:12.5px;color:var(--muted);margin-top:8mm;max-width:130mm;line-height:1.6}
.cover .meta{margin-top:13mm;display:flex;gap:13mm}
.cover .bigstat{position:absolute;right:18mm;top:56mm;text-align:right}
.cover .bigstat .n{font-family:'Bodoni Moda';font-size:46px;color:var(--accent);line-height:1}
.cover .bigstat .c{font-size:8.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-top:1mm}
.section-open{page-break-before:always;padding-top:6mm}
.kicker{display:flex;align-items:center;gap:8px;margin-bottom:4mm}
.kicker .num{font-family:'Bodoni Moda';font-size:13px;color:var(--accent)}
h2.report{font-size:27px;line-height:1.06;margin-bottom:3mm}
.lede{font-size:11px;color:var(--muted);max-width:158mm;line-height:1.62;margin-bottom:5mm}
h3{font-size:14px;margin:7mm 0 3mm;padding-bottom:2mm;border-bottom:1px solid var(--line)}
h3 .label{float:right;padding-top:4px}
p{margin-bottom:2.5mm}.note{color:var(--muted)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:3mm;margin:4mm 0 5mm}
.stat{background:var(--surface);border:1px solid var(--line);padding:4mm}
.stat .n{font-family:'Bodoni Moda';font-size:19px;color:var(--ink);line-height:1}.stat .n.accent{color:var(--accent)}
.stat .c{font-size:8.2px;color:var(--muted);margin-top:2mm;line-height:1.4}
table{width:100%;border-collapse:collapse;margin:3mm 0 5mm;font-size:9.3px}
th{text-align:left;font-weight:600;text-transform:uppercase;letter-spacing:.07em;font-size:7.8px;color:var(--muted);border-bottom:1.5px solid var(--ink);padding:2mm 2mm}
td{padding:2.2mm 2mm;border-bottom:1px solid var(--line);vertical-align:top}tr{page-break-inside:avoid}
td.r,th.r{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tr.sub td{border-top:1.5px solid var(--ink);font-weight:600}
tr.tot td{border-top:2px solid var(--ink);font-weight:700;background:var(--deep)}
.pill{display:inline-block;padding:1px 6px;border-radius:10px;font-size:7.4px;font-weight:600;letter-spacing:.04em;text-transform:uppercase}
.p-bad{background:#f3dede;color:var(--bad)}.p-warn{background:#f3e7d0;color:var(--warn)}.p-good{background:#dfe9e0;color:var(--good)}.p-info{background:var(--deep);color:var(--text)}
.callout{background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--accent);padding:4mm 5mm;margin:4mm 0;page-break-inside:avoid}
.callout h4{font-size:12.5px;margin-bottom:2mm}
.chartbox{background:var(--surface);border:1px solid var(--line);padding:5mm;margin:3mm 0 5mm;page-break-inside:avoid}
.chartbox .ct{font-size:8px;letter-spacing:.13em;text-transform:uppercase;color:var(--muted);font-weight:600;margin-bottom:3mm}
svg.chart{width:100%;height:auto;display:block}
ul.check{list-style:none}ul.check li{position:relative;padding-left:7mm;margin-bottom:2.4mm;page-break-inside:avoid;line-height:1.55}
ul.check li:before{content:"—";position:absolute;left:0;color:var(--accent)}
.bignum{font-family:'Bodoni Moda';font-size:38px;color:var(--accent);line-height:1}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:5mm}
.footer-note{margin-top:8mm;padding-top:4mm;border-top:1px solid var(--line);font-size:8.1px;color:var(--muted)}
.warnbox{background:#f7efe0;border:1px solid #e3d2ad;border-left:3px solid var(--warn);padding:3mm 4mm;margin:3mm 0}
"""


def build_html(fin, results, cfg):
    brand = cfg.get("brand", {})
    name = brand.get("name", fin.get("storeName") or "TIENDA")
    accent = brand.get("accent", "#6B2532")
    warm = brand.get("accentWarm", "#B08858")
    sym = brand.get("currencySymbol", "$")
    locale = brand.get("locale", "es-AR")
    prepared = brand.get("preparedFor", "")
    NEG = "#8C2D2D"
    results = results or {}

    a = fin["incomeStatement"]["annual"]
    m = fin["incomeStatement"]["monthly"]
    months = fin.get("months", [])
    active = fin.get("activeMonths") or len(months)
    year = fin.get("year") or ""
    ann_ventas = fin.get("annualizedVentas", 0.0)
    esc = _html.escape

    def M(n):
        n = float(n or 0)
        x = abs(n)
        if x >= 1e6:
            return f"{sym}{n/1e6:.1f}".replace(".", ",") + "M"
        if x >= 1e3:
            return f"{sym}{round(n/1e3)}k"
        return f"{sym}{round(n)}"

    def P(x):
        return f"{x*100:.1f}%".replace(".", ",")

    # ---- derived analysis ----
    V = a.get("ventas", 0.0)
    cr = a.get("costoReposicion", 0.0)
    com = a.get("comisiones", 0.0)
    ub = a.get("utilidadBruta", 0.0)
    cf = a.get("costosFijos", 0.0)
    uo = a.get("utilidadOperativa", 0.0)
    un = a.get("utilidadNeta", 0.0)
    otros = max(0.0, uo - un)          # impuestos / amortización / otros (UO -> UN)
    mb = a.get("margenBruto", 0.0)
    mo = (uo / V) if V else 0.0
    mn = a.get("margenNeto", 0.0)
    scale = (12.0 / active) if active else 1.0   # YTD -> annualized
    cf_ann = cf * scale
    be_ventas = (cf_ann / mb) if mb else 0.0     # break-even anualizado
    seg = ((ann_ventas - be_ventas) / ann_ventas) if ann_ventas else 0.0  # margen de seguridad

    am = months[:active]
    v_ser = m.get("ventas", [])[:active]
    ub_ser = m.get("utilidadBruta", [])[:active]
    uo_ser = m.get("utilidadOperativa", [])[:active]
    un_ser = m.get("utilidadNeta", [])[:active]
    gm_ser = [(ub_ser[i] / v_ser[i]) if i < len(v_ser) and v_ser[i] else 0 for i in range(len(am))]
    om_ser = [(uo_ser[i] / v_ser[i]) if i < len(v_ser) and v_ser[i] else 0 for i in range(len(am))]
    nm_ser = [(un_ser[i] / v_ser[i]) if i < len(v_ser) and v_ser[i] else 0 for i in range(len(am))]

    # ---- charts ----
    rev_chart = ch.bars(v_ser, am, accent, warm, M,
                        highlight=(v_ser.index(max(v_ser)) if v_ser else None)) if v_ser else ""
    wf = ch.waterfall([
        ("Ventas", V, "start"), ("Costo repos.", cr, "neg"), ("Comisiones", com, "neg"),
        ("Util. bruta", ub, "total"), ("Costos fijos", cf, "neg"), ("Util. oper.", uo, "total"),
        ("Otros/imp.", otros, "neg"), ("Util. neta", un, "total"),
    ], accent, warm, NEG, M) if V else ""
    margin_chart = ch.lines([gm_ser, om_ser, nm_ser], am,
                            ["Margen bruto", "Margen operativo", "Margen neto"],
                            [accent, warm, "#3F6B4A"]) if am else ""
    cost_chart = ch.stacked_bar([
        ("Costo reposición", cr, accent), ("Comisiones", com, "#A8554F"),
        ("Costos fijos", cf, warm), ("Otros/imp.", otros, "#9A6B1E"),
        ("Utilidad neta", un, "#3F6B4A"),
    ]) if V else ""

    # ---- forecast / scenarios ----
    fc = results.get("forecast") or {}
    trend = (fc.get("trend_analysis") or {}).get("trend", {})
    avg_growth = (fc.get("trend_analysis") or {}).get("average_growth_rate", 0.0)
    scen = (fc.get("scenario_comparison") or {}).get("scenarios", {})
    scen_rows, scen_groups = "", []
    scen_label = {"base": "Base", "bull": "Optimista", "bear": "Conservador"}
    for key in ("bear", "base", "bull"):
        sc = scen.get(key)
        if not sc:
            continue
        periods = sc.get("forecast_periods", [])
        rev = sum(p.get("revenue", 0) for p in periods)
        oi = sum(p.get("operating_income", 0) for p in periods)
        scen_groups.append((scen_label[key], [rev]))
        scen_rows += (f'<tr><td><b>{scen_label[key]}</b><br><span class="note">'
                      f'crec. {P(sc.get("growth_rate",0))} · margen {P(sc.get("gross_margin",0))}</span></td>'
                      f'<td class="r">{M(rev)}</td><td class="r">{M(oi)}</td></tr>')
    horizon = len(next(iter(scen.values()), {}).get("forecast_periods", [])) if scen else 0
    scen_chart = ch.grouped_bars(scen_groups, ["Ventas proyectadas"], [warm], accent, M) if scen_groups else ""

    # ---- variance ----
    var_items = (results.get("variance") or {}).get("line_items", [])
    var_rows = ""
    for li in var_items:
        act, pri = li.get("actual", 0) or 0, li.get("prior_year", 0) or 0
        d = act - pri
        dp = (d / pri) if pri else 0
        cls = "p-good" if d >= 0 else "p-bad"
        if li.get("type") == "expense":
            cls = "p-good" if d < 0 else "p-warn"
        var_rows += (f'<tr><td>{esc(li.get("name",""))}</td><td class="r">{M(act)}</td>'
                     f'<td class="r">{M(pri)}</td><td class="r">{("+" if d>=0 else "−")}{M(abs(d))}</td>'
                     f'<td class="r"><span class="pill {cls}">{("+" if dp>=0 else "")}{P(dp)}</span></td></tr>')

    # ---- narrative insights (computed) ----
    def adj_margin(x):
        return "saludable" if x >= 0.40 else ("ajustado" if x >= 0.25 else "comprimido")
    ins = []
    ins.append(f"El negocio opera a un <b>run-rate anualizado de {M(ann_ventas)}</b> "
               f"(sobre {active} meses con datos de {year}), con un <b>margen bruto {adj_margin(mb)} de {P(mb)}</b>.")
    ins.append(f"Los <b>costos fijos consumen {P(cf/V if V else 0)}</b> de la facturación y comprimen el "
               f"margen operativo a <b>{P(mo)}</b>; tras impuestos y otros, el <b>margen neto queda en {P(mn)}</b>.")
    if be_ventas:
        ins.append(f"El <b>punto de equilibrio anualizado es {M(be_ventas)}</b> de ventas; el "
                   f"<b>margen de seguridad es {P(seg)}</b> — cuánto pueden caer las ventas antes de perder.")
    if trend:
        dirn = "alcista" if trend.get("direction") == "upward" else "bajista"
        r2 = str(round(trend.get("r_squared", 0), 2)).replace(".", ",")
        ins.append(f"La <b>tendencia de ventas es {dirn}</b> (R²={r2}), con un "
                   f"<b>crecimiento mensual promedio de {P(avg_growth)}</b>.")
    if var_items:
        vv = next((x for x in var_items if x.get("name") == "Ventas"), None)
        nn = next((x for x in var_items if x.get("name") == "Utilidad neta"), None)
        if vv and nn:
            dv = (vv["actual"] or 0) - (vv["prior_year"] or 0)
            dn = (nn["actual"] or 0) - (nn["prior_year"] or 0)
            ins.append(f"En el último mes las ventas {'subieron' if dv>=0 else 'bajaron'} {M(abs(dv))}, "
                       f"y la <b>utilidad neta {'mejoró' if dn>=0 else 'cayó'} {M(abs(dn))}</b> vs. el mes previo.")
    insights_html = "".join(f"<li>{x}</li>" for x in ins)

    warns = fin.get("warnings") or []
    warn_block = ("".join(f'<div class="warnbox note">⚠ {esc(w)}</div>' for w in warns)) if warns else ""

    # ---- income-statement table ----
    is_rows_def = [("ventas", "Ventas", "line"), ("costoReposicion", "(−) Costo reposición", "line"),
                   ("comisiones", "(−) Comisiones", "line"), ("utilidadBruta", "Utilidad bruta", "sub"),
                   ("costosFijos", "(−) Costos fijos", "line"), ("utilidadOperativa", "Utilidad operativa", "sub"),
                   ("utilidadNeta", "Utilidad neta", "tot")]
    head_m = "".join(f"<th class='r'>{mo}</th>" for mo in am)
    is_rows = ""
    for key, label, kind in is_rows_def:
        cells = "".join(f"<td class='r'>{M(x)}</td>" for x in m.get(key, [])[:active])
        cls = " class='sub'" if kind == "sub" else (" class='tot'" if kind == "tot" else "")
        is_rows += (f"<tr{cls}><td>{label}</td>{cells}<td class='r'><b>{M(a.get(key,0))}</b></td>"
                    f"<td class='r'>{M(a.get(key,0)*scale)}</td></tr>")

    def kicker(num, lab):
        return f'<div class="kicker"><span class="num">{num}</span><span class="label">{lab}</span></div>'

    head_period = f"{active} meses de {year} (YTD)"
    css = _CSS.replace("__ACCENT__", accent).replace("__WARM__", warm)
    prepared_html = (f'<div><span class="label">Para</span>'
                     f'<div style="font-size:12px;margin-top:2mm">{esc(prepared)}</div></div>') if prepared else ""
    scen_chart_html = (f'<div class="chartbox"><div class="ct">Ventas proyectadas próximos {horizon} meses — '
                       f'por escenario</div>{scen_chart}</div>') if scen_chart else '<p class="note">Proyección no disponible.</p>'
    scen_table_html = (f'<table><tr><th>Escenario</th><th class="r">Ventas {horizon}m</th>'
                       f'<th class="r">Resultado operativo</th></tr>{scen_rows}</table>') if scen_rows else ""
    var_table_html = (f'<table><tr><th>Concepto</th><th class="r">Actual</th><th class="r">Mes previo</th>'
                      f'<th class="r">Δ</th><th class="r">Δ%</th></tr>{var_rows}</table>') if var_rows else \
        '<p class="note">Variación no disponible (se requieren ≥2 meses con datos).</p>'
    warn_section = (('<h3>Advertencias de datos</h3><ul class="check">' +
                     "".join(f"<li>{esc(w)}</li>" for w in warns) + "</ul>")) if warns else ""

    html = f"""<!DOCTYPE html><html lang="{locale}"><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400;0,6..96,500;0,6..96,600;0,6..96,700;1,6..96,500&family=Archivo:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>{css}</style></head><body>

<div class="cover">
  <div><div class="wordmark">{esc(name)}</div><div class="rule"></div>
    <div class="label">Informe financiero · {head_period}</div></div>
  <div class="bigstat"><div class="n">{M(ann_ventas)}</div><div class="c">Run-rate anualizado</div>
    <div class="n" style="font-size:30px;margin-top:6mm">{P(mb)}</div><div class="c">Margen bruto</div></div>
  <div>
    <h1>Análisis financiero:<br>rentabilidad, costos y<br><span class="it">proyección</span>.</h1>
    <p class="sub">Lectura experta sobre los estados ya construidos del negocio: estructura de resultados,
    márgenes, punto de equilibrio, variación mensual y escenarios. Cada cifra concilia con el workbook del
    cliente; lo prospectivo se marca como supuesto.</p>
    <div class="meta">{prepared_html}
      <div><span class="label">Período</span><div style="font-size:12px;margin-top:2mm">{head_period}</div></div>
      <div><span class="label">Moneda</span><div style="font-size:12px;margin-top:2mm">{fin.get('currency','ARS')}</div></div>
    </div>
  </div>
</div>

<div class="page section-open">
  {kicker('00', 'Resumen ejecutivo')}
  <h2 class="report">La foto financiera, en una página.</h2>
  <p class="lede">Dónde está la rentabilidad del negocio, qué se la come y hacia dónde apunta. Los números
  salen del estado de resultados real; el análisis los interpreta.</p>
  <div class="stats">
    <div class="stat"><div class="n accent">{M(ann_ventas)}</div><div class="c">Run-rate anualizado · {M(V)} en {active} meses</div></div>
    <div class="stat"><div class="n">{P(mb)}</div><div class="c">Margen bruto</div></div>
    <div class="stat"><div class="n">{P(mo)}</div><div class="c">Margen operativo</div></div>
    <div class="stat"><div class="n accent">{P(mn)}</div><div class="c">Margen neto · {M(un)} netos</div></div>
  </div>
  {warn_block}
  <div class="callout"><h4>Lecturas clave</h4><ul class="check">{insights_html}</ul></div>
</div>

<div class="page section-open">
  {kicker('01', 'Estado de resultados')}
  <h2 class="report">De cada peso vendido, qué queda.</h2>
  <p class="lede">El estado de resultados mensual (conciliado con el workbook), su total del período y el
  valor anualizado. La cascada muestra cómo la facturación se convierte en utilidad neta.</p>
  <table><tr><th>Concepto</th>{head_m}<th class="r">YTD</th><th class="r">Anualiz.</th></tr>{is_rows}</table>
  <div class="chartbox"><div class="ct">Facturación mensual — pico en dorado</div>{rev_chart}</div>
  <div class="chartbox"><div class="ct">Cascada de resultados — Ventas → Utilidad neta</div>{wf}</div>
</div>

<div class="page section-open">
  {kicker('02', 'Rentabilidad y costos')}
  <h2 class="report">Márgenes y estructura de costos.</h2>
  <p class="lede">Cómo evolucionan los márgenes mes a mes y en qué se va cada peso de facturación.
  El peso de los costos fijos define la rentabilidad final.</p>
  <div class="chartbox"><div class="ct">Evolución de márgenes (% de ventas) por mes</div>{margin_chart}</div>
  <div class="chartbox"><div class="ct">Estructura de la facturación — a dónde va cada peso</div>{cost_chart}</div>
  <table>
    <tr><th>Componente</th><th class="r">{sym}/período</th><th class="r">% ventas</th><th>Lectura</th></tr>
    <tr><td>Costo de reposición (CMV)</td><td class="r">{M(cr)}</td><td class="r">{P(cr/V if V else 0)}</td><td>Costo directo de la mercadería vendida</td></tr>
    <tr><td>Comisiones</td><td class="r">{M(com)}</td><td class="r">{P(com/V if V else 0)}</td><td>Costo variable de venta</td></tr>
    <tr class="sub"><td>Utilidad bruta</td><td class="r">{M(ub)}</td><td class="r">{P(mb)}</td><td>Margen de contribución</td></tr>
    <tr><td>Costos fijos</td><td class="r">{M(cf)}</td><td class="r">{P(cf/V if V else 0)}</td><td>Estructura — no varía con la venta</td></tr>
    <tr class="tot"><td>Utilidad neta</td><td class="r">{M(un)}</td><td class="r">{P(mn)}</td><td>Resultado final del período</td></tr>
  </table>
</div>

<div class="page section-open">
  {kicker('03', 'Punto de equilibrio')}
  <h2 class="report">Cuánto hay que vender para no perder.</h2>
  <p class="lede">El punto de equilibrio es la facturación que cubre exactamente los costos fijos al margen
  bruto actual. Por encima, cada peso aporta utilidad; por debajo, se pierde.</p>
  <div class="grid2">
    <div><div class="bignum">{M(be_ventas)}</div><p class="note">Punto de equilibrio anualizado, a un margen bruto de {P(mb)}.</p></div>
    <div><div class="bignum">{P(seg)}</div><p class="note">Margen de seguridad: cuánto pueden caer las ventas antes de entrar en pérdida.</p></div>
  </div>
  <div class="callout"><h4>Cómo leerlo</h4>
    <p class="note">Con costos fijos anualizados de <b>{M(cf_ann)}</b> y un margen bruto de <b>{P(mb)}</b>,
    el negocio necesita facturar <b>{M(be_ventas)}/año</b> para cubrir su estructura. Hoy factura a un ritmo de
    <b>{M(ann_ventas)}/año</b>, {'por encima' if ann_ventas>=be_ventas else 'por debajo'} del equilibrio.</p></div>
</div>

<div class="page section-open">
  {kicker('04', 'Proyección y escenarios')}
  <h2 class="report">Hacia dónde va el negocio.</h2>
  <p class="lede">Proyección construida sobre la tendencia y estacionalidad reales de los {active} meses con
  datos. Tres escenarios acotan el rango. <span class="note">Cifras prospectivas: supuesto.</span></p>
  {scen_chart_html}
  {scen_table_html}
</div>

<div class="page section-open">
  {kicker('05', 'Variación mensual')}
  <h2 class="report">Qué cambió respecto al mes anterior.</h2>
  <p class="lede">Variación período contra período (último mes con datos vs. el previo). El workbook no lleva
  presupuesto, por lo que la comparación es mes contra mes, no contra objetivo.</p>
  {var_table_html}
</div>

<div class="page section-open">
  {kicker('06', 'Supuestos y datos')}
  <h2 class="report">Origen de los números y supuestos.</h2>
  <p class="lede">Para que cada cifra sea defendible: de dónde sale y qué se asumió.</p>
  <h3>Origen de los datos</h3>
  <ul class="check">
    <li>Los <b>estados se leen</b> del workbook del cliente (Estado de Resultados, Flujos de Dinero, Punto de
    equilibrio) y se <b>concilian</b>: el informe no recalcula, reproduce.</li>
    <li>Se analiza el <b>año {year}</b>, ventana de <b>{active} meses con datos</b>. El "anualizado" proyecta
    el ritmo a 12 meses.</li>
    <li>El <b>margen bruto</b> usa el costo efectivo (Ventas − Utilidad bruta), por lo que concilia con el
    estado de resultados e incluye comisiones.</li>
    <li>La <b>proyección</b> y los escenarios son prospectivos: <b>supuesto</b>, no ingreso garantizado.</li>
  </ul>
  {warn_section}
  <div class="footer-note">{esc(name)} · Informe financiero sobre el workbook del cliente · período {head_period}.
  Estados conciliados; proyección y ratios son estimaciones con supuestos explícitos.</div>
</div>

</body></html>"""
    return html
