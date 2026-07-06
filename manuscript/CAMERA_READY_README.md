# CIBB 2026 — Camera-ready, LNBI full paper & talk

Build notes and rebuild instructions for the accepted CIBB 2026 short paper and its
downstream deliverables. All documents describe the GPU-vs-CPU single-cell & spatial
transcriptomics benchmark on the NVIDIA DGX H100.

## What changed

The accepted short paper needed only **de-anonymization + official-template formatting** —
the reviewers requested no scientific revisions. Concretely:

- Inserted the real **author block**: Luca Vedovelli¹˒²˒\*, Corrado Lanera¹˒², Daniele
  Sabbatini¹˒²˒³, Dario Gregori¹˒² (¹ Unit of Biostatistics, University of Padova; ²
  BIOSTAT-X, Pediatric Research Institute «Città della Speranza»; ³ Neuromuscular Unit,
  Dept. of Neuroscience, University of Padua). Emails `firstname.surname@ubep.unipd.it`.
- **Corresponding author defaulted to Luca Vedovelli** (first author). Change: edit the
  `*` superscript on the author line and the `*corresponding author:` email in
  `manuscript_short_cameraready.md`, then rebuild.
- Filled the previously-hidden sections in **black text**: Conflict of Interest,
  Acknowledgements (UPSCALE/CONVECS DGX H100), Funding (PNC "DARE" `PNC0000002`, CUP
  `B53C22006440001`; BIRD 2024/START `2024DCTV1SIDPROGETTI-00183`), Data & Software
  availability (GitHub URL).
- Scientific text, figures, tables, and numbers are **unchanged** from the accepted paper.
  Headline numbers re-verified against `results/*.json` (CPU 1.3M = 52,056.2 ± 392.0 s;
  GPU-8 = 435.2 ± 16.2 s; 119.6× speedup).

## Deliverables

### 1. Camera-ready short paper (CIBB 2026 template, 4–6 pp)
| File | Notes |
|------|-------|
| `CIBB_manuscript_short_cameraready.pdf` | **6 pages**, A4, 2.5 cm margins, single column, IEEE references. Built with typst (compact styling to meet the 4–6 pp limit). |
| `CIBB_manuscript_short_cameraready.docx` | Built from the **official** `CIBB_2026_Microsoft_Word_Template_anomymous.docx` as pandoc reference-doc. |
| `manuscript_short_cameraready.md` | De-anonymized Markdown source. |

### 2. LNBI full paper (Springer LNCS style, comprehensive ~22 pp)
Length was kept **comprehensive** (per author decision) for a journal Special Issue; a
strict 8–12 pp version would require dropping ~half the prose and several tables.
| File | Notes |
|------|-------|
| `full_paper_LNBI.pdf` | Readable LNCS-style render (typst), all 9 figures + 10 tables. |
| `full_paper_LNBI.docx` | Word version. |
| `full_paper_LNBI.md` | De-anonymized Markdown source. |
| `full_paper_LNBI_overleaf.zip` | **Genuine Springer LaTeX package** for Overleaf: `full_paper_LNBI.tex` + official `llncs.cls` (v2.26) + `splncs04.bst` + `cibb2026_references.bib` + `figures/`. Upload the zip to Overleaf and compile (pdfLaTeX → BibTeX → pdfLaTeX ×2). All 32 cite keys resolve against the 32-entry bib. |

### 3. Talk (~12 min, Quarto reveal.js)
| File | Notes |
|------|-------|
| `talk_CIBB2026.html` | **Self-contained** reveal.js deck (4.5 MB, all figures embedded). Open in any browser; press `s` for the speaker-notes view, `f` for fullscreen, `?` for shortcuts. 14 slides. |
| `talk_CIBB2026.qmd` | Quarto source (speaker notes in `::: notes` blocks). |
| `custom.scss` | Theme (Padova blue). |
| `speaker_notes_CIBB2026.pdf` / `.md` | Standalone spoken script, per-slide, with timing. ~1,607 words ≈ 10.7–12.4 min at 130–150 wpm. |

## How to rebuild

All builds use the conda env **`docbuild`** (pandoc 3.8.3, quarto 1.9.38, typst 0.14.2).
There is **no LaTeX engine** on this machine, so PDFs are produced with **typst**; the
LNBI `.tex` is provided for compilation on Overleaf.

```bash
conda activate docbuild
cd manuscript
export XDG_CACHE_HOME=/tmp/qcache HOME=/tmp

COMMON="--from markdown+citations --citeproc \
  --bibliography bibliography/cibb2026_references.bib \
  --csl csl/ieee.csl --resource-path .:..:../figures"

# --- Short paper: DOCX (official template) ---
pandoc manuscript_short_cameraready.md $COMMON \
  --reference-doc CIBB_2026_Microsoft_Word_Template_anomymous.docx \
  -o CIBB_manuscript_short_cameraready.docx

# --- Short paper: PDF (typst, 6 pp) ---
# strip the lone-backslash spacer lines, add compact typst styling,
# compress the reference block, then compile with --root at the repo top.
# (see build steps in this repo's history; the compact header sets
#  par leading ~0.5em, image width ~50%, table text 9.5pt, refs 9pt.)

# --- LNBI full paper: PDF (typst) + DOCX ---
pandoc full_paper_LNBI.md $COMMON --number-sections -o full_paper_LNBI.docx
#   PDF: pandoc full_paper_LNBI.md ... --to typst (compact header) then
#        typst compile --root <repo-top> _full.typ full_paper_LNBI.pdf

# --- LNBI LaTeX (Overleaf): use full_paper_LNBI_overleaf.zip ---

# --- Talk: reveal.js HTML ---
source quarto_env.sh          # arm64 tool-path overrides for conda-forge quarto
export HOME=/tmp
quarto render talk_CIBB2026.qmd --to revealjs -M embed-resources:true

# --- Speaker notes PDF ---
pandoc speaker_notes_CIBB2026.md --to pdf --pdf-engine=typst \
  -V papersize=a4 -V fontsize=11pt -o speaker_notes_CIBB2026.pdf
```

### Toolchain note (arm64 quarto)
The conda-forge quarto build mis-detects its bundled tool paths on this arm64 Mac.
`quarto_env.sh` (in this folder) exports the `QUARTO_DENO / QUARTO_DART_SASS /
QUARTO_ESBUILD / QUARTO_TYPST / QUARTO_PANDOC / QUARTO_SHARE_PATH / QUARTO_DENO_DOM`
overrides and writable cache dirs. Source it (and set `HOME=/tmp` on macOS, so quarto
does not try to write `~/Library/Caches/quarto`) before any `quarto render`.
