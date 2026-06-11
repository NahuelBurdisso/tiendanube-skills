"""Inline SVG charts for the finance report — zero dependencies, render in headless
Chrome. Editorial-financial palette (burgundy/gold on cream) passed in by the report.
All charts return an SVG string sized by viewBox so CSS scales them to the column."""
import html as _html


def _t(x, y, s, size=7, fill="#61574A", anchor="middle", font="Archivo", weight="400"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-family="{font}" '
            f'font-weight="{weight}">{_html.escape(str(s))}</text>')


def bars(values, labels, accent, warm, money, w=540, h=150, pad=24, highlight=None):
    """Vertical bars; `highlight` is an index drawn in the warm accent + value label."""
    mx = max(values + [1])
    gap = (w - pad) / len(values)
    bw = gap * 0.58
    out = [f'<svg viewBox="0 0 {w} {h + 28}" class="chart">'
           f'<line x1="{pad}" y1="{h}" x2="{w}" y2="{h}" stroke="#D9CFBE"/>']
    for i, (v, lb) in enumerate(zip(values, labels)):
        bh = (v / mx) * (h - pad)
        x = pad + i * gap + (gap - bw) / 2
        y = h - bh
        hi = (highlight == i)
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" '
                   f'height="{max(0, bh):.1f}" fill="{warm if hi else accent}" rx="1"/>')
        out.append(_t(x + bw / 2, h + 10, lb, 6.4))
        out.append(_t(x + bw / 2, y - 3, money(v), 6.4, accent, font="Bodoni Moda", weight="600"))
    return "".join(out) + "</svg>"


def lines(series, x_labels, names, colors, w=540, h=165, pad=28):
    """Multiple line series sharing the same x axis. Values are plotted on a shared
    scale (use comparable units, e.g. percentages 0..1). Includes a legend."""
    flat = [v for s in series for v in s]
    mx = max(flat + [0.0001])
    n = len(x_labels)
    sx = lambda i: pad + i * (w - pad - 8) / max(1, n - 1)
    sy = lambda v: (h - pad) - (v / mx) * (h - 2 * pad)
    out = [f'<svg viewBox="0 0 {w} {h}" class="chart">',
           f'<line x1="{pad}" y1="{h - pad}" x2="{w - 8}" y2="{h - pad}" stroke="#D9CFBE"/>']
    for ser, col in zip(series, colors):
        pts = " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(ser))
        out.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="1.7"/>')
        for i, v in enumerate(ser):
            out.append(f'<circle cx="{sx(i):.1f}" cy="{sy(v):.1f}" r="1.7" fill="{col}"/>')
    for i, lb in enumerate(x_labels):
        out.append(_t(sx(i), h - pad + 10, lb, 6.4))
    lx = pad
    for nm, col in zip(names, colors):
        out.append(f'<rect x="{lx:.0f}" y="4" width="7" height="7" fill="{col}" rx="1"/>')
        out.append(_t(lx + 10, 10.5, nm, 7, "#2A211A", anchor="start", weight="500"))
        lx += 11 + len(nm) * 4.4 + 14
    return "".join(out) + "</svg>"


def waterfall(items, accent, warm, neg_col, money, w=540, h=205, pad=26):
    """P&L cascade. items = [(label, value, type)] with type in
    'start' | 'neg' | 'total'. Decreases float down from the running total."""
    run = 0.0
    spans = []
    for _, v, t in items:
        if t == "start":
            lo, hi = 0.0, v
            run = v
        elif t == "neg":
            lo, hi = run - v, run
            run -= v
        else:  # total — absolute marker
            lo, hi = 0.0, v
            run = v
        spans.append((lo, hi))
    mx = max([hi for _, hi in spans] + [1])
    n = len(items)
    gap = (w - pad) / n
    bw = gap * 0.6
    base = h - pad
    sc = (h - 2 * pad) / mx
    out = [f'<svg viewBox="0 0 {w} {h + 18}" class="chart">']
    for i, ((lb, v, t), (lo, hi)) in enumerate(zip(items, spans)):
        x = pad + i * gap + (gap - bw) / 2
        y = base - hi * sc
        ht = max(1.0, (hi - lo) * sc)
        col = neg_col if t == "neg" else (warm if t == "total" else accent)
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{ht:.1f}" fill="{col}" rx="1"/>')
        out.append(_t(x + bw / 2, base + 9, lb, 5.8))
        sign = "−" if t == "neg" else ""
        out.append(_t(x + bw / 2, y - 3, sign + money(v), 5.9, col, font="Bodoni Moda", weight="600"))
    return "".join(out) + "</svg>"


def stacked_bar(segments, w=540, h=52):
    """A single 100%-width bar split into segments + a legend row below.
    segments = [(label, value, color)]."""
    tot = sum(v for _, v, _ in segments) or 1
    x = 0.0
    out = [f'<svg viewBox="0 0 {w} {h}" class="chart">']
    for lb, v, col in segments:
        sw = v / tot * w
        out.append(f'<rect x="{x:.1f}" y="0" width="{sw:.1f}" height="20" fill="{col}"/>')
        if sw > 26:
            out.append(_t(x + sw / 2, 13.5, f"{v / tot * 100:.0f}%", 7.5, "#FBF8F2", weight="700"))
        x += sw
    lx = 0.0
    for lb, v, col in segments:
        out.append(f'<rect x="{lx:.0f}" y="30" width="7" height="7" fill="{col}" rx="1"/>')
        out.append(_t(lx + 10, 36.5, lb, 6.6, "#2A211A", anchor="start"))
        lx += 11 + len(lb) * 3.6 + 18
    return "".join(out) + "</svg>"


def cashflow(net, cumulative, labels, accent, warm, neg_col, money, w=540, h=172, pad=28):
    """Monthly net cash as bars around a zero axis + the cumulative cash curve as a
    line. Reveals cash troughs even in profitable periods."""
    vals = list(net) + list(cumulative) + [0.0]
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1
    sy = lambda v: pad + ((hi - v) / rng) * (h - 2 * pad)
    n = len(labels)
    gap = (w - pad) / n
    bw = gap * 0.46
    zy = sy(0)
    out = [f'<svg viewBox="0 0 {w} {h + 14}" class="chart">',
           f'<line x1="{pad}" y1="{zy:.1f}" x2="{w}" y2="{zy:.1f}" stroke="#C9BBA2"/>']
    for i, (v, lb) in enumerate(zip(net, labels)):
        x = pad + i * gap + (gap - bw) / 2
        top = min(sy(v), zy)
        ht = max(1.0, abs(sy(v) - zy))
        out.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{ht:.1f}" '
                   f'fill="{accent if v >= 0 else neg_col}" rx="1"/>')
        out.append(_t(x + bw / 2, h + 7, lb, 6))
    sx = lambda i: pad + i * gap + gap / 2
    pts = " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(cumulative))
    out.append(f'<polyline points="{pts}" fill="none" stroke="{warm}" stroke-width="1.9"/>')
    for i, v in enumerate(cumulative):
        out.append(f'<circle cx="{sx(i):.1f}" cy="{sy(v):.1f}" r="1.9" fill="{warm}"/>')
        out.append(_t(sx(i), sy(v) - 4, money(v), 5.6, warm, font="Bodoni Moda", weight="600"))
    out.append(f'<rect x="{pad:.0f}" y="2" width="7" height="7" fill="{accent}" rx="1"/>'
               + _t(pad + 10, 8, "Caja neta mensual", 6.6, "#2A211A", anchor="start"))
    out.append(f'<rect x="{pad+126:.0f}" y="2" width="7" height="7" fill="{warm}" rx="1"/>'
               + _t(pad + 136, 8, "Caja acumulada", 6.6, "#2A211A", anchor="start"))
    return "".join(out) + "</svg>"


def dual_bars(labels, nominal, real, accent, warm, money, w=540, h=160, pad=26):
    """Paired nominal vs real bars per period — the headline 'pesos corrientes vs
    moneda de cierre' comparison. `real` entries may be None (IPC gap) → drawn as the
    nominal bar only, no real twin."""
    allv = [v for v in (list(nominal) + [r for r in real if r is not None]) if v is not None]
    mx = max(allv + [1])
    n = len(labels)
    gw = (w - pad) / n
    bw = gw * 0.66 / 2
    base = h - pad
    out = [f'<svg viewBox="0 0 {w} {h + 26}" class="chart">'
           f'<line x1="{pad}" y1="{base}" x2="{w}" y2="{base}" stroke="#D9CFBE"/>']
    for i, lb in enumerate(labels):
        gx = pad + i * gw + gw * 0.17
        pairs = [(nominal[i] if i < len(nominal) else 0, accent),
                 (real[i] if i < len(real) else None, warm)]
        for si, (v, col) in enumerate(pairs):
            if v is None:
                continue
            bh = (v / mx) * (h - pad)
            out.append(f'<rect x="{gx + si * bw:.1f}" y="{base - bh:.1f}" width="{bw * 0.86:.1f}" '
                       f'height="{max(0, bh):.1f}" fill="{col}" rx="1"/>')
        out.append(_t(gx + bw, base + 10, lb, 6.2))
    for lx0, nm, col in ((pad, "Nominal", accent), (pad + 80, "Real (cierre)", warm)):
        out.append(f'<rect x="{lx0:.0f}" y="4" width="7" height="7" fill="{col}" rx="1"/>')
        out.append(_t(lx0 + 10, 10.5, nm, 7, "#2A211A", anchor="start", weight="500"))
    return "".join(out) + "</svg>"


def tornado(items, accent, money, w=540, rowh=18, pad=26):
    """Horizontal bars sorted by |value| desc — levers ranked by impact.
    items = [(label, value)]."""
    items = sorted(items, key=lambda kv: abs(kv[1]), reverse=True)
    mx = max([abs(v) for _, v in items] + [1])
    h = pad + rowh * len(items) + 6
    barx = 150.0
    out = [f'<svg viewBox="0 0 {w} {h}" class="chart">']
    for i, (lb, v) in enumerate(items):
        y = pad + i * rowh
        bw = (abs(v) / mx) * (w - barx - 70)
        out.append(_t(barx - 6, y + rowh * 0.62, lb, 7, "#2A211A", anchor="end", weight="500"))
        out.append(f'<rect x="{barx}" y="{y + 2:.1f}" width="{bw:.1f}" height="{rowh - 6}" '
                   f'fill="{accent}" rx="1"/>')
        out.append(_t(barx + bw + 4, y + rowh * 0.62, money(v), 6.6, accent,
                      anchor="start", font="Bodoni Moda", weight="600"))
    return "".join(out) + "</svg>"


def grouped_bars(groups, series_names, colors, accent, money, w=540, h=160, pad=26):
    """Grouped vertical bars. groups = [(group_label, [v1, v2, ...])] one value per
    series. Used for base/bull/bear scenario comparison."""
    allv = [v for _, vs in groups for v in vs]
    mx = max(allv + [1])
    ng = len(groups)
    gw = (w - pad) / ng
    k = len(series_names)
    bw = gw * 0.66 / k
    base = h - pad
    out = [f'<svg viewBox="0 0 {w} {h + 26}" class="chart">'
           f'<line x1="{pad}" y1="{base}" x2="{w}" y2="{base}" stroke="#D9CFBE"/>']
    for gi, (glabel, vs) in enumerate(groups):
        gx = pad + gi * gw + gw * 0.17
        for si, v in enumerate(vs):
            x = gx + si * bw
            bh = (v / mx) * (h - pad)
            out.append(f'<rect x="{x:.1f}" y="{base - bh:.1f}" width="{bw * 0.86:.1f}" '
                       f'height="{max(0, bh):.1f}" fill="{colors[si]}" rx="1"/>')
        out.append(_t(gx + (k * bw) / 2, base + 10, glabel, 7, "#2A211A", weight="500"))
    lx = pad
    for nm, col in zip(series_names, colors):
        out.append(f'<rect x="{lx:.0f}" y="4" width="7" height="7" fill="{col}" rx="1"/>')
        out.append(_t(lx + 10, 10.5, nm, 7, "#2A211A", anchor="start"))
        lx += 11 + len(nm) * 4.4 + 16
    return "".join(out) + "</svg>"
