"""Expert financial report (Spanish, editorial-financial) rendered to PDF by render.sh.
Reads the workbook's statements (reconciled) and layers cash, profitability, break-even,
forecast/scenarios, variance and computed recommendations. build_html(fin, results, cfg)."""
import html as _html
import charts as ch
from measures import nom
from provenance import marks, legend

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
.accent{color:var(--accent)}.warm{color:var(--warm)}.bad{color:var(--bad)}.good{color:var(--good)}
.cover{height:261mm;display:flex;flex-direction:column;justify-content:space-between;padding:24mm 18mm;page-break-after:always;position:relative}
.cover .wordmark{font-family:'Bodoni Moda';font-weight:600;font-size:13px;letter-spacing:.5em;text-transform:uppercase}
.cover .rule{height:1px;background:var(--line);margin:6mm 0}
.cover h1{font-size:49px;line-height:1.05;margin-top:auto}.cover h1 .it{font-style:italic;color:var(--accent)}
.cover .sub{font-size:12.5px;color:var(--muted);margin-top:8mm;max-width:130mm;line-height:1.6}
.cover .meta{margin-top:13mm;display:flex;gap:13mm}
.cover .bigstat{position:absolute;right:18mm;top:54mm;text-align:right}
.cover .bigstat .n{font-family:'Bodoni Moda';font-size:44px;color:var(--accent);line-height:1}
.cover .bigstat .c{font-size:8.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-top:1mm}
.section-open{padding-top:9mm}
.section-open.brk{page-break-before:always;padding-top:6mm}
.kicker{display:flex;align-items:center;gap:8px;margin-bottom:4mm;page-break-after:avoid}
.kicker .num{font-family:'Bodoni Moda';font-size:13px;color:var(--accent)}
h2.report{font-size:26px;line-height:1.07;margin-bottom:3mm;page-break-after:avoid}
.lede{font-size:11px;color:var(--muted);max-width:160mm;line-height:1.62;margin-bottom:5mm;page-break-after:avoid}
h3{font-size:13.5px;margin:6mm 0 3mm;padding-bottom:2mm;border-bottom:1px solid var(--line)}
p{margin-bottom:2.5mm}.note{color:var(--muted)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:3mm;margin:4mm 0 5mm}
.stat{background:var(--surface);border:1px solid var(--line);padding:4mm}
.stat .n{font-family:'Bodoni Moda';font-size:19px;color:var(--ink);line-height:1}.stat .n.accent{color:var(--accent)}
.stat .c{font-size:8.2px;color:var(--muted);margin-top:2mm;line-height:1.4}
table{width:100%;border-collapse:collapse;margin:3mm 0 5mm;font-size:9.2px}
th{text-align:left;font-weight:600;text-transform:uppercase;letter-spacing:.07em;font-size:7.6px;color:var(--muted);border-bottom:1.5px solid var(--ink);padding:1.8mm 1.8mm}
td{padding:2mm 1.8mm;border-bottom:1px solid var(--line);vertical-align:top}tr{page-break-inside:avoid}
td.r,th.r{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tr.sub td{border-top:1.5px solid var(--ink);font-weight:600}
tr.tot td{border-top:2px solid var(--ink);font-weight:700;background:var(--deep)}
.pill{display:inline-block;padding:1px 6px;border-radius:10px;font-size:7.2px;font-weight:600;letter-spacing:.04em;text-transform:uppercase}
.p-bad{background:#f3dede;color:var(--bad)}.p-warn{background:#f3e7d0;color:var(--warn)}.p-good{background:#dfe9e0;color:var(--good)}.p-info{background:var(--deep);color:var(--text)}
.callout{background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--accent);padding:4mm 5mm;margin:4mm 0;page-break-inside:avoid}
.callout.warm{border-left-color:var(--warm)}.callout.bad{border-left-color:var(--bad)}
.callout h4{font-size:12.5px;margin-bottom:2mm}
.chartbox{background:var(--surface);border:1px solid var(--line);padding:5mm;margin:3mm 0 5mm;page-break-inside:avoid}
.chartbox .ct{font-size:8px;letter-spacing:.13em;text-transform:uppercase;color:var(--muted);font-weight:600;margin-bottom:3mm}
svg.chart{width:100%;height:auto;display:block}
ul.check{list-style:none}ul.check li{position:relative;padding-left:7mm;margin-bottom:2.6mm;page-break-inside:avoid;line-height:1.55}
ul.check li:before{content:"—";position:absolute;left:0;color:var(--accent)}
.bignum{font-family:'Bodoni Moda';font-size:36px;color:var(--accent);line-height:1}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:6mm;align-items:start}
.rec td:first-child{font-weight:600}
.footer-note{margin-top:8mm;padding-top:4mm;border-top:1px solid var(--line);font-size:8.1px;color:var(--muted)}
.warnbox{background:#f7efe0;border:1px solid #e3d2ad;border-left:3px solid var(--warn);padding:3mm 4mm;margin:3mm 0}
"""


def _rebound_month(values, labels):
    """Name of the month whose positive jump dominates the period's growth (> 50% of
    the sum of positive deltas) — the 'rebound' that inflates average growth. None
    when growth is broad-based or there is no positive delta."""
    deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
    pos = [d for d in deltas if d > 0]
    if not pos:
        return None
    mx = max(pos)
    if mx <= 0.5 * sum(pos):
        return None
    return labels[deltas.index(mx) + 1]


def _losses_at_start(loss_idx, n):
    """True when every loss month sits at the START of the window (so 'recién fue
    rentable en los últimos' is accurate) and at least one later month is profitable."""
    return bool(loss_idx) and loss_idx == list(range(len(loss_idx))) and len(loss_idx) < n


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
    esc = _html.escape

    a = fin["incomeStatement"]["annual"]
    m = fin["incomeStatement"]["monthly"]
    months = fin.get("months", [])
    active = fin.get("activeMonths") or len(months)
    year = fin.get("year") or ""
    ann_ventas = fin.get("annualizedVentas", 0.0)

    def M(n):
        n = float(n or 0)
        x, sign = abs(n), ("−" if n < 0 else "")
        if x >= 1e6:
            return f"{sign}{sym}{x/1e6:.1f}".replace(".", ",") + "M"
        if x >= 1e3:
            return f"{sign}{sym}{round(x/1e3)}k"
        return f"{sign}{sym}{round(x)}"

    def P(x):
        return f"{x*100:.1f}%".replace(".", ",")

    # ---- statement figures (all read, never recomputed) ----
    V = nom(a.get("ventas", 0.0))
    cr = nom(a.get("costoReposicion", 0.0))
    com = nom(a.get("comisiones", 0.0))
    ub = nom(a.get("utilidadBruta", 0.0))
    cf = nom(a.get("costosFijos", 0.0))
    amort = nom(a.get("amortizacion", 0.0))
    uo = nom(a.get("utilidadOperativa", 0.0))
    gv = nom(a.get("gastosVariables", 0.0))
    un = nom(a.get("utilidadNeta", 0.0))
    mb = a.get("margenBruto", 0.0)
    mo = (uo / V) if V else 0.0
    mn = a.get("margenNeto", 0.0)
    scale = (12.0 / active) if active else 1.0
    fixed_ann = (cf + amort) * scale                 # fixed pool incl. amortización
    # Break-even / margen de seguridad come from the MODEL (financials.py reads the workbook's
    # "Facturación necesaria" and only sets margenSeguridad when it exists — never a fake 100%).
    # If absent, render n/d rather than recompute an unreconciled figure (would contradict the
    # silent colchón lever and the model's margenSeguridad=None).
    be_model = fin.get("breakEven", {}) or {}
    ms_model = be_model.get("margenSeguridad")
    if ms_model is not None:
        seg_known = True
        seg = ms_model
        be_ventas = be_model.get("facturacionEquilibrioAnual") or 0.0
        seg_pesos = V - be_ventas
    else:
        seg_known = False
        seg = 0.0
        be_ventas = 0.0
        seg_pesos = 0.0

    am = months[:active]
    v_ser = [nom(x) for x in m.get("ventas", [])[:active]]
    ub_ser = [nom(x) for x in m.get("utilidadBruta", [])[:active]]
    uo_ser = [nom(x) for x in m.get("utilidadOperativa", [])[:active]]
    un_ser = [nom(x) for x in m.get("utilidadNeta", [])[:active]]
    gm_ser = [(ub_ser[i] / v_ser[i]) if i < len(v_ser) and v_ser[i] else 0 for i in range(len(am))]
    om_ser = [(uo_ser[i] / v_ser[i]) if i < len(v_ser) and v_ser[i] else 0 for i in range(len(am))]
    nm_ser = [(un_ser[i] / v_ser[i]) if i < len(v_ser) and v_ser[i] else 0 for i in range(len(am))]
    loss_idx = [i for i in range(len(am)) if i < len(un_ser) and un_ser[i] < 0]
    loss_months = [am[i] for i in loss_idx]

    # ---- cash flow (from Flujos de Dinero) ----
    cf_total = [nom(x) for x in (fin.get("cashFlow", {}).get("monthly", {}).get("total", []) or [])[:active]]
    cf_in = [nom(x) for x in (fin.get("cashFlow", {}).get("monthly", {}).get("ingresos", []) or [])[:active]]
    cum, run = [], 0.0
    for x in cf_total:
        run += x
        cum.append(run)
    cash_end = cum[-1] if cum else 0.0
    cash_trough = min(cum) if cum else 0.0
    trough_month = am[cum.index(cash_trough)] if cum else ""
    has_cash = any(cf_total)

    # ---- charts ----
    rev_chart = ch.bars(v_ser, am, accent, warm, M,
                        highlight=(v_ser.index(max(v_ser)) if v_ser else None), h=104) if v_ser else ""
    wf = ch.waterfall([
        ("Ventas", V, "start"), ("Costo repos.", cr, "neg"), ("Comisiones", com, "neg"),
        ("Util. bruta", ub, "total"), ("Costos fijos", cf, "neg"), ("Amortización", amort, "neg"),
        ("Util. oper.", uo, "total"), ("Gastos var.", gv, "neg"), ("Util. neta", un, "total"),
    ], accent, warm, NEG, M, h=150) if V else ""
    margin_chart = ch.lines([gm_ser, om_ser, nm_ser], am,
                            ["Margen bruto", "Margen operativo", "Margen neto"],
                            [accent, warm, "#3F6B4A"], h=138) if am else ""
    cost_chart = ch.stacked_bar([
        ("Costo reposición", cr, accent), ("Comisiones", com, "#A8554F"),
        ("Costos fijos", cf, warm), ("Amortización", amort, "#9A6B1E"),
        ("Gastos variables", gv, "#7E6B86"), ("Utilidad neta", un, "#3F6B4A"),
    ]) if V else ""
    cash_chart = ch.cashflow(cf_total, cum, am, accent, warm, NEG, M, h=150) if has_cash else ""

    # ---- forecast / scenarios ----
    fc = results.get("forecast") or {}
    trend = (fc.get("trend_analysis") or {}).get("trend", {})
    avg_growth = (fc.get("trend_analysis") or {}).get("average_growth_rate", 0.0)
    scen = (fc.get("scenario_comparison") or {}).get("scenarios", {})
    scen_label = {"base": "Base", "bull": "Optimista", "bear": "Conservador"}
    scen_rows, scen_groups = "", []
    for key in ("bear", "base", "bull"):
        sc = scen.get(key)
        if not sc:
            continue
        periods = sc.get("forecast_periods", [])
        rev = sum(p.get("revenue", 0) for p in periods)
        oi = sum(p.get("operating_income", 0) for p in periods)
        scen_groups.append((scen_label[key], [rev]))
        scen_rows += (f'<tr><td><b>{scen_label[key]}</b><br><span class="note">'
                      f'crec. {P(sc.get("growth_rate",0))}/mes · margen {P(sc.get("gross_margin",0))}</span></td>'
                      f'<td class="r">{M(rev)}</td><td class="r">{M(oi)}</td></tr>')
    horizon = len(next(iter(scen.values()), {}).get("forecast_periods", [])) if scen else 0
    scen_chart = ch.grouped_bars(scen_groups, ["Ventas proyectadas"], [warm], accent, M, h=132) if scen_groups else ""
    last_delta = ((v_ser[-1] - v_ser[-2]) / v_ser[-2]) if len(v_ser) >= 2 and v_ser[-2] else 0

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
                     f'<td class="r">{M(pri)}</td><td class="r">{M(d)}</td>'
                     f'<td class="r"><span class="pill {cls}">{("+" if dp>=0 else "")}{P(dp)}</span></td></tr>')

    # ---- insights ----
    def adj_margin(x):
        return "saludable" if x >= 0.50 else ("correcto pero ajustado" if x >= 0.38 else "comprimido")
    ins = []
    ins.append(f"De cada $100 vendidos quedan <b>{round(mb*100)} de margen bruto ({P(mb)}, {adj_margin(mb)})</b>; "
               f"las <b>comisiones se llevan {P(com/V if V else 0)}</b> de la facturación — una carga alta y la "
               f"palanca de rentabilidad más directa.")
    ins.append(f"Los <b>costos fijos consumen {P(cf/V if V else 0)}</b> y reducen el margen operativo a "
               f"<b>{P(mo)}</b>; tras amortizaciones y gastos variables, el <b>margen neto queda en {P(mn)}</b>.")
    if loss_months:
        tail = (" y recién fue rentable en los últimos"
                if _losses_at_start(loss_idx, len(am)) else "")
        ins.append(f"<b>Atención:</b> el {P(mn)} neto es un promedio del período. El negocio dio "
                   f"<b>pérdida neta en {len(loss_months)} de {active} meses</b> "
                   f"({', '.join(loss_months)}){tail}.")
    if has_cash and cash_trough < 0:
        ins.append(f"Ganar no es lo mismo que tener caja: la <b>caja acumulada tocó {M(cash_trough)}</b> en "
                   f"{trough_month} antes de recuperar a {M(cash_end)} — vigilar el calce entre cobranzas y pagos.")
    if seg_known and be_ventas:
        ins.append(f"<b>Punto de equilibrio del período: {M(be_ventas)}</b> (facturación necesaria del "
                   f"workbook). Hay un <b>colchón de {M(seg_pesos)} ({P(seg)})</b> antes de entrar en pérdida.")
    if trend:
        dirn = "alcista" if trend.get("direction") == "upward" else "bajista"
        r2 = str(round(trend.get("r_squared", 0), 2)).replace(".", ",")
        note = (f" aunque el último mes ya mostró una baja de {P(abs(last_delta))}" if last_delta < 0 else "")
        reb = _rebound_month(v_ser, am)
        infl = (f" está inflado por la recuperación de {esc(reb)} y" if reb else "")
        ins.append(f"La <b>tendencia es {dirn}</b> (R²={r2}) sobre {active} meses{note}; el crecimiento promedio "
                   f"de {P(avg_growth)}/mes{infl} <b>no debe extrapolarse</b>.")
    insights_html = "".join(f"<li>{x}</li>" for x in ins)

    # ---- recommendations (computed, peso-quantified) ----
    recs = []
    com_share = (com / V) if V else 0.0
    if com_share > 0.03:   # only when comisiones are a meaningful share of ventas
        recs.append(("Atacar el costo de comisiones",
                     f"Las comisiones son {P(com_share)} de las ventas. Bajarlas 3 puntos suma "
                     f"~<b>{M(0.03*ann_ventas)}/año</b> directo a la utilidad."))
    if seg_known and seg_pesos > 0:
        recs.append(("Cuidar el margen de seguridad",
                     f"Las ventas pueden caer hasta <b>{M(seg_pesos)}</b> antes de entrar en pérdida. Es el colchón a defender si la demanda se enfría."))
    if cash_trough < 0:
        recs.append(("Asegurar capital de trabajo",
                     f"La caja llegó a <b>{M(cash_trough)}</b>. Conviene una línea o colchón de al menos ese piso para los meses flojos."))
    baja = " y el último a la baja" if last_delta < 0 else ""
    recs.append(("Planificar con prudencia",
                 f"Con solo {active} meses{baja}, planificar sobre el escenario <b>Conservador</b>, no el Base."))
    gap = uo - un
    if uo and gap / uo > 0.2:
        recs.append(("Revisar la brecha operativa→neta",
                     f"Entre utilidad operativa y neta se pierde <b>{M(gap)}</b> ({P(gap/uo)} del resultado operativo, "
                     f"= gastos variables/amortización). Vale revisar su composición."))
    if v_ser:
        worst_i = v_ser.index(min(v_ser))
        recs.append(("Trabajar el mes más flojo",
                     f"<b>{am[worst_i]}</b> fue el peor ({M(v_ser[worst_i])} de ventas). Empujar temporada o bajar costos fijos ahí."))
    rec_rows = "".join(f'<tr class="rec"><td>{t}</td><td>{d}</td></tr>' for t, d in recs)

    warns = fin.get("warnings") or []
    warn_block = "".join(f'<div class="warnbox note">⚠ {esc(w)}</div>' for w in warns) if warns else ""

    # ---- income-statement table ----
    is_rows_def = [("ventas", "Ventas", "line"), ("costoReposicion", "(−) Costo reposición", "line"),
                   ("comisiones", "(−) Comisiones", "line"), ("utilidadBruta", "Utilidad bruta", "sub"),
                   ("costosFijos", "(−) Costos fijos", "line"), ("amortizacion", "(−) Amortización", "line"),
                   ("utilidadOperativa", "Utilidad operativa", "sub"),
                   ("gastosVariables", "(−) Gastos variables", "line"), ("utilidadNeta", "Utilidad neta", "tot")]
    head_m = "".join(f"<th class='r'>{esc(mo)}</th>" for mo in am)
    is_rows = ""
    for key, label, kind in is_rows_def:
        cells = "".join(f"<td class='r'>{M(nom(x))}</td>" for x in m.get(key, [])[:active])
        cls = " class='sub'" if kind == "sub" else (" class='tot'" if kind == "tot" else "")
        ann_meas = a.get(key, 0)
        ann_val = nom(ann_meas)
        ann_real = ann_meas.get("real") if isinstance(ann_meas, dict) else None
        real_cell = (M(ann_real) + marks(ann_meas)) if ann_real is not None else "—"
        is_rows += (f"<tr{cls}><td>{label}</td>{cells}<td class='r'><b>{M(ann_val)}</b></td>"
                    f"<td class='r'>{real_cell}</td><td class='r'>{M(ann_val*scale)}</td></tr>")

    def kicker(num, lab):
        return f'<div class="kicker"><span class="num">{num}</span><span class="label">{lab}</span></div>'

    # ===== Reexpresión a moneda de cierre (real vs nominal) =====
    base = fin.get("baseMonth")
    rv_ser = [x.get("real") if isinstance(x, dict) else None for x in m.get("ventas", [])[:active]]
    ventas_meas = a.get("ventas")
    real_ann = ventas_meas.get("real") if isinstance(ventas_meas, dict) else None
    real_pts = [r for r in rv_ser if r is not None]
    # months whose real was filled with PROJECTED inflation (no actual IPC yet) — must be named
    proj_months = [am[i] for i, x in enumerate(m.get("ventas", [])[:active])
                   if isinstance(x, dict) and "projected" in x.get("transforms", [])]
    proj_note = (f' Los meses <b>{", ".join(proj_months)}</b> usan inflación <b>proyectada</b>ᵖ '
                 f'(sin IPC publicado aún), no índice real.' if proj_months else "")
    if base and real_pts:
        dual = ch.dual_bars(am, v_ser, rv_ser, accent, warm, M, h=120)
        nom_growth = (v_ser[-1] / v_ser[0] - 1) if len(v_ser) >= 2 and v_ser[0] else 0.0
        real_growth = (real_pts[-1] / real_pts[0] - 1) if len(real_pts) >= 2 and real_pts[0] else 0.0
        real_ann_txt = M(real_ann) + "ʳ" if real_ann is not None else "n/d (período incompleto en la serie IPC)"
        reexp_section = f"""<div class="page section-open">
  {kicker('02', 'Reexpresión a moneda de cierre')}
  <h2 class="report">Pesos corrientes vs. moneda de cierre.</h2>
  <p class="lede">Las cifras nominales mezclan pesos de poder adquisitivo distinto. Reexpresadas a la moneda
  de <b>{base}</b> con el IPC INDEC nivel general, se comparan en términos reales. Esto homogeneiza el Estado
  de Resultados — <b>no</b> es un ajuste integral RT 6 (no calcula RECPAM); ver Supuestos.</p>
  <div class="chartbox"><div class="ct">Ventas mensuales: Nominal vs Real (moneda de cierre {base})</div>{dual}</div>
  <div class="grid2">
    <div><div class="bignum">{P(nom_growth)}</div><p class="note">Crecimiento <b>nominal</b> del período.</p></div>
    <div><div class="bignum">{P(real_growth)}</div><p class="note">Crecimiento <b>real</b> (moneda de cierre). Si es
    menor que el nominal, parte de la "suba" es solo inflación.</p></div>
  </div>
  <p class="note">Ventas anuales reexpresadas: <b>{real_ann_txt}</b> · nominal {M(V)}.{proj_note}</p>
</div>"""
    else:
        reexp_section = f"""<div class="page section-open">
  {kicker('02', 'Reexpresión a moneda de cierre')}
  <h2 class="report">Pesos corrientes vs. moneda de cierre.</h2>
  <p class="lede">No se pudo reexpresar el período: faltan meses en la serie IPC disponible, o el año no está
  etiquetado. Se reportan valores <b>nominales</b>. Ver Advertencias.</p>
</div>"""

    # ===== Posición fiscal =====
    fz = fin.get("fiscal") or {}
    reg = fz.get("regimen")
    if reg == "responsable_inscripto":
        iva = fz.get("iva", {}); br = fz.get("bridge", {})
        fiscal_body = f"""<table>
    <tr><th>Concepto</th><th class="r">{sym}/período</th><th>Nota</th></tr>
    <tr><td>IVA débito fiscal</td><td class="r">{M(iva.get('debito',0))}</td><td>Sobre ventas</td></tr>
    <tr><td>IVA crédito fiscal</td><td class="r">{M(iva.get('credito',0))}</td><td>Estimado s/compras gravadas</td></tr>
    <tr class="sub"><td>Posición IVA</td><td class="r">{M(iva.get('posicion',0))}</td><td>Flujo fiscal — no integra el Resultado</td></tr>
    <tr class="sub"><td>Resultado neto (workbook)</td><td class="r">{M(br.get('resultadoAntes',0))}</td><td>Punto de partida — antes de impuesto nacional</td></tr>
    <tr><td>Ingresos Brutos (IIBB)</td><td class="r">{M(br.get('iibb',0))}</td><td>Informativo — verificar si ya está en costos</td></tr>
    <tr><td>(−) Impuesto a las Ganancias</td><td class="r">{M(br.get('ganancias',0))}</td><td>Estimación s/resultado neto</td></tr>
    <tr class="tot"><td>Resultado después de Ganancias</td><td class="r">{M(br.get('resultadoDespues',0))}</td><td>Neto − Ganancias estimadas (IIBB no re-restado)</td></tr>
  </table>
  <div class="callout warm"><h4>Alcance fiscal</h4><p class="note">{esc(br.get('ganancias_nota',''))} {esc(br.get('iibb_nota',''))}
  La posición de IVA es un flujo fiscal y no integra el Resultado. Convenio Multilateral (IIBB
  multi-jurisdicción) y la liquidación completa de Ganancias quedan fuera de alcance.</p></div>"""
    elif reg == "monotributo":
        mt = fz.get("monotributo", {}); prox = mt.get("proximidad", 0) or 0
        fiscal_body = f"""<div class="grid2">
    <div><div class="bignum">{M(mt.get('cuotaMensualTotal',0))}</div><p class="note">Cuota mensual Monotributo,
    categoría {mt.get('categoria','')}.</p></div>
    <div><div class="bignum">{P(prox)}</div><p class="note">Proximidad al techo (nominal
    {M(mt.get('techoFacturacionAnual',0))}); headroom {M(mt.get('headroom',0))}.</p></div>
  </div>
  <div class="callout {'bad' if prox>=0.85 else 'warm'}"><h4>Categoría</h4><p class="note">Facturación y techos
  en pesos <b>nominales</b> (los topes AFIP son nominales; no se reexpresan).
  {'Cerca del techo: planificar recategorización o pase a Responsable Inscripto.' if prox>=0.85 else 'Con margen respecto del techo.'}</p></div>"""
    else:
        fiscal_body = ('<p class="note">Régimen fiscal no configurado: capa fiscal omitida. Definir '
                       '<code>fiscal.regimen</code> (monotributo / responsable_inscripto) en la configuración.</p>')
    fiscal_section = f"""<div class="page section-open">
  {kicker('06', 'Posición fiscal')}
  <h2 class="report">La carga impositiva, estimada.</h2>
  <p class="lede">Posición fiscal según el régimen. Los impuestos se calculan sobre pesos <b>nominales</b>
  (base AFIP); las cifras de Ganancias son una <b>estimación</b> por alícuota efectiva, no una liquidación.</p>
  {fiscal_body}
</div>"""

    # ===== Palancas / Acciones =====
    lv = results.get("levers") or {}
    levs = lv.get("levers", [])
    if levs:
        torn = ch.tornado([(l["titulo"], l["impacto"]["real"]) for l in levs], accent, M)
        lev_rows = "".join(
            f'<tr><td><b>{esc(l["titulo"])}</b><br><span class="note">{esc(l["accion"])}</span></td>'
            f'<td class="r">{M(l["impacto"]["real"])}</td>'
            f'<td><span class="pill p-info">{esc(l["confianza"])}</span></td>'
            f'<td class="note">{esc(l["supuesto"])}</td></tr>' for l in levs)
        levers_body = f"""<div class="chartbox"><div class="ct">Palancas por impacto estimado</div>{torn}</div>
  <table><tr><th>Palanca / acción</th><th class="r">Impacto/mes</th><th>Confianza</th><th>Supuesto</th></tr>{lev_rows}</table>
  <p class="note"><b>{esc(lv.get('nota',''))}</b></p>"""
    else:
        levers_body = ('<p class="note">No se detectaron palancas accionables con los umbrales actuales: los '
                       'indicadores del período están dentro de rango. <b>Impactos no aditivos.</b></p>')
    levers_section = f"""<div class="page section-open">
  {kicker('09', 'Palancas / Acciones')}
  <h2 class="report">De los números a las decisiones.</h2>
  <p class="lede">Acciones priorizadas y cuantificadas, cada una atada a la cifra que la dispara y medida en
  términos reales. Se estiman de forma independiente y pueden solaparse: <b>no son aditivas</b>, no sumar.</p>
  {levers_body}
</div>"""

    # ===== Ratios — filter_ratios returns a FLAT {metric: value} dict =====
    ratios = results.get("ratios") or {}
    _RATIO_LABELS = {
        "gross_margin": ("Rentabilidad", "Margen bruto"), "operating_margin": ("Rentabilidad", "Margen operativo"),
        "net_margin": ("Rentabilidad", "Margen neto"), "roe": ("Rentabilidad", "ROE"), "roa": ("Rentabilidad", "ROA"),
        "current_ratio": ("Liquidez", "Razón corriente"), "quick_ratio": ("Liquidez", "Prueba ácida"),
        "cash_ratio": ("Liquidez", "Razón de caja"), "inventory_turnover": ("Eficiencia", "Rotación de existencias"),
        "asset_turnover": ("Eficiencia", "Rotación de activos"), "receivables_turnover": ("Eficiencia", "Rotación de créditos"),
        "dso": ("Eficiencia", "Días de venta (DSO)")}
    _PCT_KEYS = {"gross_margin", "operating_margin", "net_margin", "roe", "roa"}
    def _ratio_fmt(k, v):
        try:
            f = float(v)
        except (TypeError, ValueError):
            return esc(str(v))
        return f"{f*100:.1f}%".replace(".", ",") if k in _PCT_KEYS else f"{f:.2f}".replace(".", ",")
    ratio_rows = ""
    for k, v in (ratios.items() if isinstance(ratios, dict) else []):
        if isinstance(v, dict):
            continue
        cat, lab = _RATIO_LABELS.get(k, ("—", k))
        ratio_rows += f'<tr><td>{cat}</td><td>{esc(lab)}</td><td class="r">{_ratio_fmt(k, v)}</td></tr>'
    ratios_table = (f'<table><tr><th>Categoría</th><th>Indicador</th><th class="r">Valor</th></tr>{ratio_rows}</table>'
                    if ratio_rows else '<p class="note">Ratios no disponibles para este período.</p>')
    ratios_section = f"""<div class="page section-open">
  {kicker('10', 'Ratios')}
  <h2 class="report">Indicadores financieros.</h2>
  <p class="lede">Ratios de rentabilidad, liquidez y eficiencia sobre los estados del período. Se omiten los de
  endeudamiento y de mercado (un comercio privado no tiene deuda, patrimonio ni cotización).</p>
  {ratios_table}
</div>"""

    # provenance legend over the annual measures actually shown
    # pool annual AND active monthly measures so projected months surface ᵖ in the legend
    _pool = [a[k] for k in a if isinstance(a.get(k), dict)]
    for series in m.values():
        _pool.extend(x for x in series[:active] if isinstance(x, dict))
    prov_legend = legend(_pool)

    # ===== Punto de equilibrio body (from the model; n/d when the workbook lacks it) =====
    if seg_known:
        equilibrio_body = f"""<div class="grid2">
    <div><div class="bignum">{M(be_ventas)}</div><p class="note">Punto de equilibrio del período
    (facturación necesaria informada en el workbook).</p></div>
    <div><div class="bignum">{P(seg)}</div><p class="note">Margen de seguridad: las ventas pueden caer
    {M(seg_pesos)} antes de entrar en pérdida.</p></div>
  </div>
  <div class="callout"><h4>Cómo leerlo</h4>
    <p class="note">El workbook informa una facturación necesaria de <b>{M(be_ventas)}</b> para el período;
    contra ventas de <b>{M(V)}</b>, el negocio opera {'por encima' if V>=be_ventas else 'por debajo'} del
    equilibrio, con un margen de seguridad de <b>{P(seg)}</b>.</p></div>"""
    else:
        equilibrio_body = ('<div class="callout warm"><h4>Sin dato de equilibrio</h4>'
                           '<p class="note">El workbook no informa la "facturación necesaria" (punto de '
                           'equilibrio), por lo que el margen de seguridad no puede calcularse de forma '
                           'conciliable. Completar esa fila en la hoja PUNTO DE EQUILIBRIO del workbook '
                           'para habilitar este análisis.</p></div>')

    head_period = f"{active} meses de {year} (YTD)"
    css = _CSS.replace("__ACCENT__", accent).replace("__WARM__", warm)
    prepared_html = (f'<div><span class="label">Para</span>'
                     f'<div style="font-size:12px;margin-top:2mm">{esc(prepared)}</div></div>') if prepared else ""
    scen_chart_html = (f'<div class="chartbox"><div class="ct">Ventas proyectadas próximos {horizon} meses — '
                       f'por escenario</div>{scen_chart}</div>') if scen_chart else '<p class="note">Proyección no disponible.</p>'
    scen_table_html = (f'<table><tr><th>Escenario</th><th class="r">Ventas {horizon}m</th>'
                       f'<th class="r">Result. operativo</th></tr>{scen_rows}</table>') if scen_rows else ""
    var_table_html = (f'<table><tr><th>Concepto</th><th class="r">Actual</th><th class="r">Mes previo</th>'
                      f'<th class="r">Δ</th><th class="r">Δ%</th></tr>{var_rows}</table>') if var_rows else \
        '<p class="note">Variación no disponible (se requieren ≥2 meses con datos).</p>'
    cash_section = (f'''<div class="page section-open">
  {kicker('04', 'Caja y flujo de fondos')}
  <h2 class="report">Una cosa es ganar; otra, tener la plata.</h2>
  <p class="lede">El resultado contable y la caja no son lo mismo: se puede ser rentable y aun así quedarse
  corto de efectivo si la cobranza llega tarde. Esta es la película del dinero real del período.</p>
  <div class="chartbox"><div class="ct">Caja neta mensual y caja acumulada</div>{cash_chart}</div>
  <div class="callout {'bad' if cash_trough < 0 else 'warm'}"><h4>Lectura de caja</h4>
    <p class="note">La caja acumulada cerró el período en <b>{M(cash_end)}</b>, con un piso de
    <b>{M(cash_trough)}</b> en {trough_month}. {'Estuvo en terreno negativo: el negocio operó con caja ajustada pese a ser rentable hacia el final.' if cash_trough < 0 else 'Se mantuvo en terreno positivo.'}
    Vigilar el capital de trabajo es clave para no quedar sin caja en los meses flojos.</p></div>
</div>''') if has_cash else ""
    warn_section = (('<h3>Advertencias de datos</h3><ul class="check">' +
                     "".join(f"<li>{esc(w)}</li>" for w in warns) + "</ul>")) if warns else ""

    html = f"""<!DOCTYPE html><html lang="{locale}"><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400;0,6..96,500;0,6..96,600;0,6..96,700;1,6..96,500&family=Archivo:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>{css}</style></head><body>

<div class="cover">
  <div><div class="wordmark">{esc(name)}</div><div class="rule"></div>
    <div class="label">Informe financiero · {head_period}</div></div>
  <div class="bigstat"><div class="n">{M(ann_ventas)}</div><div class="c">Ritmo anualizado (run-rate)</div>
    <div class="n" style="font-size:29px;margin-top:6mm">{P(mb)}</div><div class="c">Margen bruto</div></div>
  <div>
    <h1>Análisis financiero:<br>rentabilidad, caja y<br><span class="it">proyección</span>.</h1>
    <p class="sub">Lectura experta sobre los estados ya construidos del negocio: resultados, márgenes, caja,
    punto de equilibrio, variación y escenarios — con recomendaciones cuantificadas. Cada cifra concilia con
    el workbook del cliente; lo prospectivo se marca como supuesto.</p>
    <div class="meta">{prepared_html}
      <div><span class="label">Período</span><div style="font-size:12px;margin-top:2mm">{head_period}</div></div>
      <div><span class="label">Moneda</span><div style="font-size:12px;margin-top:2mm">{fin.get('currency','ARS')}</div></div>
    </div>
  </div>
</div>

<div class="page section-open">
  {kicker('00', 'Resumen ejecutivo')}
  <h2 class="report">La foto financiera, en una página.</h2>
  <p class="lede">Dónde está la rentabilidad, qué se la come y hacia dónde apunta. Los números salen del
  estado de resultados real; el análisis los interpreta y los traduce en acciones.</p>
  <div class="stats">
    <div class="stat"><div class="n accent">{M(ann_ventas)}</div><div class="c">Ritmo anualizado · {M(V)} en {active} meses</div></div>
    <div class="stat"><div class="n">{P(mb)}</div><div class="c">Margen bruto</div></div>
    <div class="stat"><div class="n">{P(mo)}</div><div class="c">Margen operativo</div></div>
    <div class="stat"><div class="n accent">{P(mn)}</div><div class="c">Margen neto · {M(un)} netos</div></div>
  </div>
  {warn_block}
  <div class="callout"><h4>Lecturas clave</h4><ul class="check">{insights_html}</ul></div>
</div>

<div class="page section-open">
  {kicker('01', 'Estado de Resultados')}
  <h2 class="report">De cada peso vendido, qué queda.</h2>
  <p class="lede">El estado de resultados mensual (conciliado con el workbook), su total YTD en pesos
  <b>nominales</b> y <b>reales</b> (moneda de cierre{f' {base}' if base else ''}), y el valor anualizado.
  La cascada muestra, paso a paso, cómo la facturación se convierte en utilidad neta.</p>
  <table><tr><th>Concepto</th>{head_m}<th class="r">YTD Nominal</th><th class="r">YTD Real</th><th class="r">Anual est.</th></tr>{is_rows}</table>
  <div class="chartbox"><div class="ct">Facturación mensual — pico en dorado</div>{rev_chart}</div>
  <div class="chartbox"><div class="ct">Cascada de resultados — Ventas → Utilidad neta (concilia al peso)</div>{wf}</div>
</div>

{reexp_section}

<div class="page section-open">
  {kicker('03', 'Rentabilidad y costos')}
  <h2 class="report">Márgenes y estructura de costos.</h2>
  <p class="lede">Cómo evolucionan los márgenes mes a mes y en qué se va cada peso de facturación.
  El peso de las comisiones y de los costos fijos define la rentabilidad final.</p>
  <div class="chartbox"><div class="ct">Evolución de márgenes (% de ventas) por mes</div>{margin_chart}</div>
  <div class="chartbox"><div class="ct">Estructura de la facturación — a dónde va cada peso (suma 100%)</div>{cost_chart}</div>
  <table>
    <tr><th>Componente</th><th class="r">{sym}/período</th><th class="r">% ventas</th><th>Lectura</th></tr>
    <tr><td>Costo de reposición (CMV)</td><td class="r">{M(cr)}</td><td class="r">{P(cr/V if V else 0)}</td><td>Costo directo de la mercadería</td></tr>
    <tr><td>Comisiones</td><td class="r">{M(com)}</td><td class="r">{P(com/V if V else 0)}</td><td>Costo variable de venta — peso alto</td></tr>
    <tr class="sub"><td>Utilidad bruta (margen de contribución)</td><td class="r">{M(ub)}</td><td class="r">{P(mb)}</td><td>Lo que aporta cada venta a cubrir fijos</td></tr>
    <tr><td>Costos fijos</td><td class="r">{M(cf)}</td><td class="r">{P(cf/V if V else 0)}</td><td>Estructura — no varía con la venta</td></tr>
    <tr><td>Amortización</td><td class="r">{M(amort)}</td><td class="r">{P(amort/V if V else 0)}</td><td>Cargo no operativo (créditos)</td></tr>
    <tr><td>Gastos variables</td><td class="r">{M(gv)}</td><td class="r">{P(gv/V if V else 0)}</td><td>Entre resultado operativo y neto</td></tr>
    <tr class="tot"><td>Utilidad neta</td><td class="r">{M(un)}</td><td class="r">{P(mn)}</td><td>Resultado final del período</td></tr>
  </table>
</div>

{cash_section}

<div class="page section-open">
  {kicker('05', 'Punto de equilibrio')}
  <h2 class="report">Cuánto hay que vender para no perder.</h2>
  <p class="lede">El punto de equilibrio es la facturación a la que el margen de contribución (el {P(mb)} que deja
  cada venta) cubre exactamente los costos fijos y la amortización. Asume que costo de mercadería y comisiones
  varían con la venta, y que la estructura se mantiene.</p>
  {equilibrio_body}
</div>

{fiscal_section}

<div class="page section-open">
  {kicker('07', 'Proyección y escenarios')}
  <h2 class="report">Hacia dónde va el negocio.</h2>
  <p class="lede">Proyección construida sobre la tendencia y estacionalidad reales de los {active} meses con
  datos. Tres escenarios acotan el rango. Con pocos meses, conviene leerla con cautela.
  <span class="note">Cifras prospectivas: supuesto.</span></p>
  {scen_chart_html}
  {scen_table_html}
</div>

<div class="page section-open">
  {kicker('08', 'Variación mensual')}
  <h2 class="report">Qué cambió respecto al mes anterior.</h2>
  <p class="lede">Variación período contra período (último mes con datos vs. el previo). El workbook no lleva
  presupuesto, por lo que la comparación es mes contra mes, no contra objetivo.</p>
  {var_table_html}
</div>

{levers_section}

{ratios_section}

<div class="page section-open">
  {kicker('11', 'Conclusiones')}
  <h2 class="report">Qué hacer con estos números.</h2>
  <p class="lede">Recomendaciones concretas, cada una atada a una cifra del informe y cuantificada en pesos
  donde se puede.</p>
  <table class="rec"><tr><th>Recomendación</th><th>Por qué / cuánto</th></tr>{rec_rows}</table>
</div>

<div class="page section-open">
  {kicker('12', 'Supuestos y datos')}
  <h2 class="report">Origen de los números y supuestos.</h2>
  <p class="lede">Para que cada cifra sea defendible: de dónde sale y qué se asumió.</p>
  <h3>Origen de los datos</h3>
  <ul class="check">
    <li>Los <b>estados se leen</b> del workbook del cliente (Estado de Resultados, Flujos de Dinero, Punto de
    equilibrio) y se <b>concilian</b>: el informe no recalcula, reproduce. La cascada cierra al peso.</li>
    <li>Se analiza el <b>año {year}</b>, ventana de <b>{active} meses con datos</b>. El "anualizado / run-rate"
    proyecta el ritmo a 12 meses y asume que los meses sin datos rinden como el promedio del período
    (ojo con la estacionalidad).</li>
    <li>El <b>margen bruto</b> usa el costo efectivo (Ventas − Utilidad bruta), por lo que concilia con el
    estado de resultados e incluye comisiones.</li>
    <li>La <b>proyección</b> y los escenarios son prospectivos: <b>supuesto</b>, no ingreso garantizado.</li>
    <li>La <b>reexpresión a moneda de cierre</b> usa el IPC INDEC nivel general; reexpresa el Estado de
    Resultados a la moneda de <b>{base or 'n/d'}</b>. Es una homogeneización del P&amp;L — <b>no</b> calcula
    <b>RECPAM</b> (Resultado por Exposición a la Inflación): eso queda <b>fuera de alcance</b> por requerir un
    balance completo con partidas monetarias/no monetarias.</li>
    <li>La <b>posición fiscal</b> se calcula sobre pesos nominales (base AFIP). Ganancias es una
    <b>estimación</b> por alícuota efectiva, no una liquidación; el IVA es un flujo fiscal y no integra el
    Resultado. Topes de Monotributo en pesos nominales.</li>
    <li>Las <b>palancas</b> se estiman de forma independiente y pueden solaparse: <b>no son aditivas</b>.</li>
  </ul>
  {f'<p class="note">Referencias: {prov_legend}</p>' if prov_legend else ''}
  {warn_section}
  <div class="footer-note">{esc(name)} · Informe financiero sobre el workbook del cliente · período {head_period}.
  Estados conciliados; proyección, ratios y recomendaciones son estimaciones con supuestos explícitos.</div>
</div>

</body></html>"""
    return html
