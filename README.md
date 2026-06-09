# tiendanube-skills

Integrated Claude Code **skill family** for Tienda Nube / Nuvemshop stores. Layered so every analysis skill reads one stable dataset instead of re-pulling and re-deriving the API.

```
┌─ FOUNDATION ─────────────────────────────────────────────┐
│ tiendanube-stores       auth/OAuth, theme dev, MCP, API   │
├─ DATA LAYER ─────────────────────────────────────────────┤
│ tiendanube-store-data   TN API → canonical FACTS          │
│                         store-data.json (+ .xlsx)         │
├─ ANALYSIS LAYER (each consumes the data layer) ──────────┤
│ tiendanube-store-audit      facts → branded audit PDF     │
│ tiendanube-store-finance    facts → forecast .xlsx + PDF  │
│ …-marketing / -inventory / -customers   (future plug-ins) │
└───────────────────────────────────────────────────────────┘
```

## Layout

| Path | What |
|---|---|
| `skills/tiendanube-stores/` | Platform model, OAuth token exchange, theme dev, MCP install. Foundation. |
| `skills/tiendanube-store-audit/` | Operative/financial audit → branded PDF with money-quantified levers. |
| `skills/tiendanube-store-data/` | *(planned)* Canonical extraction layer: TN API → versioned `store-data.json` + `.xlsx`. |
| `skills/tiendanube-store-finance/` | *(planned)* Retail financial-analyst report from a physical-store **accounting workbook** (consistent `.xlsx` template) + optional Tienda Nube online data. Modes: xlsx-only / tn-only / merged. Vendors borghei/financial-analyst (forecast + variance + ratios + DCF) via openpyxl. → `.xlsx` + branded PDF. |
| `docs/specs/` | Design specs (brainstorming output). |

## Conventions (keep the family integrated)

1. **Versioned data contract** — `tiendanube-store-data` emits `store-data.json` with a `schemaVersion`. Consumers code against the schema in its `reference/`, not against the script.
2. **Facts vs opinion** — the data layer holds only normalized facts (revenue series, AOV, gateway mix, catalog stats, cohorts). Levers/forecasts/recommendations live in the consuming analysis skill.
3. **One report contract** — shared `report.config.json` brand schema across report skills → consistent branded output.
4. **One render pipeline** — `render.sh` (HTML → headless Chrome PDF) is shared infra.
5. **One xlsx writer** — Node/SheetJS, owned by the data layer; analysis skills reuse it for extra tabs.
6. **Python isolated to finance** — vendored financial-analyst stays inside `tiendanube-store-finance/scripts/`; cross-stage handoff is JSON files. Rest of the family is pure Node.

## Local development

Skills are symlinked into `~/.claude/skills/` from this repo, so edits here are live in Claude Code. To wire a fresh checkout:

```bash
for s in skills/*/; do
  name=$(basename "$s")
  ln -sfn "$PWD/$s" "$HOME/.claude/skills/$name"
done
```

Distribution-ready as a Claude Code plugin via `.claude-plugin/plugin.json`.
