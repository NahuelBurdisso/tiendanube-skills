#!/usr/bin/env python3
"""xlsx-only orchestrator: workbook + config -> financials.json + results + xlsx + html.
Statements are READ from the workbook and reconciled; analyses augment them."""
import json, pathlib, argparse
from workbook import parse_workbook
from financials import build_financials
from fiscal import apply_fiscal
from restatement import restate
from levers import build_levers
from measures import nom
from adapters import to_forecast_input, to_ratios_input, to_variance_input
from run_scripts import run_script
from ratios_filter import filter_ratios
from xlsx_report import write_xlsx
from html_report import build_html

def run(workbook_path, config_path, out_dir):
    out_dir = pathlib.Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(pathlib.Path(config_path).read_text()) if config_path else {}
    fin_cfg = cfg.get("finance", {})

    fin = build_financials(parse_workbook(workbook_path),
                           store_name=cfg.get("brand", {}).get("name"))
    fin = apply_fiscal(fin, cfg)  # taxes on NOMINAL (AFIP basis)
    fin = restate(fin, fin_cfg)   # reexpresión a moneda de cierre — ALWAYS last
    fin_path = out_dir / "financials.json"; fin_path.write_text(json.dumps(fin, indent=1))

    results = {}
    results["forecast"] = run_script("forecast_builder.py",
                                     to_forecast_input(fin, fin_cfg), out_dir)
    raw_ratios = run_script("ratio_calculator.py", to_ratios_input(fin), out_dir)
    results["ratios"] = filter_ratios(raw_ratios)  # handles the nested categories shape
    var_in = to_variance_input(fin)
    var_out = run_script("budget_variance_analyzer.py", var_in, out_dir)
    var_out["line_items"] = var_in["line_items"]  # keep raw pairs for the xlsx tab
    results["variance"] = var_out
    results["levers"] = build_levers(fin, cfg)
    if fin_cfg.get("enableDcf"):
        ventas_nom = [nom(x) for x in fin["incomeStatement"]["monthly"]["ventas"]]
        results["dcf"] = run_script("dcf_valuation.py",
                                    {"historical": {"revenue": ventas_nom},
                                     "assumptions": {"wacc_inputs": fin_cfg.get("wacc", {})}}, out_dir)

    xlsx = out_dir / "store-finance.xlsx"; write_xlsx(fin, results, str(xlsx))
    html = out_dir / "report.html"; html.write_text(build_html(fin, results, cfg))
    return {"financials": str(fin_path), "xlsx": str(xlsx),
            "html": str(html), "results": results}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workbook")
    ap.add_argument("--config", default="report.config.json")
    ap.add_argument("--out", default=".")
    args = ap.parse_args()
    cfg = args.config if pathlib.Path(args.config).exists() else None
    out = run(args.workbook, cfg, args.out)
    print(json.dumps({k: out[k] for k in ("financials","xlsx","html")}, indent=1))

if __name__ == "__main__":
    main()
