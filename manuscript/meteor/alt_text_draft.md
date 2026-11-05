# Alternative text of the figures: draft for the METEOR assistant

Draft written on 2026-11-05 (step S7) from the captions and the text of the chapter; every number below occurs in the chapter (checked by `tools/s7_meteor_package.py`). METEOR asks the authors to generate the alternative text with its own assistant, check it by hand and upload the exported Excel file with the manuscript. Use this draft to check, or replace, what the assistant proposes.

## Figure 1 (figures/fig1.pdf)

Heat map of per-step speedup, CPU time divided by GPU time, of single-GPU rapids-singlecell over CPU Scanpy. Rows are eleven pipeline steps, from data loading to DE testing; columns are 10k, 50k and 100k cells; each cell prints its value. A logarithmic colour scale is blue above 1 and orange below 1. Normalisation has the largest speedups (329, 206 and 173). Data loading is slower on the GPU at all three sizes (0.76-0.85), and Leiden at resolution 0.5 is slower at 10k cells (0.36).

## Figure 2 (figures/fig2.pdf)

Two dot plots of CPU-GPU agreement at 10,000 cells. Left: adjusted Rand index (filled circles) and normalised mutual information (open squares) of Leiden clustering at resolutions 0.5, 1.0 and 1.5; ARI ranges from 0.908 to 0.963 and NMI from 0.951 to 0.971. Right: HVG Jaccard and PCA Spearman absolute rho both at 1.000, kNN Jaccard at 0.930 just below its maximum of 0.9375 (dashed line), and the mean Spearman rho of DE log-fold-changes at 0.946.

## Figure 3 (figures/fig3.pdf)

Horizontal dot plot of the per-step GPU speedup on Visium HD 8 um against the DGX CPU reference, on a logarithmic axis, with 95% bootstrap intervals and a vertical line at 1. The largest speedups are UMAP (197), Geary's C (122), PCA (37.0), normalisation (30.4) and Moran's I (20.8). Spatial neighbours (0.80) and neighbourhood enrichment (1.1), run on the CPU in both pipelines, are open circles near 1. Co-occurrence from the separate check with rapids-singlecell 0.15.1 is an open diamond.

## Figure 4 (figures/fig4.pdf)

Two panels of CPU-GPU spatial concordance on Visium v1 (filled circles), Visium HD 8 um (open squares) and the Visium HD 2 um subsample (triangles). Left: Spearman rho of Moran's I and Geary's C, at least 0.9995 on all platforms, and Jaccard indices of the SVG sets ranked by Moran's I, equal to 1.000 for the top 50 and slightly lower for larger sets on Visium HD. Right: ARI and NMI of the Leiden partitions; ARI is 0.856 on Visium v1 and 0.971-0.974 on Visium HD 8 um, and falls to 0.071 on the 2 um subsample.
