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

def test_error_cells_flagged_as_warning(tmp_path):
    import openpyxl
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Resultados"
    ws.cell(1,1,"FLUJOS DE DINERO")
    for i,m in enumerate(["Enero","Febrero"]): ws.cell(3,2+i,m)
    ws.cell(4,1,"Ingresos"); ws.cell(4,2,1); ws.cell(4,3,1)
    ws.cell(9,1,"ESTADO DE RESULTADOS")
    for i,m in enumerate(["Enero","Febrero"]): ws.cell(11,2+i,m)
    ws.cell(12,1,"Ventas"); ws.cell(12,2,100); ws.cell(12,3,200)
    ws.cell(20,1,"Utilidad neta"); ws.cell(20,2,"#REF!"); ws.cell(20,3,"#REF!")
    p = tmp_path/"err.xlsx"; wb.save(str(p))
    from workbook import parse_workbook
    fin = parse_workbook(str(p))
    assert fin["incomeStatement"]["monthly"]["utilidadNeta"] == [0.0, 0.0]
    assert any("utilidad neta" in w.lower() for w in fin["warnings"])

def test_num_parses_es_ar_numeric_strings():
    from workbook import _num
    assert _num("$ 1.234,56") == 1234.56
    assert _num("1.234") == 1234          # es-AR thousands, not 1.234
    assert _num("-1.234,5") == -1234.5
    assert _num("1234.56") == 1234.56     # plain decimal point
    assert _num("1234") == 1234
    assert _num("(1.234)") == -1234       # parenthesized negative
    assert _num("12.345.678") == 12345678
    assert _num("0,5") == 0.5
    assert _num("abc") == 0               # unparseable text -> 0 (warned at line level)
    assert _num("#REF!") == 0
    assert _num("") == 0 and _num(None) == 0

def test_text_cells_flagged_as_warning(tmp_path):
    import openpyxl
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Resultados"
    ws.cell(1,1,"FLUJOS DE DINERO")
    for i,m in enumerate(["Enero","Febrero"]): ws.cell(3,2+i,m)
    ws.cell(4,1,"Ingresos"); ws.cell(4,2,1); ws.cell(4,3,1)
    ws.cell(9,1,"ESTADO DE RESULTADOS")
    for i,m in enumerate(["Enero","Febrero"]): ws.cell(11,2+i,m)
    ws.cell(12,1,"Ventas"); ws.cell(12,2,100); ws.cell(12,3,"abc")
    p = tmp_path/"txtcell.xlsx"; wb.save(str(p))
    fin = parse_workbook(str(p))
    assert fin["incomeStatement"]["monthly"]["ventas"] == [100.0, 0]
    assert any("texto no numérico" in w for w in fin["warnings"])

def test_currency_text_cells_parsed_not_zeroed(tmp_path):
    import openpyxl
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Resultados"
    ws.cell(1,1,"FLUJOS DE DINERO")
    for i,m in enumerate(["Enero","Febrero"]): ws.cell(3,2+i,m)
    ws.cell(4,1,"Ingresos"); ws.cell(4,2,1); ws.cell(4,3,1)
    ws.cell(9,1,"ESTADO DE RESULTADOS")
    for i,m in enumerate(["Enero","Febrero"]): ws.cell(11,2+i,m)
    ws.cell(12,1,"Ventas"); ws.cell(12,2,"$ 1.234,56"); ws.cell(12,3,200)
    p = tmp_path/"cur.xlsx"; wb.save(str(p))
    fin = parse_workbook(str(p))
    assert fin["incomeStatement"]["monthly"]["ventas"] == [1234.56, 200]
    assert not any("texto no numérico" in w for w in fin["warnings"])

def _wb_with_total(tmp_path, total_val):
    """2-month Estado de Resultados with a TOTAL column right after the months."""
    import openpyxl
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Resultados"
    ws.cell(1,1,"FLUJOS DE DINERO")
    for i,m in enumerate(["Enero","Febrero"]): ws.cell(3,2+i,m)
    ws.cell(4,1,"Ingresos"); ws.cell(4,2,1); ws.cell(4,3,1)
    ws.cell(9,1,"ESTADO DE RESULTADOS")
    for i,m in enumerate(["Enero","Febrero"]): ws.cell(11,2+i,m)
    ws.cell(11,4,"TOTAL")
    ws.cell(12,1,"Ventas"); ws.cell(12,2,100); ws.cell(12,3,200); ws.cell(12,4,total_val)
    p = tmp_path/"tot.xlsx"; wb.save(str(p))
    return str(p)

def test_parse_workbook_captures_total_column(tmp_path):
    fin = parse_workbook(_wb_with_total(tmp_path, 300))
    assert fin["incomeStatement"]["annualFromWorkbook"]["ventas"] == 300

def test_parse_workbook_omits_total_column_gracefully(fixture_workbook):
    fin = parse_workbook(fixture_workbook)   # fixture has no TOTAL/Anual header
    assert fin["incomeStatement"]["annualFromWorkbook"] is None

def test_parse_workbook_selects_latest_year(tmp_path):
    import openpyxl
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Resultados"
    yrs = [2025,2025,2026,2026]; mns = ["Enero","Febrero","Enero","Febrero"]
    # ESTADO: anchor row 9, year row 10, month header row 11
    ws.cell(9,1,"ESTADO DE RESULTADOS")
    for i,y in enumerate(yrs): ws.cell(10,2+i,y)
    for i,mn in enumerate(mns): ws.cell(11,2+i,mn)
    for i,v in enumerate([10,20,300,400]): ws.cell(12,2+i,v)  # 2025:10,20  2026:300,400
    ws.cell(12,1,"Ventas")
    # FLUJOS: anchor row 1, year row 2, month header row 3
    ws.cell(1,1,"FLUJOS DE DINERO")
    for i,y in enumerate(yrs): ws.cell(2,2+i,y)
    for i,mn in enumerate(mns): ws.cell(3,2+i,mn)
    ws.cell(4,1,"Ingresos")
    for i,v in enumerate([1,2,3,4]): ws.cell(4,2+i,v)
    p = tmp_path/"twoyr.xlsx"; wb.save(str(p))
    from workbook import parse_workbook
    fin = parse_workbook(str(p))
    assert fin["year"] == 2026
    assert fin["months"] == ["Enero","Febrero"]
    assert fin["incomeStatement"]["monthly"]["ventas"] == [300,400]   # 2026 only
    assert fin["cashFlow"]["monthly"]["ingresos"] == [3,4]

def test_sibling_block_without_year_row_does_not_collapse(tmp_path):
    import openpyxl
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Resultados"
    # ESTADO: 2-year, year row 10, months row 11
    ws.cell(9,1,"ESTADO DE RESULTADOS")
    for i,y in enumerate([2025,2025,2026,2026]): ws.cell(10,2+i,y)
    for i,mn in enumerate(["Enero","Febrero","Enero","Febrero"]): ws.cell(11,2+i,mn)
    ws.cell(12,1,"Ventas")
    for i,v in enumerate([10,20,300,400]): ws.cell(12,2+i,v)
    # FLUJOS: single-year, NO year row (month header right under anchor)
    ws.cell(1,1,"FLUJOS DE DINERO")
    for i,mn in enumerate(["Enero","Febrero"]): ws.cell(2,2+i,mn)
    ws.cell(3,1,"Ingresos"); ws.cell(3,2,7); ws.cell(3,3,8)
    p = tmp_path/"sib.xlsx"; wb.save(str(p))
    from workbook import parse_workbook
    fin = parse_workbook(str(p))
    assert fin["year"] == 2026
    assert fin["incomeStatement"]["monthly"]["ventas"] == [300,400]
    # sibling FLUJOS must NOT collapse to []
    assert fin["cashFlow"]["monthly"]["ingresos"] == [7,8]

def test_text_year_headers_are_parsed(tmp_path):
    import openpyxl
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Resultados"
    ws.cell(9,1,"ESTADO DE RESULTADOS")
    for i,y in enumerate(["2025","2025","2026","2026"]): ws.cell(10,2+i,y)  # TEXT years
    for i,mn in enumerate(["Enero","Febrero","Enero","Febrero"]): ws.cell(11,2+i,mn)
    ws.cell(12,1,"Ventas")
    for i,v in enumerate([10,20,300,400]): ws.cell(12,2+i,v)
    ws.cell(1,1,"FLUJOS DE DINERO")
    for i,mn in enumerate(["Enero","Febrero"]): ws.cell(2,2+i,mn)
    ws.cell(3,1,"Ingresos"); ws.cell(3,2,1); ws.cell(3,3,1)
    p = tmp_path/"txt.xlsx"; wb.save(str(p))
    from workbook import parse_workbook
    fin = parse_workbook(str(p))
    assert fin["year"] == 2026
    assert fin["incomeStatement"]["monthly"]["ventas"] == [300,400]  # not all 4 summed
