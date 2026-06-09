"""Accent/case-insensitive label tools for parsing the accounting workbook."""
import unicodedata

MONTHS = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
          "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
_MONTHSET = {m.lower() for m in MONTHS}

def normalize(s):
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())

def col_a_index(ws):
    """normalized column-A label -> row number (first occurrence)."""
    idx = {}
    for row in ws.iter_rows(min_col=1, max_col=1):
        c = row[0]
        if isinstance(c.value, str):
            key = normalize(c.value)
            if key and key not in idx:
                idx[key] = c.row
    return idx

def find_month_header(ws, after_row, search=6):
    """Find the row at/after `after_row` whose cells are the month names.
    Returns (row, start_col, months_present)."""
    for r in range(after_row, after_row + search + 1):
        for col in range(2, 6):
            if normalize(ws.cell(r, col).value) in _MONTHSET:
                months, c = [], col
                while normalize(ws.cell(r, c).value) in _MONTHSET:
                    months.append(ws.cell(r, c).value)
                    c += 1
                return r, col, months
    raise ValueError(f"no month header found after row {after_row}")
