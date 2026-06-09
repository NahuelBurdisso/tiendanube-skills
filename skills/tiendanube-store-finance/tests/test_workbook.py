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
