#!/usr/bin/env bash
# Build manuscript from Pandoc Markdown to DOCX and/or PDF.
#
# Usage:
#   ./manuscript/build.sh          # default: DOCX
#   ./manuscript/build.sh pdf      # PDF only
#   ./manuscript/build.sh both     # DOCX + PDF
#   ./manuscript/build.sh docx     # DOCX only
#
# Requirements: pandoc >= 2.19, pandoc-citeproc (bundled in recent pandoc)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${SCRIPT_DIR}/manuscript.md"
BIB="${SCRIPT_DIR}/bibliography/cibb2026_references.bib"
OUTDIR="${SCRIPT_DIR}"

FORMAT="${1:-docx}"

PANDOC_COMMON=(
    --from markdown+citations
    --citeproc
    --bibliography "${BIB}"
    --csl "${SCRIPT_DIR}/csl/ieee.csl"
    --number-sections
    --standalone
    --resource-path "${SCRIPT_DIR}:${SCRIPT_DIR}/.."
)

build_docx() {
    echo "Building DOCX..."
    pandoc "${PANDOC_COMMON[@]}" \
        --to docx \
        --reference-doc "${SCRIPT_DIR}/CIBB_2026_Microsoft_Word_Template_anomymous.docx" \
        --output "${OUTDIR}/manuscript.docx" \
        "${SRC}"
    echo "  -> ${OUTDIR}/manuscript.docx"
}

build_pdf() {
    echo "Building PDF..."
    pandoc "${PANDOC_COMMON[@]}" \
        --to pdf \
        --pdf-engine=xelatex \
        -V geometry:margin=2.5cm \
        -V fontsize=11pt \
        -V linestretch=1.15 \
        --output "${OUTDIR}/manuscript.pdf" \
        "${SRC}"
    echo "  -> ${OUTDIR}/manuscript.pdf"
}

case "${FORMAT}" in
    docx)  build_docx ;;
    pdf)   build_pdf ;;
    both)  build_docx; build_pdf ;;
    *)     echo "Usage: $0 [docx|pdf|both]"; exit 1 ;;
esac

echo "Done."
