#!/usr/bin/env bash
# Render report.html -> report.pdf via headless Chrome/Edge. Usage: ./render.sh [in.html] [out.pdf]
set -euo pipefail
IN="${1:-report.html}"; OUT="${2:-report.pdf}"
CHROME=""
for c in \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium" \
  "$(command -v google-chrome || true)" \
  "$(command -v chromium || true)" \
  "$(command -v chromium-browser || true)"; do
  [ -n "$c" ] && [ -x "$c" ] && CHROME="$c" && break
done
[ -z "$CHROME" ] && { echo "No Chrome/Edge/Chromium found. Install one or print report.html manually." >&2; exit 1; }
ABS="$(cd "$(dirname "$IN")" && pwd)/$(basename "$IN")"
"$CHROME" --headless --disable-gpu --no-sandbox --no-pdf-header-footer \
  --print-to-pdf="$OUT" --virtual-time-budget=10000 "file://$ABS" 2>/dev/null | grep -i "bytes written" || true
echo "✓ $OUT"
