#!/usr/bin/env node
// Self-contained Tienda Nube / Nuvemshop store analyzer.
// Reads ./.env (TIENDANUBE_ACCESS_TOKEN, TIENDANUBE_STORE_ID, optional API_BASE, CONTACT_EMAIL).
// Pulls store/orders/products/customers/checkouts/coupons/categories via the Admin REST API,
// computes operative + financial metrics + quantified opportunity levers, writes ./analysis.json.
// Levers are FORMULA-BASED (defensible), tunable via ./report.config.json -> {assumptions:{...}}.
import fs from 'fs'

// ---- env ----
for (const line of fs.existsSync('.env') ? fs.readFileSync('.env','utf8').split('\n') : []) {
  if (/^\s*#/.test(line)) continue
  const m = line.match(/^\s*([A-Z_]+)\s*=\s*(.*?)\s*$/); if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, '')
}
const TOKEN = process.env.TIENDANUBE_ACCESS_TOKEN, STORE = process.env.TIENDANUBE_STORE_ID
const BASE = (process.env.API_BASE || 'https://api.tiendanube.com/v1').replace(/\/$/,'')
const UA = `store-audit (${process.env.CONTACT_EMAIL || 'audit@example.com'})`
if (!TOKEN || !STORE) { console.error('Missing TIENDANUBE_ACCESS_TOKEN / TIENDANUBE_STORE_ID in .env'); process.exit(1) }

// ---- tiny API client w/ pagination + 429 retry ----
async function api(path, params = {}) {
  const qs = new URLSearchParams(params).toString()
  const url = `${BASE}/${STORE}${path}${qs ? '?' + qs : ''}`
  for (let i = 0; i < 6; i++) {
    const r = await fetch(url, { headers: { Authentication: `bearer ${TOKEN}`, 'User-Agent': UA, 'Content-Type': 'application/json' } })
    if (r.status === 429) { await new Promise(s => setTimeout(s, 2000)); continue }
    if (!r.ok) throw new Error(`${r.status} ${path}: ${(await r.text()).slice(0,200)}`)
    return { data: await r.json(), link: r.headers.get('link') || '' }
  }
  throw new Error(`429 retries exhausted ${path}`)
}
async function listAll(path, params = {}, cap = 60) {
  let out = []
  for (let page = 1; page <= cap; page++) {
    let res
    try { res = await api(path, { ...params, per_page: '200', page: String(page) }) }
    catch (e) { if (page === 1) throw e; break }
    out = out.concat(res.data || [])
    if (!res.link || !res.link.includes('rel="next"') || (res.data || []).length < 200) return out
    if (page === cap) console.error(`⚠ ${path}: reached ${cap*200}-record cap, results may be partial`)
  }
  return out
}

// ---- helpers ----
const N = x => Number(x) || 0
const S = v => v == null ? '' : (typeof v === 'string' ? v : (v.date || ''))
const T = o => o && typeof o === 'object' ? (o.es ?? Object.values(o)[0] ?? '') : (o ?? '')
const ym = d => S(d).slice(0, 7)

// ---- config / assumptions ----
const cfg = fs.existsSync('report.config.json') ? JSON.parse(fs.readFileSync('report.config.json','utf8')) : {}
const A = Object.assign({
  abandonRecoveryRate: 0.08,   // 3-mail flow recovers 5-15%
  aovUpliftPct: 0.10,          // cross-sell + free-ship threshold
  repeatUpliftPp: 0.08,        // +8pp of buyers become repeat
  seoUpliftPct: 0.05,          // organic channel from zero
  deadStockRecoveryRate: 0.40, // share of dead listings restockable
  transferDiscountPct: 0.20,   // current payment-method discount
  transferDiscountNewPct: 0.15,// proposed
  transferGatewayKeys: ['offline'], // gateways treated as the discounted/transfer channel
  pendingRecoveryRate: 0.10,
}, cfg.assumptions || {})

console.error('Fetching store…')
const store = (await api('/store')).data
console.error('Fetching orders…')
let orders
try { orders = await listAll('/orders', { fields: 'id,status,payment_status,shipping_status,gateway,total,created_at,completed_at,products,customer' }) }
catch (e) { if (String(e).includes('403')) { console.error('✗ 403 on /orders — token lacks read_orders. Re-authorize with full read scopes (see tiendanube-stores).'); process.exit(1) } throw e }
const paid = orders.filter(o => o.payment_status === 'paid')

// monthly (15) + yearly
const mR = {}, mO = {}, yR = {}, yO = {}
for (const o of paid) {
  const k = ym(o.completed_at) || ym(o.created_at); if (!k) continue
  mR[k] = (mR[k] || 0) + N(o.total); mO[k] = (mO[k] || 0) + 1
  const y = k.slice(0, 4); yR[y] = (yR[y] || 0) + N(o.total); yO[y] = (yO[y] || 0) + 1
}
const monthsAll = Object.keys(mR).sort()
const monthly = monthsAll.slice(-15).map(k => ({ m: k, rev: Math.round(mR[k]), ord: mO[k], aov: Math.round(mR[k] / mO[k]) }))
const yearly = Object.keys(yR).sort().map(y => ({ y, rev: Math.round(yR[y]), ord: yO[y] }))
// run-rate = trailing 12 months (annualized if fewer)
const last12 = monthsAll.slice(-12)
const ttm = last12.reduce((s, k) => s + mR[k], 0)
const runRate = Math.round(last12.length ? ttm * 12 / last12.length : 0)

// gateway
const gR = {}, gO = {}
for (const o of paid) { let g = (o.gateway || '(none)').replace('mercadopago','mercado-pago'); gR[g] = (gR[g] || 0) + N(o.total); gO[g] = (gO[g] || 0) + 1 }
const gTot = Object.values(gR).reduce((a, b) => a + b, 0) || 1
const gateway = Object.entries(gR).sort((a, b) => b[1] - a[1]).map(([g, v]) => ({ g, rev: Math.round(v), ord: gO[g], pct: Math.round(v / gTot * 100) }))

// leaks
console.error('Fetching checkouts (abandoned)…')
let checkouts = []
try { checkouts = await listAll('/checkouts', { fields: 'id,total,completed_at,created_at,contact_email' }) } catch {}
const aband = checkouts.filter(c => !c.completed_at)
const abVal = Math.round(aband.reduce((s, c) => s + N(c.total), 0))
const cd = aband.map(c => S(c.created_at)).filter(Boolean).sort()
const windowDays = cd.length ? Math.max(1, Math.round((new Date(cd[cd.length-1]) - new Date(cd[0])) / 864e5)) : 30
const abandYr = Math.round(abVal * 365 / windowDays)
const pend = orders.filter(o => o.payment_status === 'pending')
const canc = orders.filter(o => o.status === 'cancelled')
const leaks = {
  abandoned: { n: aband.length, val: abVal, withEmail: aband.filter(c => c.contact_email).length, windowDays, annualized: abandYr },
  pending: { n: pend.length, val: Math.round(pend.reduce((s, o) => s + N(o.total), 0)) },
  cancelled: { n: canc.length, val: Math.round(canc.reduce((s, o) => s + N(o.total), 0)) },
}

// customers
console.error('Fetching customers…')
const customers = await listAll('/customers', { fields: 'id,total_spent' })
const buyerCount = {}
for (const o of paid) { const c = o.customer && (o.customer.id || o.customer); if (c) buyerCount[c] = (buyerCount[c] || 0) + 1 }
const buyers = Object.keys(buyerCount).length
const repeat = Object.values(buyerCount).filter(n => n > 1).length
const cust = { total: customers.length, buyers, repeat, repeatPct: buyers ? Math.round(repeat / buyers * 100) : 0, oneTime: buyers - repeat }

// products (operative + catalog quality)
console.error('Fetching products…')
const prods = await listAll('/products', { fields: 'id,name,published,variants,images,seo_title,seo_description,description,attributes,categories' })
let published = 0, deadPub = 0, nullp = 0, single = 0, noImg = 0, noSeoT = 0, noSeoD = 0, promo = 0, talle = 0, weightDims = 0, invVal = 0
for (const p of prods) {
  const vs = p.variants || []
  if (p.published) published++
  if (vs.every(v => (v.stock ?? 0) <= 0) && p.published) deadPub++
  if (vs.some(v => v.price == null || N(v.price) === 0)) nullp++
  const imgs = (p.images || []).length
  if (imgs === 0) noImg++; else if (imgs === 1) single++
  if (!T(p.seo_title)) noSeoT++
  if (!T(p.seo_description)) noSeoD++
  if (vs.some(v => v.promotional_price && N(v.promotional_price) > 0)) promo++
  if ((p.attributes || []).some(a => /talle|size|talla/i.test(T(a)))) talle++
  const v0 = vs[0] || {}
  if (N(v0.weight) > 0 && N(v0.depth) > 0 && N(v0.width) > 0 && N(v0.height) > 0) weightDims++
  for (const v of vs) { const st = N(v.stock); if (st > 0) invVal += st * N(v.price) }
}
const products = { total: prods.length, published, deadPub, nullp, single, noImg, noSeoTitle: noSeoT, noSeoDescription: noSeoD, promo, talleAttr: talle, weightDims, invValue: Math.round(invVal) }

// categories
const cats = await listAll('/categories', { fields: 'id,name,parent' })
const categories = { total: cats.length, topLevel: cats.filter(c => c.parent === 0 || c.parent == null).length,
  tree: cats.filter(c => c.parent === 0 || c.parent == null).map(c => ({ name: T(c.name), children: cats.filter(x => x.parent === c.id).length })) }

// coupons
let coupons = { total: 0, used: 0 }
try { const cp = await listAll('/coupons'); coupons = { total: cp.length, used: cp.reduce((s, c) => s + N(c.used), 0) } } catch {}

// top sellers by revenue
const rev = {}, un = {}
for (const o of paid) for (const p of (o.products || [])) { const n = T(p.name) || p.product_id; rev[n] = (rev[n] || 0) + N(p.price) * N(p.quantity); un[n] = (un[n] || 0) + N(p.quantity) }
const topRev = Object.entries(rev).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([n, v]) => ({ n, rev: Math.round(v), u: un[n] }))

const lifetime = { rev: Math.round(paid.reduce((s, o) => s + N(o.total), 0)), orders: paid.length, aov: paid.length ? Math.round(paid.reduce((s, o) => s + N(o.total), 0) / paid.length) : 0 }

// ---- opportunity levers (formula-based) ----
const offRev = gateway.filter(g => A.transferGatewayKeys.includes(g.g)).reduce((s, g) => s + g.rev, 0)
const offShare = gTot ? offRev / gTot : 0
const transferGivenYr = runRate * offShare / (1 - A.transferDiscountPct) * A.transferDiscountPct
const avgRevPerProdYr = published ? runRate / published : 0
const levers = [
  { key: 'abandoned', name: 'Recuperación de carrito abandonado', val: Math.round(abandYr * A.abandonRecoveryRate), eff: 'Bajo', risk: 'bajo', assume: `Recuperar ${Math.round(A.abandonRecoveryRate*100)}% de lo que se abandona (flujo de 3 mails recupera 5–15%)` },
  { key: 'aov', name: `AOV +${Math.round(A.aovUpliftPct*100)}% con cross-sell y envío gratis por monto`, val: Math.round(runRate * A.aovUpliftPct), eff: 'Medio', risk: 'medio', assume: `El ticket sube ${Math.round(A.aovUpliftPct*100)}% sobre el run-rate` },
  { key: 'repeat', name: `Recompra de ${cust.repeatPct}% → ${cust.repeatPct + Math.round(A.repeatUpliftPp*100)}%`, val: Math.round(buyers * A.repeatUpliftPp * lifetime.aov), eff: 'Medio', risk: 'medio', assume: `+${Math.round(A.repeatUpliftPp*100)} pp de clientes vuelven con flujo post-compra` },
  { key: 'seo', name: 'SEO — canal orgánico hoy sin explotar', val: Math.round(runRate * A.seoUpliftPct), eff: 'Medio', risk: 'medio', assume: `+${Math.round(A.seoUpliftPct*100)}% de sesiones convirtiendo al ritmo actual` },
  { key: 'deadstock', name: `Reponer la vidriera muerta (${deadPub} productos)`, val: Math.round(deadPub * avgRevPerProdYr * A.deadStockRecoveryRate), eff: 'Bajo', risk: 'bajo', assume: `${Math.round(A.deadStockRecoveryRate*100)}% de los ${deadPub} sin stock se reponen y venden` },
  { key: 'transfer', name: 'Optimizar el descuento por transferencia', val: Math.round(transferGivenYr * ((A.transferDiscountPct - A.transferDiscountNewPct) / A.transferDiscountPct)), eff: 'Bajo', risk: 'alto', assume: `Bajar ${Math.round(A.transferDiscountPct*100)}%→${Math.round(A.transferDiscountNewPct*100)}% sin perder volumen` },
  { key: 'pending', name: 'Recuperar pedidos sin pagar', val: Math.round(leaks.pending.val * A.pendingRecoveryRate), eff: 'Bajo', risk: 'bajo', assume: `Recuperar ${Math.round(A.pendingRecoveryRate*100)}% de los pendientes con recordatorio + link de pago` },
].filter(l => l.val > 0).sort((a, b) => b.val - a.val)
const totalUpside = levers.reduce((s, l) => s + l.val, 0)

const out = {
  generatedAt: new Date().toISOString(),
  store: { id: store.id, name: T(store.name), domain: (store.url_with_protocol || (store.domains || [])[0] || ''), theme: store.current_theme, plan: store.plan_name, currency: store.main_currency, logo: store.logo, description: T(store.description), whatsapp: store.whatsapp_phone_number, instagram: store.instagram },
  lifetime, runRate, yearly, monthly, gateway, leaks, customers: cust, products, categories, coupons, topRev,
  assumptions: A, levers, totalUpside,
}
fs.writeFileSync('analysis.json', JSON.stringify(out, null, 1))
console.error(`\n✓ analysis.json written`)
console.log(JSON.stringify({ store: out.store.name, products: products.total, paidOrders: lifetime.orders, lifetimeRev: lifetime.rev, runRate, totalUpside, levers: levers.map(l => ({ [l.key]: l.val })) }, null, 1))
