# Prompt per generare il diagramma della pipeline (Figure 7)

Usa questo prompt con un LLM che genera immagini (DALL-E, Midjourney) oppure con un LLM che genera codice TikZ/Mermaid/draw.io.

---

## Prompt per generazione codice (raccomandato: TikZ o SVG via Claude/GPT)

Create a publication-ready pipeline flow diagram for a scientific paper comparing CPU vs GPU single-cell RNA-seq analysis. The diagram should be clean, minimal, and use a professional colour scheme suitable for print.

### Layout

A horizontal flow diagram (left to right) with 10 numbered pipeline steps. Each step is a rounded rectangle. Steps are connected by arrows. The diagram has THREE horizontal swim lanes (rows), colour-coded:

1. **CPU-only lane** (top, light blue background, #D6EAF8): steps that always run on CPU
2. **Multi-GPU lane** (middle, light red/pink background, #FADBD8): steps distributed across 2-8 GPUs via Dask-CUDA
3. **Single-GPU lane** (bottom, light green background, #D5F5E3): steps that run on GPU device 0 only

### Steps and their lane assignments

**CPU lane (light blue):**
- Step 1: "Data loading" (h5ad file icon)
- Step 2: "QC & filtering" (min_genes=200, min_cells=3)
- Step 3: "Normalisation" (target_sum=10^4, log1p)
- Step 4: "HVG selection" (n=2,000)

**Transition arrow from CPU to GPU** (dashed, labelled "anndata_to_GPU()" or "GPU transfer")

**CPU lane again (for multi-GPU pipeline only):**
- Step 5: "Scaling" (dense, max_value=10) — note: for single-GPU this runs on GPU, for multi-GPU it runs on CPU

**Multi-GPU lane (light pink):**
- Step 6: "PCA" (50 components, SVD) — label "Dask distributed"
- Step 7: "Neighbour graph" (k=15, 50 PCs) — label "Dask distributed"

**Single-GPU lane (light green):**
- Step 8: "Leiden clustering" (r=0.5, 1.0, 1.5) — label "cuGraph"
- Step 9: "UMAP" (2D embedding) — label "cuML"
- Step 10: "DE testing" (Wilcoxon, one-vs-rest) — label "GPU or CPU"

### Visual annotations

- Above the diagram: a timeline bar showing approximate % of total wall time at 1.3M cells:
  - CPU preprocessing (steps 1-4): 75%
  - Multi-GPU (steps 6-7): 4%
  - Single-GPU (steps 8-10): 21%
- Below step 5, a small annotation: "Dense matrix: n_cells x 2,000 x 4B"
- Below step 6, annotation: "Distributed across N GPUs"
- Right side: output annotation showing "Cluster labels, UMAP coords, DE genes"

### Style requirements

- Font: sans-serif (Helvetica or similar), 8-9pt
- Colours: muted, colour-blind friendly (blue/red/green at low saturation)
- No gradients, no shadows, no 3D effects
- White background
- Figure width: ~170mm (single-column) or ~85mm (half-column)
- Resolution: vector (SVG/PDF) preferred, or 300 DPI PNG
- Include a small legend box explaining the three swim lane colours

### For TikZ output

Generate a complete, compilable LaTeX document using TikZ that produces this diagram. Use `\documentclass[tikz,border=5mm]{standalone}` for easy compilation.

### For Mermaid output

Generate Mermaid.js code for this diagram that can be rendered at mermaid.live.
