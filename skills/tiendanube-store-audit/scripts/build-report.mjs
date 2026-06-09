#!/usr/bin/env node
// Builds a branded HTML report from ./analysis.json. Render to PDF with render.sh (headless Chrome).
// Optional ./report.config.json: { brand:{ name, accent, accentWarm, preparedFor, locale, currencySymbol } }
import fs from 'fs'
const d = JSON.parse(fs.readFileSync('analysis.json', 'utf8'))
const cfg = fs.existsSync('report.config.json') ? JSON.parse(fs.readFileSync('report.config.json', 'utf8')) : {}
const B = Object.assign({ name: d.store.name || 'TIENDA', accent: '#6B2532', accentWarm: '#B08858', preparedFor: '', locale: 'es-AR', currencySymbol: '$' }, cfg.brand || {})

const fmt = n => Math.round(n).toLocaleString(B.locale)
// adaptive: big stores read in millions, small stores in thousands
const M = n => {
  const a = Math.abs(n), s = B.currencySymbol
  if (a >= 1e6) return s + (n / 1e6).toFixed(a >= 1e7 ? 0 : 1).replace('.', ',') + 'M'
  if (a >= 1e3) return s + Math.round(n / 1e3) + 'k'
  return s + Math.round(n)
}
const pc = n => Math.round(n) + '%'

// ---------- SVG charts ----------
function vbars(data, getV, getL, { w = 540, h = 150, pad = 22, hi = null, fmtV = M } = {}) {
  const max = Math.max(...data.map(getV), 1), gap = (w - pad) / data.length, bw = gap * 0.62
  let s = `<svg viewBox="0 0 ${w} ${h + 30}" class="chart"><line x1="${pad}" y1="${h}" x2="${w}" y2="${h}" stroke="#D9CFBE"/>`
  data.forEach((dd, i) => {
    const v = getV(dd), bh = v / max * (h - pad), x = pad + i * gap + (gap - bw) / 2, y = h - bh
    const c = hi && hi(dd) ? B.accentWarm : B.accent
    s += `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${bw.toFixed(1)}" height="${Math.max(0,bh).toFixed(1)}" fill="${c}" rx="1"/>`
    s += `<text x="${(x + bw / 2).toFixed(1)}" y="${h + 11}" font-size="6.5" fill="#61574A" text-anchor="middle" font-family="Archivo">${getL(dd)}</text>`
    if (hi && hi(dd)) s += `<text x="${(x + bw / 2).toFixed(1)}" y="${(y - 3).toFixed(1)}" font-size="6.5" fill="${B.accent}" text-anchor="middle" font-family="Bodoni Moda" font-weight="600">${fmtV(v)}</text>`
  })
  return s + '</svg>'
}
function hbars(data, { w = 540, rowh = 26, labelW = 175 } = {}) {
  const max = Math.max(...data.map(x => x.val), 1), barMax = w - labelW - 75
  let s = `<svg viewBox="0 0 ${w} ${data.length * rowh + 6}" class="chart">`
  data.forEach((dd, i) => {
    const y = i * rowh + 4, bw = dd.val / max * barMax
    s += `<text x="0" y="${y + 12}" font-size="8" fill="#2A211A" font-family="Archivo" font-weight="500">${dd.label}</text>`
    s += `<rect x="${labelW}" y="${y + 3}" width="${bw.toFixed(1)}" height="13" fill="${dd.color || B.accent}" rx="2"/>`
    s += `<text x="${labelW + bw + 5}" y="${y + 13}" font-size="8" fill="#2A211A" font-family="Bodoni Moda" font-weight="600">${dd.right}</text>`
  })
  return s + '</svg>'
}

const yearChart = vbars(d.yearly.slice(-5), y => y.rev, y => y.y, { hi: y => y === d.yearly[d.yearly.length - 1] })
const monthLab = m => { const [y, mo] = m.m.split('-'); return mo + '/' + y.slice(2) }
const maxMonth = Math.max(...d.monthly.map(m => m.rev))
const monthChart = vbars(d.monthly, m => m.rev, monthLab, { hi: m => m.rev === maxMonth })
const gatewayChart = hbars(d.gateway.filter(g => g.pct >= 1).map(g => ({ label: g.g, val: g.rev, right: M(g.rev) + ' · ' + pc(g.pct), color: g.g.includes('offline') || g.g.includes('transfer') ? B.accentWarm : B.accent })))
const leakChart = hbars([
  { label: 'Carritos abandonados /año', val: d.leaks.abandoned.annualized, right: M(d.leaks.abandoned.annualized) },
  { label: 'Pedidos sin pagar (histórico)', val: d.leaks.pending.val, right: M(d.leaks.pending.val) },
  { label: 'Cancelados (histórico)', val: d.leaks.cancelled.val, right: M(d.leaks.cancelled.val) },
])
const leverChart = hbars(d.levers.map(l => ({ label: l.name.length > 36 ? l.name.slice(0, 35) + '…' : l.name, val: l.val, right: M(l.val) })), { rowh: 24 })
const leverRows = d.levers.map(l => `<tr><td><b>${l.name}</b><br><span class="note">${l.assume}</span></td><td class="r">${M(l.val)}</td><td><span class="pill p-${l.eff === 'Bajo' ? 'good' : 'warn'}">${l.eff}</span></td></tr>`).join('')
const riskRows = d.levers.map(l => `<tr><td>${l.name.replace(/ \(.*\)/, '').slice(0,40)}</td><td>${l.assume}</td><td><span class="pill p-${l.risk === 'alto' ? 'bad' : l.risk === 'medio' ? 'warn' : 'good'}">${l.risk}</span></td></tr>`).join('')

const ab = d.leaks.abandoned, p = d.products, c = d.customers
const html = `<!DOCTYPE html><html lang="${B.locale}"><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400;0,6..96,500;0,6..96,600;0,6..96,700;1,6..96,500&family=Archivo:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#F4EFE6;--surface:#FBF8F2;--deep:#EAE2D4;--text:#2A211A;--ink:#1A1512;--muted:#61574A;--accent:${B.accent};--warm:${B.accentWarm};--line:#D9CFBE;--good:#3F6B4A;--warn:#9A6B1E;--bad:#8C2D2D}
*{box-sizing:border-box;margin:0;padding:0}@page{size:A4;margin:18mm 0 16mm 0}
html{-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{font-family:'Archivo',sans-serif;color:var(--text);background:var(--bg);font-size:10.2px;line-height:1.55}
.page{padding:0 18mm}h1,h2,h3,h4{font-family:'Bodoni Moda',serif;font-weight:500;letter-spacing:-.01em;color:var(--ink)}
.label{text-transform:uppercase;letter-spacing:.22em;font-size:8px;font-weight:600;color:var(--muted)}
.accent{color:var(--accent)}
.cover{height:261mm;display:flex;flex-direction:column;justify-content:space-between;padding:24mm 18mm;page-break-after:always;position:relative}
.cover .wordmark{font-family:'Bodoni Moda';font-weight:600;font-size:13px;letter-spacing:.5em;text-transform:uppercase}
.cover .rule{height:1px;background:var(--line);margin:6mm 0}
.cover h1{font-size:52px;line-height:1.04;margin-top:auto}.cover h1 .it{font-style:italic;color:var(--accent)}
.cover .sub{font-size:13px;color:var(--muted);margin-top:8mm;max-width:128mm;line-height:1.6}
.cover .meta{margin-top:14mm;display:flex;gap:14mm}
.cover .bigstat{position:absolute;right:18mm;top:58mm;text-align:right}
.cover .bigstat .n{font-family:'Bodoni Moda';font-size:50px;color:var(--accent);line-height:1}
.cover .bigstat .c{font-size:9px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-top:1mm}
.section-open{page-break-before:always;padding-top:6mm}
.kicker{display:flex;align-items:center;gap:8px;margin-bottom:4mm}.kicker .num{font-family:'Bodoni Moda';font-size:13px;color:var(--accent)}
h2.report{font-size:29px;line-height:1.05;margin-bottom:3mm}
.lede{font-size:11.5px;color:var(--muted);max-width:155mm;line-height:1.6;margin-bottom:6mm}
h3{font-size:15px;margin:7mm 0 3mm;padding-bottom:2mm;border-bottom:1px solid var(--line)}h3 .label{float:right;padding-top:4px}
p{margin-bottom:2.5mm}.note{color:var(--muted)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:3mm;margin:4mm 0 6mm}
.stat{background:var(--surface);border:1px solid var(--line);padding:4mm}
.stat .n{font-family:'Bodoni Moda';font-size:20px;color:var(--ink);line-height:1}.stat .n.accent{color:var(--accent)}
.stat .c{font-size:8.3px;color:var(--muted);margin-top:2mm;line-height:1.4}
table{width:100%;border-collapse:collapse;margin:3mm 0 5mm;font-size:9.4px}
th{text-align:left;font-weight:600;text-transform:uppercase;letter-spacing:.08em;font-size:8px;color:var(--muted);border-bottom:1.5px solid var(--ink);padding:2mm 2.5mm}
td{padding:2.4mm 2.5mm;border-bottom:1px solid var(--line);vertical-align:top}tr{page-break-inside:avoid}
td.r,th.r{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.pill{display:inline-block;padding:1px 6px;border-radius:10px;font-size:7.5px;font-weight:600;letter-spacing:.04em;text-transform:uppercase}
.p-bad{background:#f3dede;color:var(--bad)}.p-warn{background:#f3e7d0;color:var(--warn)}.p-good{background:#dfe9e0;color:var(--good)}.p-info{background:var(--deep);color:var(--text)}
.callout{background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--accent);padding:4mm 5mm;margin:4mm 0;page-break-inside:avoid}
.callout h4{font-size:13px;margin-bottom:2mm}
.chartbox{background:var(--surface);border:1px solid var(--line);padding:5mm;margin:3mm 0 5mm;page-break-inside:avoid}
.chartbox .ct{font-size:8px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600;margin-bottom:3mm}
svg.chart{width:100%;height:auto;display:block}
ul.check{list-style:none}ul.check li{position:relative;padding-left:7mm;margin-bottom:2.2mm;page-break-inside:avoid}ul.check li:before{content:"—";position:absolute;left:0;color:var(--accent)}
.bignum{font-family:'Bodoni Moda';font-size:40px;color:var(--accent);line-height:1}
.footer-note{margin-top:8mm;padding-top:4mm;border-top:1px solid var(--line);font-size:8.3px;color:var(--muted)}
</style></head><body>

<div class="cover">
  <div><div class="wordmark">${B.name}</div><div class="rule"></div><div class="label">Informe de mejoras · Tienda online</div></div>
  <div class="bigstat"><div class="n">+${M(d.totalUpside)}</div><div class="c">de ingreso anual identificado</div></div>
  <div>
    <h1>Dónde está<br>la plata, y cómo<br><span class="it">capturarla</span>.</h1>
    <p class="sub">Análisis sobre datos reales de la tienda: crecimiento, de dónde entra el dinero, qué se fuga, y las palancas concretas para facturar más. Cada número trae su supuesto.</p>
    <div class="meta">
      ${B.preparedFor ? `<div><span class="label">Para</span><div style="font-size:12px;margin-top:2mm">${B.preparedFor}</div></div>` : ''}
      <div><span class="label">Tienda</span><div style="font-size:12px;margin-top:2mm">${(d.store.domain||'').replace(/^https?:\/\//,'')}</div></div>
      <div><span class="label">Generado</span><div style="font-size:12px;margin-top:2mm">${d.generatedAt.slice(0,10)}</div></div>
    </div>
  </div>
</div>

<div class="page section-open">
  <div class="kicker"><span class="num">00</span><span class="label">La tesis</span></div>
  <h2 class="report">Una tienda de <span class="accent">${M(d.runRate)}/año</span> con <span class="accent">+${M(d.totalUpside)}/año</span> arriba de la mesa.</h2>
  <p class="lede">La tienda factura a un ritmo de ~${M(d.runRate)} al año. Hay ingreso que hoy no se captura — plata que se fuga y palancas sin activar. Sumadas con supuestos conservadores, son <b>+${M(d.totalUpside)} al año</b>.</p>
  <div class="stats">
    <div class="stat"><div class="n accent">${M(d.lifetime.rev)}</div><div class="c">Facturado histórico · ${fmt(d.lifetime.orders)} pedidos pagos</div></div>
    <div class="stat"><div class="n">${B.currencySymbol}${fmt(d.lifetime.aov)}</div><div class="c">Ticket promedio (AOV)</div></div>
    <div class="stat"><div class="n accent">~${M(d.runRate)}</div><div class="c">Ritmo anual (últimos 12 meses)</div></div>
    <div class="stat"><div class="n">${c.repeatPct}%</div><div class="c">Recompra · ${fmt(c.oneTime)} compran una sola vez</div></div>
  </div>
  <div class="chartbox"><div class="ct">Palancas de ingreso — ${B.currencySymbol} anual estimado (conservador)</div>${leverChart}</div>
</div>

<div class="page section-open">
  <div class="kicker"><span class="num">01</span><span class="label">El motor</span></div>
  <h2 class="report">Cómo viene el negocio.</h2>
  <p class="lede">La foto del motor: crecimiento y estacionalidad. Define cuándo y dónde empujar.</p>
  <div class="chartbox"><div class="ct">Facturación por año — último año en dorado</div>${yearChart}</div>
  <div class="chartbox"><div class="ct">Facturación mensual (últimos 15 meses) — pico en dorado</div>${monthChart}</div>
  <div class="chartbox"><div class="ct">Facturación por medio de pago</div>${gatewayChart}</div>
</div>

<div class="page section-open">
  <div class="kicker"><span class="num">02</span><span class="label">Las fugas</span></div>
  <h2 class="report">La plata que hoy se escapa.</h2>
  <p class="lede">Las canillas abiertas. La más grande suele ser recurrente: carritos que se abandonan mes a mes.</p>
  <div class="chartbox"><div class="ct">Fugas de ingreso — abandonados anualizados vs. acumulado histórico</div>${leakChart}</div>
  <table>
    <tr><th>Fuga</th><th>Ventana</th><th class="r">Monto</th><th>Recuperable</th></tr>
    <tr><td><b>Carritos abandonados</b></td><td>${ab.n} en ~${ab.windowDays} días</td><td class="r">${M(ab.val)} · ${M(ab.annualized)}/año</td><td><span class="pill p-good">${ab.withEmail}/${ab.n} con email</span></td></tr>
    <tr><td><b>Pedidos sin pagar</b></td><td>${d.leaks.pending.n} pedidos</td><td class="r">${M(d.leaks.pending.val)}</td><td><span class="pill p-warn">recordatorio</span></td></tr>
    <tr><td><b>Cancelados</b></td><td>${d.leaks.cancelled.n} pedidos</td><td class="r">${M(d.leaks.cancelled.val)}</td><td><span class="pill p-info">parcial</span></td></tr>
  </table>
</div>

<div class="page section-open">
  <div class="kicker"><span class="num">03</span><span class="label">El plan de ingresos</span></div>
  <h2 class="report">Palancas para facturar más.</h2>
  <p class="lede">El corazón del informe. Cada palanca con su número, su supuesto y su esfuerzo.</p>
  <div style="display:flex;align-items:baseline;gap:5mm;margin:2mm 0 4mm"><div class="bignum">+${M(d.totalUpside)}</div><div class="note" style="max-width:110mm">de ingreso anual potencial, supuestos conservadores, sobre ~${M(d.runRate)}/año.</div></div>
  <table><tr><th>Palanca</th><th class="r">${B.currencySymbol}/año</th><th>Esfuerzo</th></tr>${leverRows}
    <tr style="border-top:2px solid var(--ink)"><td><b>TOTAL identificado</b></td><td class="r"><b>${M(d.totalUpside)}</b></td><td></td></tr></table>
</div>

<div class="page section-open">
  <div class="kicker"><span class="num">04</span><span class="label">Operativa y catálogo</span></div>
  <h2 class="report">Estado operativo de la tienda.</h2>
  <p class="lede">Lo que hace que el dinero entre (o no): calidad de catálogo, SEO, stock y estructura.</p>
  <div class="stats">
    <div class="stat"><div class="n">${fmt(p.total)}</div><div class="c">Productos · ${p.published} publicados</div></div>
    <div class="stat"><div class="n ${p.nullp?'accent':''}">${p.nullp}</div><div class="c">Precios en ${B.currencySymbol}0 (bug visible)</div></div>
    <div class="stat"><div class="n ${p.deadPub?'accent':''}">${p.deadPub}</div><div class="c">Publicados sin stock (vidriera muerta)</div></div>
    <div class="stat"><div class="n ${p.noSeoDescription===p.total?'accent':''}">${p.noSeoTitle}/${p.total}</div><div class="c">Sin título SEO · ${p.noSeoDescription} sin descripción</div></div>
  </div>
  <table>
    <tr><th>Punto</th><th class="r">Dato</th><th>Lectura</th></tr>
    <tr><td>Productos sin foto / con 1 sola</td><td class="r">${p.noImg} / ${p.single}</td><td>Sumar imágenes sube conversión</td></tr>
    <tr><td>Precio promocional (tachado) cargado</td><td class="r">${p.promo}/${p.total}</td><td>${p.promo < p.total*0.1 ? 'Sin precio tachado, las ofertas no se ven' : 'OK'}</td></tr>
    <tr><td>Atributo de talle cargado</td><td class="r">${p.talleAttr}/${p.total}</td><td>Sin talle no hay filtro ni guía</td></tr>
    <tr><td>Peso y medidas (cotización de envío)</td><td class="r">${p.weightDims}/${p.total}</td><td>${p.total-p.weightDims} cotizan mal el envío</td></tr>
    <tr><td>Capital inmovilizado en stock</td><td class="r">${M(p.invValue)}</td><td>Lo que no rota es caja dormida</td></tr>
    <tr><td>Categorías</td><td class="r">${d.categories.total}</td><td>${d.categories.topLevel} de primer nivel</td></tr>
    <tr><td>Cupones (histórico)</td><td class="r">${d.coupons.total} · ${d.coupons.used} usos</td><td>${d.coupons.total < 6 ? 'Promociones sin explotar' : 'OK'}</td></tr>
  </table>
</div>

<div class="page section-open">
  <div class="kicker"><span class="num">05</span><span class="label">Letra chica</span></div>
  <h2 class="report">Supuestos y tecnicismos.</h2>
  <p class="lede">Para que cada número sea defendible: origen del dato y qué se asumió.</p>
  <h3>Origen de los datos</h3>
  <ul class="check">
    <li>Todo sale de la <b>API oficial de Tienda Nube</b> (store ID ${d.store.id}), consultada el ${d.generatedAt.slice(0,10)}.</li>
    <li><b>Facturación</b> = suma de <code>total</code> con <code>payment_status = paid</code> (${fmt(d.lifetime.orders)} pedidos = ${M(d.lifetime.rev)}).</li>
    <li><b>Run-rate ~${M(d.runRate)}</b> = facturación de los últimos 12 meses.</li>
    <li><b>Carritos abandonados</b> = checkouts sin <code>completed_at</code>: ${ab.n} en ~${ab.windowDays} días, anualizado.</li>
  </ul>
  <h3>Supuesto y riesgo de cada palanca</h3>
  <table><tr><th>Palanca</th><th>Supuesto clave</th><th>Riesgo</th></tr>${riskRows}</table>
  <p class="note">Números <b>conservadores y aditivos</b>: no todas se capturan al 100% ni de inmediato. Las de riesgo alto (precio) se prueban con un test, no a ciegas.</p>
  <div class="footer-note">${B.name} · Informe sobre datos reales (store ID ${d.store.id}), API oficial de Tienda Nube, ${d.generatedAt.slice(0,10)}. Montos de oportunidad = estimaciones con supuestos explícitos, no ingresos garantizados.</div>
</div>

</body></html>`
fs.writeFileSync('report.html', html)
console.log('✓ report.html written — render with render.sh')
