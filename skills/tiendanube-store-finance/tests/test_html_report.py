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


def test_report_break_even_nd_without_facturacion(fixture_workbook):
    # The fixture's PUNTO DE EQUILIBRIO has no "facturación necesaria" -> margenSeguridad None.
    # The report must show n/d, never a fabricated cushion (would contradict the silent lever).
    fin = build_financials(parse_workbook(fixture_workbook))
    assert fin["breakEven"]["margenSeguridad"] is None
    html = build_html(fin, {"ratios": {}, "forecast": {}, "variance": {}}, {"brand": {"name": "A"}})
    assert "Sin dato de equilibrio" in html
