from workbook import parse_workbook
from financials import build_financials
from html_report import build_html

def test_build_html_contains_brand_and_statement(fixture_workbook):
    fin = build_financials(parse_workbook(fixture_workbook))
    cfg = {"brand": {"name": "ACME", "accent": "#123456", "currencySymbol": "$"}}
    results = {"ratios": {"gross_margin": 0.5}, "forecast": {}, "variance": {}}
    html = build_html(fin, results, cfg)
    assert "ACME" in html and "Estado de Resultados" in html
    assert "#123456" in html  # accent applied
    assert "supuesto" in html.lower()  # assumption caveat present

def test_build_html_renders_data_warnings(fixture_workbook):
    fin = build_financials(parse_workbook(fixture_workbook))
    fin["warnings"] = ["'utilidad neta' tiene celdas con error (#REF!) en el workbook"]
    html = build_html(fin, {"ratios": {}, "forecast": {}, "variance": {}},
                      {"brand": {"name": "ACME"}})
    assert "Advertencias" in html and "#REF!" in html


def test_report_has_expert_sections_and_charts(fixture_workbook):
    from workbook import parse_workbook
    from financials import build_financials
    from html_report import build_html
    fin = build_financials(parse_workbook(fixture_workbook))
    html = build_html(fin, {"ratios": {}, "forecast": {}, "variance": {}},
                      {"brand": {"name": "ACME", "accent": "#6B2532"}})
    for section in ["Resumen ejecutivo", "Estado de Resultados", "Punto de equilibrio",
                    "Proyección y escenarios", "Variación mensual", "Cascada de resultados",
                    "Conclusiones"]:
        assert section in html, f"missing section: {section}"
    assert html.count("<svg") >= 3      # revenue bars + waterfall + margin lines at minimum
    assert "Ritmo anualizado" in html


def test_html_does_not_leak_measure_dicts(fixture_workbook):
    # schema-2.0 money lines are measure dicts; the report must unwrap them via nom(),
    # never str() a {'nominal': ...} dict into the output.
    fin = build_financials(parse_workbook(fixture_workbook))
    html = build_html(fin, {"ratios": {}, "forecast": {}, "variance": {}},
                      {"brand": {"name": "ACME"}})
    assert "'nominal'" not in html and "{'nominal" not in html


def test_report_has_new_sections_and_marks(fixture_workbook):
    from workbook import parse_workbook
    from financials import build_financials
    from fiscal import apply_fiscal
    from restatement import restate
    from levers import build_levers
    cfg = {"brand": {"name": "ACME", "accent": "#6B2532"},
           "fiscal": {"regimen": "responsable_inscripto", "alicuotaIIBB": 0.035,
                      "alicuotaEfectivaGanancias": 0.30, "proporcionComprasGravadas": 1.0},
           "finance": {}}
    fin = build_financials(parse_workbook(fixture_workbook))
    fin = apply_fiscal(fin, cfg)
    fin = restate(fin, cfg["finance"])
    results = {"forecast": {}, "variance": {"line_items": []},
               "ratios": {"gross_margin": 0.6, "operating_margin": 0.2, "net_margin": 0.05},
               "levers": build_levers(fin, cfg)}
    html = build_html(fin, results, cfg)
    for h in ["Estado de Resultados", "Reexpresión a moneda de cierre", "Posición fiscal",
              "Proyección", "Palancas", "Ratios", "Supuestos"]:
        assert h in html, f"missing section: {h}"
    assert "Margen bruto" in html and "60,0%" in html      # flat ratios rendered as %
    assert "Nominal" in html and "Real" in html            # dual columns
    assert "reexpresado a moneda de cierre" in html.lower()  # provenance legend
    assert "RECPAM" in html and "fuera de alcance" in html.lower()
    assert "estimación" in html.lower()                    # Ganancias not a liquidación
    assert "Impactos no aditivos" in html                  # levers non-additive
    assert ("CMV" in html) or ("Costo de la mercadería vendida" in html)
    assert "'nominal'" not in html and "{'nominal" not in html   # no measure dict leaks


# ---------------------------------------------------------------------------
# De-fossilized narrative — no ACME-engagement leftovers for other clients
# ---------------------------------------------------------------------------
_IS_KEYS = ["ventas","costoReposicion","comisiones","utilidadBruta","costosFijos",
            "amortizacion","utilidadOperativa","gastosVariables","utilidadNeta"]

def _fin_with(months, ventas, utilidad_neta=None, comisiones=None):
    n = len(months)
    mp = {k: [0]*n for k in _IS_KEYS}
    mp["ventas"] = list(ventas)
    mp["utilidadNeta"] = list(utilidad_neta if utilidad_neta is not None else ventas)
    if comisiones is not None:
        mp["comisiones"] = list(comisiones)
    parsed = {"months": list(months), "year": 2025,
              "incomeStatement": {"monthly": mp},
              "cashFlow": {"monthly": {"ingresos":[0]*n,"egresos":[0]*n,"total":[0]*n}},
              "breakEven": {"margenBrutoMonthly": [], "facturacionEquilibrioMonthly": []},
              "warnings": []}
    return build_financials(parsed)

_TREND = {"trend_analysis": {"trend": {"direction": "upward", "r_squared": 0.9},
                             "average_growth_rate": 0.05}}

def test_rebound_month_helper_names_dominant_jump():
    from html_report import _rebound_month
    assert _rebound_month([100, 50, 200, 210], ["Ago","Sep","Oct","Nov"]) == "Oct"
    assert _rebound_month([100, 150, 200, 250], ["Ago","Sep","Oct","Nov"]) is None  # broad-based
    assert _rebound_month([200, 150, 100], ["Ago","Sep","Oct"]) is None             # no rebound

def test_narrative_names_actual_rebound_month_not_febrero():
    fin = _fin_with(["Agosto","Septiembre","Octubre","Noviembre"], [100, 50, 200, 210])
    html = build_html(fin, {"forecast": _TREND, "ratios": {}, "variance": {}},
                      {"brand": {"name": "A"}})
    assert "recuperación de Octubre" in html
    assert "febrero" not in html.lower()

def test_narrative_drops_rebound_clause_when_growth_broad():
    fin = _fin_with(["Agosto","Septiembre","Octubre","Noviembre"], [100, 150, 200, 250])
    html = build_html(fin, {"forecast": _TREND, "ratios": {}, "variance": {}},
                      {"brand": {"name": "A"}})
    assert "está inflado por la recuperación" not in html

def test_last_month_falling_clause_gated_on_delta():
    rising = _fin_with(["Agosto","Septiembre","Octubre"], [100, 150, 200])
    assert "el último a la baja" not in build_html(
        rising, {"ratios": {}, "forecast": {}, "variance": {}}, {"brand": {"name": "A"}})
    falling = _fin_with(["Agosto","Septiembre","Octubre"], [100, 200, 150])
    assert "el último a la baja" in build_html(
        falling, {"ratios": {}, "forecast": {}, "variance": {}}, {"brand": {"name": "A"}})

def test_comisiones_rec_only_when_meaningful_share():
    none = _fin_with(["Agosto","Septiembre"], [100, 100], comisiones=[0, 0])
    assert "Atacar el costo de comisiones" not in build_html(
        none, {"ratios": {}, "forecast": {}, "variance": {}}, {"brand": {"name": "A"}})
    heavy = _fin_with(["Agosto","Septiembre"], [100, 100], comisiones=[10, 10])
    assert "Atacar el costo de comisiones" in build_html(
        heavy, {"ratios": {}, "forecast": {}, "variance": {}}, {"brand": {"name": "A"}})

def test_rentable_en_los_ultimos_only_when_losses_at_start():
    at_start = _fin_with(["Agosto","Septiembre","Octubre"], [100]*3,
                         utilidad_neta=[-50, 100, 100])
    assert "recién fue rentable en los últimos" in build_html(
        at_start, {"ratios": {}, "forecast": {}, "variance": {}}, {"brand": {"name": "A"}})
    at_end = _fin_with(["Agosto","Septiembre","Octubre"], [100]*3,
                       utilidad_neta=[100, 100, -50])
    html = build_html(at_end, {"ratios": {}, "forecast": {}, "variance": {}},
                      {"brand": {"name": "A"}})
    assert "recién fue rentable en los últimos" not in html
    assert "pérdida neta en 1 de 3 meses" in html      # the loss count itself stays

def test_month_names_escaped_in_table_header():
    fin = _fin_with(["<Mes>", "Febrero"], [100, 100])
    html = build_html(fin, {"ratios": {}, "forecast": {}, "variance": {}},
                      {"brand": {"name": "A"}})
    assert "<th class='r'><Mes></th>" not in html
    assert "&lt;Mes&gt;" in html


def test_report_break_even_nd_without_facturacion(fixture_workbook):
    # The fixture's PUNTO DE EQUILIBRIO has no "facturación necesaria" -> margenSeguridad None.
    # The report must show n/d, never a fabricated cushion (would contradict the silent lever).
    fin = build_financials(parse_workbook(fixture_workbook))
    assert fin["breakEven"]["margenSeguridad"] is None
    html = build_html(fin, {"ratios": {}, "forecast": {}, "variance": {}}, {"brand": {"name": "A"}})
    assert "Sin dato de equilibrio" in html
