#!/bin/bash
# Build smartwilds_sys_dataset.pdf with the ACM acmart class.
#
#   ./build.sh            review build: \TODO notes visible (default)
#   ./build.sh --submit   submission build: \TODO notes suppressed
#
# acmart.cls is NOT in the system TeX Live 2020 on OSC; it IS in the
# texlive/2025 module, which this script loads.

set -u
cd "$(dirname "$0")"

source /etc/profile.d/lmod.sh 2>/dev/null || true
module load texlive/2025 || { echo "ERROR: could not load texlive/2025"; exit 1; }

MODE="review"
[ "${1:-}" = "--submit" ] && MODE="submit"

BUILD="build_${MODE}"
mkdir -p "$BUILD"
cp references.bib "$BUILD"/
# figures (source filenames may contain spaces; copy to safe names)
mkdir -p "$BUILD/figures" && cp figures/*.pdf "$BUILD/figures/" 2>/dev/null || \
  echo "WARNING: deployment map figure not found"

if [ "$MODE" = "submit" ]; then
  # Suppress the review notes so the page count reflects the real submission.
  # flip the review-mode switch: hides \TODO notes and the table of contents
  sed 's|^\\reviewmodetrue$|\\reviewmodefalse|' \
    smartwilds_sys_dataset.tex > "$BUILD/smartwilds_sys_dataset.tex"
else
  cp smartwilds_sys_dataset.tex "$BUILD"/
fi

cd "$BUILD"
pdflatex -interaction=nonstopmode smartwilds_sys_dataset.tex > pass1.log 2>&1
bibtex   smartwilds_sys_dataset                              > bibtex.log 2>&1
pdflatex -interaction=nonstopmode smartwilds_sys_dataset.tex > pass2.log 2>&1
pdflatex -interaction=nonstopmode smartwilds_sys_dataset.tex > pass3.log 2>&1

LOG=smartwilds_sys_dataset.log
fail=0

echo "=== fatal errors ==="
if grep -h '^! ' pass*.log | sort -u | grep . ; then fail=1; else echo "none"; fi

echo "=== undefined citations ==="
# natbib writes "Citation `key' on page N undefined", so allow text before "undefined".
if { grep -oE "Citation \`[^']*'[^.]*undefined" "$LOG";
     grep -o "didn't find a database entry for \"[^\"]*\"" bibtex.log; } \
   | sort -u | grep . ; then fail=1; else echo "none"; fi

echo "=== undefined references ==="
if grep -oE "Reference \`[^']*' on page [0-9]+ undefined" "$LOG" | sort -u | grep . ; then fail=1; else echo "none"; fi

echo "=== overfull hboxes > 15pt ==="
n=$(grep -oE 'Overfull \\hbox \([0-9]+\.[0-9]+pt too wide\)' "$LOG" \
      | grep -oE '\([0-9]+' | tr -d '(' | awk '$1>15' | wc -l)
echo "$n"

if [ -f smartwilds_sys_dataset.pdf ]; then
  cp smartwilds_sys_dataset.pdf "../smartwilds_sys_dataset_${MODE}.pdf"
  echo "=== page count ==="
  pdfinfo smartwilds_sys_dataset.pdf | grep -i '^Pages'
  pdftotext smartwilds_sys_dataset.pdf out.txt 2>/dev/null
  python3 - <<'PY'
pages = open('out.txt').read().split('\f')
pages = [p for p in pages if p.strip()]
ref = next((i for i, p in enumerate(pages, 1) if '[1] ' in p), None)
print('total pages      :', len(pages))
print('references begin : page %s' % (ref if ref else '?'))
if ref:
    # references may start partway down a page that still carries body text
    head = ' '.join(pages[ref - 1].split())
    cut = head.find('[1] ')
    shared = any(k in head[:cut] for k in
                 ('Conclusion', 'ACKNOWLEDGMENTS', 'Acknowledgments',
                  'Artifact and Supplemental', 'REFERENCES'))
    body = ref if shared else ref - 1
    note = ' (body text shares page %d with the start of references)' % ref if shared else ''
    print('body pages       : %d%s' % (body, note))
    print('LIMIT            : %s (ICDE 2027: 12 pages excl. references + AI-content acknowledgement; no appendix)'
          % ('OK' if body <= 12 else 'OVER by %d' % (body - 12)))
else:
    print('body pages       : ?')
PY
  echo
  echo "wrote ../smartwilds_sys_dataset_${MODE}.pdf"
else
  echo "NO PDF PRODUCED -- tail of pass1.log:"
  tail -40 pass1.log
  fail=1
fi

exit $fail
