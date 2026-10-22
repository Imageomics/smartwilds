#!/bin/bash
# Render the staged Hugging Face dataset cards (README.md) to PDF for review.
#
#   release/scripts/cards_to_pdf.sh            # all repos -> release/cards_pdf/
#
# Renders from the built repos in release/hf_smartwilds_20261022/ so image
# paths resolve. HTML <img> tags become pandoc images; <!-- TODO --> comments
# become visible "[TODO: ...]" notes; the YAML front matter (HF metadata) is
# shown as an appendix block.
set -euo pipefail
ROOT=/fs/ess/PAS2136/TheWilds2025/release
STAGE=$ROOT/hf_smartwilds_20261022
OUT=$ROOT/cards_pdf
mkdir -p "$OUT"
source /etc/profile.d/lmod.sh
module load pandoc/3.6.4 texlive/2025 >/dev/null 2>&1

for d in "$STAGE"/smartwilds*/; do
  repo=$(basename "$d")
  tmp=$(mktemp "$d/.card_XXXX.md")
  python3 -I - "$d/README.md" "$tmp" "$repo" <<'EOF'
import re, sys
src, dst, repo = sys.argv[1:4]
s = open(src).read()
front = ""
if s.startswith("---\n"):
    end = s.index("\n---", 4)
    front, s = s[4:end], s[end + 4:].lstrip("\n")
# <img src="x" alt="y" width="N"> -> ![y](x){width=..}
def img(m):
    a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(0)))
    w = int(a.get("width", "400"))
    return f'![{a.get("alt", "")}]({a["src"]}){{width={min(w / 7, 95):.0f}%}}'
s = re.sub(r"<img [^>]*>", img, s)
# make TODO comments visible for review
s = re.sub(r"<!--\s*(TODO[^>]*?)\s*-->", lambda m: f"**[{m.group(1).strip()}]**", s)
s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
title = f"{repo} — dataset card (review draft)"
head = ("---\n"
        f"title: \"{title}\"\n"
        "date: \"Rendered from release/hf_smartwilds_20261022/" + repo + "/README.md\"\n"
        "---\n\n")
appendix = ("\n\n# Appendix: Hugging Face metadata (YAML front matter)\n\n"
            "```yaml\n" + front.strip() + "\n```\n") if front else ""
open(dst, "w").write(head + s + appendix)
EOF
  ( cd "$d" && pandoc "$(basename "$tmp")" -o "$OUT/$repo.pdf" \
      --pdf-engine=lualatex -f markdown+pipe_tables+link_attributes-implicit_figures \
      -V geometry:margin=0.8in -V fontsize=10pt \
      -V mainfont="DejaVu Serif" -V sansfont="DejaVu Sans" -V monofont="DejaVu Sans Mono" \
      -V monofontoptions="Scale=0.85" -V colorlinks=true -V linkcolor=blue -V urlcolor=blue \
      --highlight-style=tango 2> "$OUT/$repo.log" ) \
    && echo "ok   $repo -> $OUT/$repo.pdf" || { echo "FAIL $repo (see $OUT/$repo.log)"; tail -5 "$OUT/$repo.log"; }
  rm -f "$tmp"
done
