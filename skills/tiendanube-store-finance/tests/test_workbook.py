from workbook import read_statement_block, parse_workbook

def test_read_estado_de_resultados(fixture_workbook):
    block = read_statement_block(
        fixture_workbook, "Resultados", "ESTADO DE RESULTADOS",
        ["Ventas","Costo reposición","Utilidad bruta","Costos fijos",
         "Utilidad operativa","Utilidad neta"])
    assert block["months"][0] == "Enero" and len(block["months"]) == 12
    assert block["lines"]["ventas"] == [1000]*12
    assert block["lines"]["costo reposicion"] == [400]*12
    assert "amortizacion creditos" not in block["lines"]  # not requested

def test_parse_workbook_assembles_sections(fixture_workbook):
    fin = parse_workbook(fixture_workbook)
    assert fin["incomeStatement"]["monthly"]["ventas"] == [1000]*12
    assert fin["cashFlow"]["monthly"]["total"] == [40]*12
    assert fin["breakEven"]["margenBrutoMonthly"] == [0.6]*12
