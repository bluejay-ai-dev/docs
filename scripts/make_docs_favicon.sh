#!/usr/bin/env bash
# regenerate the docs chrome-tab favicon from the website's bluejay bird symbol,
# filled with a purple -> pink -> blue brand gradient. no tile/background — matches
# the production app mark (app.getbluejay.ai/favicon-dark.svg), just gradient-filled.
# the website favicon svg is the single source of truth.
set -euo pipefail

# gradient stops along the diagonal: pink edge -> purple middle -> blue edge,
# then darkened slightly so the mark reads more prominently on a light tab.
C1="#FFBEFF"   # start edge (pink)
C2="#8A5EEB"   # middle     (purple)
C3="#6FD0FB"   # end edge   (blue)
KEEP_PCT="100"  # keep this % of each channel (88 = 12% darker; 100 = unchanged)
GID="bjGrad"

darken() { # #RRGGBB -> scaled to KEEP_PCT brightness (bash integer math, no awk/float)
  local h="${1#\#}"
  printf '#%02X%02X%02X' \
    "$(( 16#${h:0:2} * KEEP_PCT / 100 ))" \
    "$(( 16#${h:2:2} * KEEP_PCT / 100 ))" \
    "$(( 16#${h:4:2} * KEEP_PCT / 100 ))"
}
C1="$(darken "$C1")"; C2="$(darken "$C2")"; C3="$(darken "$C3")"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docs_dir="$(dirname "$script_dir")"
repo_dir="$(dirname "$docs_dir")"

src="$repo_dir/bluejay_frontend_v2/public/favicon-dark.svg"  # website bird symbol
svg_out="$docs_dir/favicon.svg"
png_out="$docs_dir/favicon.png"

# span the gradient across the mark's viewBox. userSpaceOnUse renders reliably in
# rsvg / mintlify / browsers; objectBoundingBox on a <g fill> does not (renders black).
read vbw vbh <<<"$(grep -oE 'viewBox="[^"]*"' "$src" | head -1 | awk -F'"' '{print $2}' | awk '{print $(NF-1), $NF}')"

defs="<defs><linearGradient id=\"$GID\" gradientUnits=\"userSpaceOnUse\" x1=\"0\" y1=\"0\" x2=\"$vbw\" y2=\"$vbh\"><stop offset=\"0\" stop-color=\"$C1\"/><stop offset=\".5\" stop-color=\"$C2\"/><stop offset=\"1\" stop-color=\"$C3\"/></linearGradient></defs>"

# point the mark's fill at the gradient, then inject the gradient def after <svg>.
# @-delimiter on the inject so the # in the hex stops isn't read as a delimiter.
sed -E "s/fill=\"#[0-9a-fA-F]{3,6}\"/fill=\"url(#$GID)\"/g" "$src" \
  | sed -E "s@<svg[^>]*>@&$defs@" \
  >"$svg_out"

# render a 512px transparent png from the svg. the gradient needs a real svg renderer
# (system rsvg/inkscape aren't installed, and imagemagick's msvg renders gradients
# black), so use the sibling app's sharp — already present, same repo as the source mark.
sharp_dir="$repo_dir/bluejay_frontend_v2/node_modules/sharp"
node -e "require('$sharp_dir')('$svg_out',{density:512}).resize(512,512,{fit:'contain',background:{r:0,g:0,b:0,alpha:0}}).png().toFile('$png_out').catch(e=>{console.error(String(e));process.exit(1)})" \
  || echo "warn: favicon.png not regenerated (sharp unavailable) — favicon.svg is the source mintlify builds from"

echo "docs favicon: $C1 -> $C2 -> $C3 gradient, no tile"
echo "  $svg_out"
echo "  $png_out"
