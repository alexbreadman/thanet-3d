#!/usr/bin/env bash
#
# add-splat.sh — the whole splat pipeline in one command.
#
#   Usage:    pipeline/add-splat.sh <site-id> <trained-splat.ply>
#   Example:  pipeline/add-splat.sh margate-harbour-arm ~/Downloads/export.ply
#
# Takes the .ply that LichtFeld Studio saved and produces, in assets/splats/:
#   <site-id>.ply           the archival master (kept as-is)
#   <site-id>.spz           the compressed web file (~10x smaller)
#   <site-id>.preview.html  double-click to view the splat in your browser
#   <site-id>.meta.json     the sidecar — FILL IN lat/lon before it ships
#
# Needs: node/npx (uses @playcanvas/splat-transform, fetched automatically).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/assets/splats"

if [[ $# -ne 2 ]]; then
  grep '^#' "$0" | sed 's/^# \{0,1\}//' | head -14
  exit 1
fi

ID="$1"
SRC="$2"

if [[ ! "$ID" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  echo "site-id must be lowercase-kebab-case, e.g. margate-harbour-arm" >&2
  exit 1
fi
if [[ ! -f "$SRC" ]]; then
  echo "no such file: $SRC" >&2
  exit 1
fi
command -v npx >/dev/null || { echo "node/npx is required (https://nodejs.org)" >&2; exit 1; }

echo "→ archiving master ply"
cp "$SRC" "$OUT/$ID.ply"

echo "→ compressing to .spz (this is the file the web loads)"
npx --yes @playcanvas/splat-transform "$OUT/$ID.ply" "$OUT/$ID.spz"

echo "→ writing browser preview"
npx --yes @playcanvas/splat-transform "$OUT/$ID.ply" "$OUT/$ID.preview.html"

META="$OUT/$ID.meta.json"
if [[ -f "$META" ]]; then
  echo "→ sidecar already exists, leaving it alone: $META"
else
  echo "→ writing sidecar (remember: lat/lon before it ships)"
  cat > "$META" <<EOF
{
  "id": "$ID",
  "name": "TODO human-readable name",
  "kind": "place",
  "captured": "$(date +%F)",
  "capture_method": "phone-video",
  "location": { "lat": null, "lon": null, "crs": "EPSG:4326" },
  "heading_deg": 0,
  "units": "metres",
  "outputs": { "splat": "splats/$ID.spz" },
  "license": "CC-BY-4.0",
  "source": "own capture",
  "twin_id": null
}
EOF
fi

echo
echo "done."
ls -lh "$OUT/$ID".* | awk '{print "  " $9 "  (" $5 ")"}'
echo
echo "next:"
echo "  1. open $OUT/$ID.preview.html to eyeball it"
echo "  2. put real lat/lon + name in $META  (right-click the spot on Google Maps to copy coords)"
echo "  3. commit — .ply and .spz go via LFS automatically"
