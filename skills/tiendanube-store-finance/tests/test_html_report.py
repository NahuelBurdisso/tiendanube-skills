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
    for section in ["Resumen ejecutivo", "Estado de resultados", "Punto de equilibrio",
                    "Proyección y escenarios", "Variación mensual", "Cascada de resultados"]:
        assert section in html, f"missing section: {section}"
    assert html.count("<svg") >= 3      # revenue bars + waterfall + margin lines at minimum
    assert "Run-rate anualizado" in html
