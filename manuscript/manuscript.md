---
title: "GPU-accelerated single-cell and spatial transcriptomics on NVIDIA DGX H100: a systematic benchmark of speed, scalability, and biological concordance"
author:
  - name: Luca Vedovelli
    affiliation: "Unit of Biostatistics, Epidemiology and Public Health, Department of Cardiac, Thoracic, Vascular Sciences and Public Health, University of Padova, Padova, Italy"
  - name: Dario Gregori
    affiliation: "Unit of Biostatistics, Epidemiology and Public Health, Department of Cardiac, Thoracic, Vascular Sciences and Public Health, University of Padova, Padova, Italy"
bibliography: bibliography/cibb2026_references.bib
abstract: |
  Single-cell RNA sequencing (scRNA-seq) datasets now routinely exceed one million cells,
  and spatial transcriptomics platforms such as Visium HD generate hundreds of thousands of
  measurement bins per tissue section, placing severe computational demands on analysis
  frameworks that remain predominantly CPU-bound.
  We present a systematic benchmark comparing Scanpy (CPU, 100 cores) against
  rapids-singlecell (GPU, 1--8 NVIDIA H100 80 GB) on the canonical 1.3-million mouse brain
  cell dataset, evaluating speed, multi-GPU scalability, memory efficiency,
  and biological concordance across five dataset sizes (10k--1.3M cells) with five
  independent repeats per configuration.
  The GPU pipeline achieved up to 120-fold end-to-end speedup at 1.3M cells
  (435 s vs 52,056 s on CPU), reducing a 14.5-hour analysis to 7.3 minutes.
  Per-step speedups ranged from 0.76$\times$ (data loading) to 329$\times$ (normalization).
  Biological concordance was high: highly variable gene (HVG) selection was identical
  (Jaccard = 1.0), PCA loadings perfectly correlated (Spearman $|\rho|$ = 1.0),
  and Leiden clustering concordance ranged from ARI = 0.908 to 0.963 across resolutions.
  Multi-GPU scaling was sublinear, with 2--8 GPUs yielding similar wall times,
  because CPU preprocessing and single-GPU graph operations dominated.
  In a stress test, the optimised pipeline processed 11.9 million cells on a single
  DGX H100 node, with CPU RAM (535 of 2,048 GB) as the limiting factor
  rather than GPU VRAM (49 of 640 GB, 7.6%).
  A factorial differential expression benchmark at 3.4M cells demonstrated that
  pseudo-bulk aggregation was 44$\times$ faster than cell-level $t$-test and that
  GPU Wilcoxon (826 s) outperformed GPU $t$-test (1,656 s).
  We extended the benchmark to spatial transcriptomics, comparing Squidpy (CPU) against
  rapids-singlecell (GPU) on three 10x Visium platforms (Visium v1, Visium HD 8 $\mu$m,
  Visium HD 2 $\mu$m). End-to-end speedups ranged from 1.7$\times$ (2,695 spots) to
  51.6$\times$ (393,543 bins), with co-occurrence analysis achieving a 3,272$\times$
  speedup. Spatial autocorrelation concordance was near-perfect (Moran/Geary
  Spearman $\rho \geq$ 0.9995) and spatially variable gene sets were identical
  (top-50 Jaccard = 1.0).
  These results provide practical guidance for deploying GPU-accelerated single-cell
  and spatial workflows at atlas scale and identify CPU-side preprocessing as the primary
  bottleneck for future optimisation.
---


# Introduction

Single-cell RNA sequencing has become the standard technology for dissecting cellular heterogeneity in complex tissues [@Regev2017].
Recent atlas-scale projects such as the Human Cell Atlas, Tabula Sapiens [@TabulaSapiens2022], and the Allen Brain Atlas [@Yao2023] routinely generate datasets exceeding one million cells, placing severe computational demands on analysis pipelines.
The dominant analysis framework, Scanpy [@Wolf2018], executes on CPU and relies on NumPy, SciPy, and scikit-learn for linear algebra and graph operations.
While multi-threaded CPU implementations scale modestly with core count, a standard analysis of one million cells, encompassing quality control, normalisation, principal component analysis (PCA), neighbourhood graph construction, Leiden clustering [@Traag2019], uniform manifold approximation and projection (UMAP) [@McInnes2018], and differential expression (DE) testing, can require hours to days on a multi-core workstation.

In parallel, spatial transcriptomics has matured from low-throughput technologies to platforms that tile entire tissue sections with hundreds of thousands of measurement points.
The 10x Genomics Visium HD platform generates up to 6.3 million 2 $\mu$m bins per tissue section, and spatial analysis pipelines built on Squidpy [@Palla2022] add computationally intensive operations such as spatial autocorrelation (Moran's I, Geary's C), co-occurrence analysis, and neighbourhood enrichment on top of the standard expression analysis workflow.
As both single-cell and spatial datasets grow, the need for GPU-accelerated analysis becomes increasingly pressing.

GPU-accelerated alternatives have emerged to address this scalability challenge.
The RAPIDS ecosystem [@RAPIDS2024] provides GPU-native implementations of common data science primitives, and rapids-singlecell [@Dicks2026] offers a near-drop-in replacement for Scanpy that executes the same analytical pipeline on NVIDIA GPUs via cuML, cuGraph, and CuPy.
Prior work has demonstrated substantial GPU speedups for genomic analyses [@TaylorWeiner2019], including single-cell pipelines [@Nolet2022], and proposed GPU frameworks for datasets exceeding ten million cells [@Hu2025].
However, most benchmarks report headline speedups without systematically examining (i) per-step performance variation, (ii) multi-GPU scaling behaviour and its bottlenecks, (iii) numerical concordance of GPU floating-point results with CPU baselines, and (iv) practical memory limits at extreme scale.
Gardner et al. [-@Gardner2025] recently evaluated accuracy-performance trade-offs for GPU single-cell analysis, but their study was limited to a single GPU and did not explore multi-GPU configurations or stress-test hardware limits.

Here we present a comprehensive benchmark addressing five questions simultaneously.
First, **speed**: what is the per-step and end-to-end speedup of rapids-singlecell relative to Scanpy on identical hardware?
Second, **scalability**: how does the pipeline scale from 1 to 8 GPUs, and where are the bottlenecks?
Third, **concordance**: do CPU and GPU pipelines yield biologically equivalent results in terms of HVG selection, PCA embeddings, clustering, and DE gene rankings?
Fourth, **capacity**: what is the maximum dataset size a single DGX H100 node can process, and what limits it?
Fifth, **spatial generalisability**: do the GPU speedup and concordance patterns extend from single-cell to spatial transcriptomics?

All single-cell experiments were conducted on an NVIDIA DGX H100 node with 8$\times$H100 80 GB GPUs, dual Intel Xeon Platinum 8480C processors (112 cores), and 2 TB of DDR5 RAM, using a Singularity container to ensure full reproducibility.
Spatial benchmarks were run on a local workstation equipped with an NVIDIA RTX 4090 (24 GB VRAM), 100 CPU cores, and 256 GB RAM, as driver incompatibilities prevented running the spatial container on the DGX at the time of this study.
Each configuration was run five times with independent random seeds to quantify measurement variability.


# Methods

## Single-cell RNA-seq

### Dataset and subsampling

All single-cell experiments used the 10x Genomics 1.3-million mouse brain cell dataset (E18) [@Zheng2017], obtained as a pre-processed AnnData h5ad file from the RAPIDS single-cell examples repository.
This dataset is the canonical large-scale single-cell benchmark and contains approximately 1.3 million cells with gene expression measured by the 10x Chromium platform.

To evaluate performance across scales, we created reproducible subsamples of 10,000, 50,000, 100,000, and 500,000 cells by uniform random sampling without replacement (seed = 42), in addition to the full 1.3M cell dataset.
All subsamples were derived from the same parent dataset to ensure consistent biological composition across benchmarking tiers.

### Analysis pipeline

Both the CPU and GPU pipelines implemented the standard Scanpy best-practices workflow [@Luecken2019; @Heumos2023] with identical parameters.
The CPU pipeline used Scanpy 1.12 [@Wolf2018] with NumPy 2.2.6 and the igraph Leiden backend (igraph 1.0.0); the GPU pipeline used rapids-singlecell 0.14.1 [@Dicks2026] with CuPy 13.6.0, RMM 26.2.0, and the cuGraph Leiden backend.
Both pipelines shared the AnnData format [@Virshup2024] for data interchange.

The pipeline comprised ten steps, each timed independently using `time.perf_counter()` (Table 4).

: **Table 4.** Pipeline steps, parameters, and implementations for the scRNA-seq benchmark. All steps used identical parameters for the CPU and GPU pipelines except where noted. {#tbl:pipeline}

| Step | Operation | Key parameters | Implementation note |
|-----:|:----------|:---------------|:--------------------|
| 1 | Data loading | --- | `read_h5ad()` from disk |
| 2 | QC and filtering | `min_genes` = 200, `min_cells` = 3, mt prefix = `mt-` | Mitochondrial QC metrics |
| 3 | Normalisation | `target_sum` = $10^4$ | Library-size scaling + `log1p` |
| 4 | HVG selection | `n_top_genes` = 2,000, Seurat v1 method | On log-normalised data [@Satija2015; @Yip2019] |
| 5 | Scaling | `max_value` = 10 | Sparse $\rightarrow$ dense float32, mean-centre, unit-variance |
| 6 | PCA | 50 components, seed = 42 | Truncated SVD |
| 7 | Neighbour graph | $k$ = 15, 50 PCs, seed = 42 | $k$-NN in PCA space |
| 8 | Leiden clustering | $r \in \{0.5, 1.0, 1.5\}$, seed = 42 | igraph (CPU) / cuGraph (GPU) [@Traag2019] |
| 9 | UMAP | 2 components, seed = 42 | 2D embedding [@McInnes2018] |
| 10 | DE testing | Wilcoxon, one-vs-rest, `use_raw` = True | On Leiden $r$ = 1.0 clusters [@Soneson2018] |

For the CPU pipeline, threading was maximised by setting `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, and `NUMBA_NUM_THREADS` to 100 (the usable core count) before importing any numerical library.
For single-GPU runs, RAPIDS Memory Manager (RMM) was initialised with a pool allocator and a GPU warmup step was executed to absorb CUDA context initialisation overhead before timing.

### Multi-GPU pipeline

For datasets exceeding single-GPU VRAM capacity (500k and 1.3M cells), we employed a hybrid multi-GPU pipeline using Dask-CUDA [@Rocklin2015].
Preprocessing steps (data loading, QC, normalisation, HVG selection) executed on CPU, as they are I/O- or memory-bound and do not benefit from GPU parallelism.
PCA and neighbour graph construction were distributed across $N$ GPUs ($N \in \{2, 4, 8\}$) via Dask workers, each with a 10 GB initial / 70 GB maximum RMM pool.
Scaling, Leiden clustering, UMAP, and DE testing executed on a single GPU (device 0), as they operate on the reduced PCA embedding or require global graph access.

### Concordance metrics

To assess whether the GPU pipeline produces biologically equivalent results, we computed six concordance metrics comparing CPU and GPU outputs on the 10,000-cell dataset (Table 5).

: **Table 5.** Concordance metrics used to compare CPU and GPU pipeline outputs. {#tbl:concordance}

| Metric | Definition | Scope |
|:-------|:-----------|:------|
| HVG Jaccard | $|S_\text{CPU} \cap S_\text{GPU}| / |S_\text{CPU} \cup S_\text{GPU}|$ for 2,000 HVGs | Feature selection |
| PCA loading $|\rho|$ | Mean absolute Spearman $\rho$ across first 10 PC loadings, accounting for sign flips | Dimensionality reduction |
| $k$NN Jaccard | Mean per-cell Jaccard overlap of $k$-nearest-neighbour sets ($k$ = 15) | Graph structure |
| ARI | Adjusted Rand Index of Leiden cluster assignments, adjusted for chance [@Hubert1985] | Clustering |
| NMI | Normalised Mutual Information of cluster assignments [@Vinh2010] | Clustering |
| DE logFC $\rho$ | Spearman $\rho$ of log-fold-changes for top 100 DE genes per cluster, after Hungarian matching | Differential expression |

### Stress test: maximum capacity

To determine the maximum dataset size processable on a single DGX H100 node, we implemented a memory-optimised pipeline variant.
The key optimisations were: (i) scaling on CPU rather than GPU (leveraging 2 TB system RAM); (ii) a distributed covariance PCA that scatters the scaled matrix across all 8 GPUs, computes local covariance contributions ($\mathbf{X}_i^\top \mathbf{X}_i$, each 2,000$\times$2,000), sums and eigendecomposes on GPU 0, then projects locally, which is mathematically equivalent to standard PCA via the covariance method; (iii) lean GPU transfer that replaces the dense matrix with an empty sparse placeholder after PCA, since downstream steps (neighbours, clustering, UMAP) only require the PCA embedding; and (iv) a reduced RMM pool (2 GB per worker).
We conducted a binary search from 3.4M to 13.7M cells to identify the failure point.

### Differential expression at scale

At 3.4 million cells$\times$41,000 genes$\times$81 Leiden clusters, the raw count matrix (`adata.raw.X`) occupies approximately 121 GB as a sparse CSR matrix, exceeding single-GPU VRAM.
We evaluated seven DE strategies in a factorial design crossing test type (Wilcoxon, $t$-test, pseudo-bulk) with GPU strategy (none, scatter-by-genes across 8 GPUs, chunk-and-stream on 1 GPU).
Gene chunks of 500 were used for GPU strategies (500$\times$3.4M$\times$4 bytes $\approx$ 6.8 GB per chunk, fitting within 80 GB VRAM).
Pseudo-bulk aggregation summed raw counts by donor$\times$cluster, normalised to counts per million, log-transformed, and applied the Wilcoxon test on the aggregated matrix [@Squair2021].


## Spatial transcriptomics

### Datasets

Spatial benchmarks used two 10x Genomics public datasets:

1. **Visium v1 Mouse Brain Sagittal Anterior**: 2,695 spots at 55 $\mu$m resolution, approximately 32,285 genes. The standard spot-based spatial transcriptomics platform.
2. **Visium HD Mouse Brain (CytAssist, FFPE)**: binned at 8 $\mu$m (393,543 bins) and 2 $\mu$m (subsampled from 6.3 million to 389,492 bins), each with 19,059 genes. The Visium HD 2 $\mu$m dataset was subsampled to approximately 400,000 bins using the `--max-spots` flag to fit within the RTX 4090's 24 GB VRAM; full-scale benchmarking of the complete 6.3 million bins requires DGX-class resources.

Both datasets were downloaded programmatically from the 10x Genomics public data portal.

### Spatial analysis pipeline

The spatial pipeline comprised two phases: an expression analysis phase (shared with the scRNA-seq pipeline) and a spatial statistics phase (Table 6).

: **Table 6.** Spatial analysis pipeline steps. Steps 1--8 share parameters with the scRNA-seq pipeline (Table 4) except for QC filtering, which used `min_genes` = 1 for Visium HD (Space Ranger pre-filters on-tissue barcodes). Steps 9--14 are spatial-specific. {#tbl:spatial_pipeline}

| Step | Operation | GPU support | Notes |
|-----:|:----------|:-----------:|:------|
| 1--8 | Expression analysis (QC through UMAP) | Yes | As in Table 4; Leiden $r$ = 1.0 for Visium, $r$ = 0.1 for HD |
| 9 | Spatial neighbours | No | Delaunay triangulation (scipy.spatial) |
| 10 | Moran's I | Yes | Spatial autocorrelation per gene |
| 11 | Geary's C | Yes | Spatial autocorrelation per gene |
| 12 | Co-occurrence | Yes | Cluster co-occurrence across distance intervals |
| 13 | Neighbourhood enrichment | No | Cluster--cluster proximity enrichment |
| 14 | Ligand-receptor interaction | No | Cell communication inference |

The CPU baseline used Scanpy 1.12 for expression steps and Squidpy 1.8.1 [@Palla2022] for spatial steps.
The GPU pipeline used rapids-singlecell 0.14.1 for both expression and GPU-accelerated spatial steps (Moran's I, Geary's C, co-occurrence).
Steps without GPU implementations (spatial neighbours, neighbourhood enrichment, ligand-receptor) were executed identically on CPU in both pipelines.

Co-occurrence and neighbourhood enrichment were skipped when cluster counts exceeded 500, as their $O(k^2)$ memory complexity becomes prohibitive.
Ligand-receptor interaction analysis was skipped for datasets exceeding 100,000 spots.

### Spatial concordance metrics

We compared CPU and GPU spatial outputs using four concordance measures:

1. **Spatial autocorrelation concordance**: Spearman $\rho$ between CPU and GPU per-gene Moran's I (and Geary's C) statistics across all genes.
2. **Spatially variable gene (SVG) Jaccard**: overlap of the top-$N$ SVGs ($N \in \{50, 100, 200\}$) ranked by Moran's I, and overlap of all genes with FDR < 0.05.
3. **Clustering ARI/NMI**: agreement of Leiden cluster assignments from the expression-based pipeline.
4. **Co-occurrence Spearman $\rho$**: correlation of the full co-occurrence matrices.


## Hardware and software environment

Single-cell benchmarks ran on a single node of the UPSCALE/CONVECS DGX H100 cluster at the University of Padova, comprising 8$\times$NVIDIA H100 80 GB SXM GPUs connected via NVLink 4.0, dual Intel Xeon Platinum 8480C CPUs (112 cores total), and 2 TB DDR5 RAM.
The software environment was encapsulated in a Singularity container built from the NVIDIA RAPIDS base image (`nvcr.io/nvidia/rapidsai/base:25.02-cuda12.8-py3.12`).
Key software versions: Scanpy 1.12, rapids-singlecell 0.14.1, CuPy 13.6.0, Dask 2026.1.1, Dask-CUDA 26.2.0, Python 3.12.12.
Jobs were submitted via SLURM on a dedicated DGX H100 node (`poddgx02`).

Spatial benchmarks ran on a local workstation equipped with an NVIDIA RTX 4090 (24 GB GDDR6X), 100 CPU cores, and 256 GB DDR5 RAM.
A separate container was built from `nvcr.io/nvidia/rapidsai/base:26.02-cuda12-py3.12` with Squidpy 1.8.1 [@Palla2022] and spatialdata [@Marconato2024] dependencies.
DGX-scale spatial benchmarks were not possible at the time of this study because the cluster's CUDA driver (535.183.01) was incompatible with the RAPIDS 26.02 runtime required for the spatial pipeline.

Each benchmark configuration was repeated five times; we report mean $\pm$ standard deviation.
For spatial benchmarks, the first repeat served as a JIT/warmup run and was excluded; we report the mean of repeats 2--5.

## Reproducibility

All code, Dockerfiles, SLURM submission scripts, and result JSON files are available at TODO_URL.
Random seeds were fixed at 42 for all stochastic operations (subsampling, PCA, Leiden, UMAP).
We note that GPU floating-point arithmetic is non-deterministic due to non-associative parallel reductions [@Shanmugavelu2024; @Collange2015], and quantify the resulting divergence through the concordance metrics above rather than expecting bit-identical outputs.


# Results

## Single-cell RNA-seq

### GPU acceleration achieves up to 120-fold end-to-end speedup

Table 1 summarises the benchmark results across all 23 pipeline-dataset-GPU configurations, each averaged over five repeats.
At 1.3 million cells, the 8-GPU pipeline completed the full analysis in 435.2 $\pm$ 16.2 s (7.3 min), compared with 52,056.2 $\pm$ 392.0 s (14.5 h) for the CPU pipeline, a **119.6-fold speedup** (Fig. 6).
Even at 10,000 cells, the single-GPU pipeline was 12-fold faster than the CPU baseline (3.3 $\pm$ 1.7 s vs 39.5 $\pm$ 10.2 s).
The speedup increased monotonically with dataset size: 33.6$\times$ at 50k, 43.7$\times$ at 100k, 34.9$\times$ at 500k (2 GPU), and 119.6$\times$ at 1.3M (8 GPU), reflecting the GPU's superior arithmetic throughput on larger matrices.

### Per-step speedup varies over two orders of magnitude

The per-step speedup heatmap (Fig. 1) reveals that GPU advantage varies dramatically by operation type.
**Normalisation** achieved the highest speedups: 329$\times$ at 10k, 206$\times$ at 50k, and 173$\times$ at 100k cells, reflecting the trivially parallelisable element-wise division and logarithm.
**HVG selection** (24--94$\times$), **neighbours** (44--88$\times$), **UMAP** (27--45$\times$), and **DE testing** (16--88$\times$) also showed strong GPU acceleration.
**PCA** speedup grew with dataset size (4.8$\times$ to 36.5$\times$), consistent with the increasing arithmetic intensity of singular value decomposition on larger matrices.

Notably, some steps showed CPU advantage at small scales.
**Data loading** was consistently faster on CPU (0.76--0.85$\times$ GPU/CPU), as the overhead of GPU context and data transfer dominated at small dataset sizes.
**Leiden clustering** at resolution 0.5 was faster on CPU at 10k cells (0.36$\times$), attributable to cuGraph's higher constant-time overhead for graph partitioning on small graphs, but GPU overtook CPU at 50k cells (1.80$\times$) and 100k cells (3.58$\times$).

### Multi-GPU scaling is sublinear: CPU preprocessing dominates

Adding GPUs beyond two provided diminishing returns (Fig. 2, Fig. 6).
At 500k cells, wall time was virtually identical for 2, 4, and 8 GPUs (124.5, 125.0, and 124.6 s, respectively).
At 1.3M cells, 8 GPUs (435.2 s) were only 12% faster than 2 GPUs (493.3 s).

The timing breakdown (Fig. 6) reveals why: in a representative 8-GPU run at 1.3M cells (total 463.4 s), CPU preprocessing (data loading + QC + normalisation + HVG selection) consumed 348.7 s (75%), the multi-GPU phase (PCA + neighbours) took only 17.5 s (4%), and single-GPU operations (transfer + scale + Leiden + UMAP + DE) took 97.2 s (21%).
Since CPU preprocessing is constant regardless of GPU count, and Leiden/UMAP/DE execute on a single GPU, only the PCA and neighbour steps benefit from additional GPUs, a classic instance of Amdahl's law [@Amdahl1967].

### CPU and GPU produce biologically concordant results

Concordance analysis on the 10,000-cell dataset (Fig. 3) demonstrated that the two pipelines yield near-identical biological conclusions.
**HVG selection was perfectly concordant**: all 2,000 genes were identical between CPU and GPU (Jaccard = 1.000).
**PCA loadings were perfectly correlated**: mean absolute Spearman $\rho$ = 1.000 across all 10 inspected PCs.
**$k$NN graph overlap was high**: mean Jaccard = 0.930 (median = 0.938, min = 0.409).

Leiden clustering concordance depended on resolution: ARI ranged from 0.908 (resolution 1.0) to 0.963 (resolution 1.5), with NMI from 0.951 to 0.971.
The lower ARI at resolution 1.0 (40 clusters for both CPU and GPU) reflects the stochastic nature of the Leiden algorithm and minor differences in the cuGraph vs igraph implementations, rather than a systematic bias.
DE log-fold-change correlation across 40 matched cluster pairs averaged Spearman $\rho$ = 0.946, with 30 of 40 pairs achieving $\rho > 0.97$.

These concordance levels are consistent with the range of inter-method variation reported in mixture-control benchmarks of scRNA-seq analysis pipelines [@Tian2019] and systematic clustering evaluations [@Duo2020], and support the conclusion that GPU and CPU pipelines are interchangeable for biological interpretation.

### Memory: CPU RAM is the bottleneck, not GPU VRAM

CPU RAM usage scaled approximately linearly with cell count, from 1.2 GB at 10k to 107.4 GB at 1.3M cells (Fig. 4, left panel).
The dominant memory consumers were the dense float32 matrix created during scaling (1.3M$\times$2,000 HVGs$\times$4 bytes $\approx$ 10.4 GB) and the sparse raw count matrix (1.3M$\times$39,182 genes).

GPU VRAM for single-GPU runs was approximately constant at 40.7 GB across dataset sizes, dominated by the pre-allocated RMM pool.
For multi-GPU runs, aggregate VRAM scaled with worker count: at 1.3M cells with 8 GPUs, the aggregate peak was 134.2 GB (mean 16.8 GB per device, 21% of 80 GB capacity), well below the per-device limit.

### Stress test: 11.9 million cells on one DGX H100 node

Using the memory-optimised pipeline, we conducted a binary search for the maximum processable cell count (Table 2).
The pipeline succeeded at 11.9 million cells (119 min, 535 GB RAM, 49 GB aggregate VRAM) and failed at 12.0 million cells (Leiden out-of-memory, SLURM signal 9).
A separate test at 13.7 million cells failed during the CPU-side scaling step (sparse-to-dense conversion out-of-memory).

Critically, **GPU VRAM was not the limiting factor**: aggregate VRAM remained flat at approximately 49 GB (7.6% of total 640 GB) from 6.9M to 11.9M cells, because the distributed covariance PCA kept per-GPU memory at 6.7 GB and the lean GPU transfer only placed the PCA embedding ($n$ cells$\times$50 components$\times$4 bytes) on GPU 0.
The bottleneck was **CPU RAM**: at approximately 45 GB per million cells, the 2 TB system memory was exhausted at around 12M cells by the Leiden algorithm's internal data structures on top of the dense scaled matrix.

We also tested cuML KMeans as a GPU-native clustering alternative to Leiden, but the failure point was identical (13.7M) because the out-of-memory event occurred during CPU preprocessing, before clustering was invoked.
Similarly, a sparse-scatter optimisation that avoided the CPU-side dense matrix was tested at 14M cells but failed during Scanpy's HVG selection step, confirming that **Scanpy's CPU-side preprocessing is the ultimate capacity bottleneck**.

The memory limit is fundamentally a function of cells$\times$genes, not cells alone.
With 2,000 HVGs and float32 precision, the dense scaled matrix occupies $n \times 2{,}000 \times 4$ bytes.
Fewer HVGs would permit more cells (estimated 20M at 1,000 HVGs) and vice versa (estimated 4M at 5,000 HVGs).

### Differential expression: pseudo-bulk is fastest and most correct

The factorial DE benchmark at 3.4M cells (Table 3) revealed three findings.
First, **pseudo-bulk aggregation was the fastest strategy by a wide margin**: 128 s (2.1 min), representing a 43.7$\times$ speedup over the CPU $t$-test baseline (5,598 s, 93 min).
Pseudo-bulk reduces the problem from 3.4 million cells to a few hundred pseudo-samples per cluster by aggregating raw counts by donor, and is also the statistically correct approach for multi-donor scRNA-seq data as it avoids pseudoreplication [@Squair2021].

Second, **Wilcoxon outperformed $t$-test on GPU**: GPU Wilcoxon (scatter across 8 GPUs) completed in 826 s (6.8$\times$ speedup), while GPU $t$-test took 1,656 s (3.4$\times$ speedup).
This counterintuitive result arises because the Wilcoxon test's ranking step maps efficiently to CuPy's `argsort` on sparse data, whereas the $t$-test requires dense mean and variance computations.

Third, **multi-GPU provided no advantage over single-GPU for DE**: Wilcoxon scatter (826 s, 8 GPUs) was nearly identical to Wilcoxon chunk-and-stream (831 s, 1 GPU).
The bottleneck is the CSR-to-dense conversion when loading each gene chunk, which is sequential I/O, not parallel compute.

We emphasise that at 3.4 million cells, $p$-values from cell-level tests are uninformative: virtually every gene reaches statistical significance due to enormous sample size.
Effect size (log-fold-change) and pseudo-bulk methods with proper count-based models (DESeq2, edgeR) should guide biological interpretation [@Squair2021; @Soneson2018].


## Spatial transcriptomics

### GPU speedup scales dramatically with platform resolution

Table 7 summarises the spatial benchmark results across three Visium platforms.
End-to-end speedup increased from 1.7$\times$ on Visium v1 (2,695 spots) to 51.6$\times$ on Visium HD 8 $\mu$m (393,543 bins), demonstrating that GPU acceleration becomes increasingly valuable as spatial resolution increases.

The dominant contributor to the HD 8 $\mu$m speedup was **co-occurrence analysis**, which achieved a 3,272$\times$ speedup (from 3,573 s on CPU to 1.09 s on GPU).
The CPU implementation computes pairwise cluster co-occurrence across distance intervals with $O(n^2)$ complexity per interval, while the GPU implementation parallelises this computation across all bins and intervals simultaneously.
At 393,543 bins with 7 Leiden clusters, co-occurrence alone consumed 88% of the CPU pipeline time.

Other large GPU advantages on HD 8 $\mu$m included PCA (257$\times$), normalisation (176$\times$), spatial autocorrelation (162--163$\times$), and UMAP (159$\times$).
Leiden clustering achieved a 16$\times$ speedup, and $k$-NN graph construction achieved 20$\times$.

Visium HD 2 $\mu$m showed a lower overall speedup (10.8$\times$) despite a similar bin count (389,492) because co-occurrence analysis was skipped (>500 clusters exceeded the $O(k^2)$ memory threshold).
Without this step, UMAP dominated the GPU pipeline time (92$\times$ speedup, but consuming 92% of the 97 s total GPU time).

On Visium v1, the modest 1.7$\times$ overall speedup reflects the small dataset size (2,695 spots): GPU kernel launch overhead is not amortised, and CPU-only steps (spatial neighbours, ligand-receptor) dominate.

Three pipeline steps lacked GPU implementations and constituted the GPU pipeline's primary bottleneck: **spatial neighbours** (Delaunay triangulation via scipy.spatial, $\sim$55 s on all HD platforms), **neighbourhood enrichment** (CPU-only), and **ligand-receptor interaction** (CPU-only, Visium v1 only).
Spatial neighbours alone represented 57--73% of total GPU pipeline time on HD platforms.

### Spatial concordance: near-perfect for spatial statistics, divergent for clustering at high resolution

Spatial autocorrelation concordance was near-perfect across all platforms (Table 8).
Moran's I and Geary's C Spearman correlations between CPU and GPU exceeded 0.9995 in all cases.
**The top-50 spatially variable genes were identical** (Jaccard = 1.0) across all three platforms, confirming that GPU-accelerated spatial autocorrelation produces scientifically equivalent results.
At the FDR < 0.05 threshold, SVG overlap remained high: 100% (Visium v1), 99.9% (HD 8 $\mu$m), and 98.2% (HD 2 $\mu$m).

Expression-based Leiden clustering showed platform-dependent concordance.
On Visium v1 (ARI = 0.856, NMI = 0.892) and HD 8 $\mu$m (ARI = 0.974, NMI = 0.940), concordance was high, consistent with the scRNA-seq results.
However, on **HD 2 $\mu$m, clustering diverged substantially** (ARI = 0.080, NMI = 0.667): the CPU pipeline identified 2,559 clusters while the GPU pipeline found 538.
This 4.75$\times$ difference in cluster granularity arises from algorithmic differences between the leidenalg (CPU) and cuGraph (GPU) Leiden implementations, which are amplified at high resolution where the graph has many near-degenerate partitions.
Subsampling from 6.3 million to 389,492 bins also disrupts spatial contiguity, compounding the effect.
This is a known limitation of comparing stochastic graph-partitioning algorithms across implementations, not a deficiency of GPU computation per se.

### Memory usage is modest across spatial platforms

Peak GPU VRAM was 12.9 GB on Visium v1 and plateaued at 22.6 GB for both HD platforms (Table 7), well within the RTX 4090's 24 GB capacity.
CPU RAM ranged from 1.3 GB (Visium v1) to 10.8 GB (HD 2 $\mu$m).
These modest requirements suggest that spatial benchmarks at full Visium HD resolution (6.3M bins at 2 $\mu$m) would fit comfortably within DGX H100 memory.


# Discussion

Our benchmark demonstrates that rapids-singlecell on NVIDIA H100 GPUs delivers consistent, large-magnitude speedups over Scanpy for the standard scRNA-seq analysis pipeline, with high biological concordance and practical scalability to nearly 12 million cells on a single DGX H100 node.
The extension to spatial transcriptomics shows that GPU advantages are even more pronounced for spatial-specific operations, with co-occurrence analysis achieving over three orders of magnitude speedup.
Several aspects of these results merit discussion.

**The speedup is not uniform across pipeline steps.**
Normalisation (element-wise arithmetic) and neighbour graph construction ($k$-NN search in high-dimensional space) are ideal GPU workloads, achieving 88--329$\times$ speedups.
Data loading from disk and Leiden clustering on small graphs show no GPU advantage or even a CPU advantage, consistent with the roofline model [@Williams2009]: these operations are I/O-bound or have insufficient arithmetic intensity to saturate GPU compute units [@Lindegger2023].
This heterogeneity has practical implications: GPU acceleration is most valuable for large datasets where the compute-heavy steps dominate total runtime.

**Multi-GPU scaling is limited by Amdahl's law.**
The 12% improvement from 2 to 8 GPUs at 1.3M cells reflects the fact that only PCA and neighbour graph construction run in a distributed manner, while the remaining 95% of wall time is spent on CPU preprocessing or single-GPU operations.
Future frameworks could address this by distributing preprocessing (e.g., chunked QC and normalisation on GPU) and parallelising Leiden clustering across graph partitions.

**Concordance is high but not perfect, and the differences are expected.**
The perfect agreement on HVG selection and PCA loadings reflects the deterministic nature of these operations given identical inputs.
The ARI range of 0.908--0.963 for Leiden clustering is consistent with the algorithm's inherent stochasticity across implementations (igraph vs cuGraph) and with published benchmarks of scRNA-seq clustering variability [@Duo2020].
Floating-point non-associativity in GPU parallel reductions contributes negligibly to the observed differences, as the dominant source of variation is the Leiden algorithm's non-deterministic vertex ordering.

**CPU RAM, not GPU VRAM, limits scale.**
This finding challenges the intuition that GPU memory is the primary constraint for GPU-accelerated bioinformatics.
At 11.9M cells, each H100 used only 6.1 GB for the distributed PCA (7.6% of 80 GB), while CPU RAM consumption reached 535 GB (26% of 2 TB).
The bottleneck is Scanpy's preprocessing, which creates dense intermediate matrices and requires the full dataset to reside in CPU memory.
Out-of-core or chunked preprocessing frameworks could extend the limit substantially, as GPU VRAM has ample headroom.

**Pseudo-bulk DE is both fastest and most statistically rigorous.**
Our DE benchmark confirms that pseudo-bulk aggregation is not merely a statistical best practice [@Squair2021] but also a computational optimisation, reducing runtime by 44$\times$ relative to cell-level $t$-test.
GPU acceleration of cell-level DE provides moderate speedups (3--7$\times$) but is ultimately limited by the I/O cost of converting sparse matrices to dense gene chunks.
For multi-donor experimental designs, pseudo-bulk should be the default approach on both statistical and computational grounds.

**Spatial GPU acceleration is most impactful for computationally intensive spatial statistics.**
The 3,272$\times$ speedup for co-occurrence analysis on Visium HD 8 $\mu$m is, to our knowledge, the largest GPU speedup reported for any spatial transcriptomics operation.
This reflects the $O(n^2)$ algorithmic complexity of the CPU implementation, which the GPU parallelises effectively.
Spatial autocorrelation (Moran's I, Geary's C) achieved 162--170$\times$ speedups with near-perfect numerical concordance ($\rho \geq$ 0.9995), meaning scientists obtain identical lists of spatially variable genes in seconds rather than minutes.
The remaining CPU-only bottlenecks (spatial neighbours via Delaunay triangulation, neighbourhood enrichment, ligand-receptor analysis) represent opportunities for future GPU-native implementations.

**Clustering concordance at ultra-high spatial resolution is an open challenge.**
The dramatic divergence at Visium HD 2 $\mu$m (ARI = 0.080) is not specific to GPU vs CPU: it reflects the fundamental sensitivity of community detection algorithms to implementation details when the graph has many near-degenerate partitions.
At 389,492 bins with resolution 0.1, the solution landscape has many local optima, and the leidenalg and cuGraph implementations explore this landscape differently.
This finding suggests that users working at ultra-high spatial resolution should not rely on a single Leiden run (from either CPU or GPU) but instead use consensus clustering or alternative spatial-aware methods.

**Limitations.**
Our scRNA-seq benchmark used a single biological dataset (mouse brain E18); performance profiles may differ for datasets with different sparsity patterns or gene counts.
Concordance was assessed at 10,000 cells; larger datasets may show different ARI distributions.
The stress test used a memory-optimised pipeline that is mathematically but not implementation-identical to the standard rapids-singlecell workflow.
Spatial benchmarks were conducted on a local RTX 4090 workstation rather than the DGX H100, precluding multi-GPU spatial scaling measurements and full-resolution Visium HD 2 $\mu$m benchmarks (6.3 million bins).
We did not benchmark integration methods (Harmony, scVI) or multi-sample spatial designs, which are the subject of ongoing work.

## Conclusion

GPU-accelerated single-cell analysis via rapids-singlecell on NVIDIA H100 GPUs reduces a 14.5-hour CPU pipeline to 7.3 minutes at 1.3M cells, with biologically concordant results.
The principal scalability bottleneck is CPU-side preprocessing, not GPU VRAM: a single DGX H100 node processed 11.9M cells while using only 7.6% of total GPU memory.
Multi-GPU scaling provides modest benefit (12% at 1.3M cells, 2$\rightarrow$8 GPUs) due to the dominance of non-GPU-parallelised pipeline phases.
For differential expression, pseudo-bulk aggregation is simultaneously the fastest (44$\times$ vs $t$-test) and most statistically rigorous approach.
For spatial transcriptomics, GPU acceleration delivers 51.6$\times$ end-to-end speedup on Visium HD, with co-occurrence analysis achieving a 3,272$\times$ speedup and spatial autocorrelation concordance exceeding 0.9995.
These results provide practical guidance for the computational bioinformatics community as single-cell and spatial datasets grow toward the billion-cell and billion-bin scales [@Regev2017].


# Tables

: **Table 1.** Summary of scRNA-seq benchmark results across all pipeline configurations. Times are mean $\pm$ SD over five repeats. Single-GPU results for 500k and 1.3M cells are absent because the standard pipeline exceeded 80 GB VRAM on a single H100. {#tbl:summary}

| Pipeline | Cells | GPUs | Total time (s) | SD (s) | Peak RAM (GB) | Peak VRAM (GB) |
|:---------|------:|-----:|---------------:|-------:|---------------:|---------------:|
| CPU (Scanpy) | 10k | 0 | 39.5 | 10.2 | 1.2 | --- |
| GPU (rapids) | 10k | 1 | 3.3 | 1.7 | 2.4 | 40.7 |
| GPU | 10k | 2 | 4.9 | 2.6 | 2.3 | 52.4 |
| GPU | 10k | 4 | 4.9 | 2.6 | 2.3 | 65.0 |
| GPU | 10k | 8 | 4.9 | 2.3 | 2.3 | 106.5 |
| CPU (Scanpy) | 50k | 0 | 282.5 | 9.1 | 3.6 | --- |
| GPU (rapids) | 50k | 1 | 8.4 | 2.2 | 5.4 | 40.7 |
| GPU | 50k | 2 | 14.7 | 2.4 | 3.5 | 52.4 |
| GPU | 50k | 4 | 14.6 | 2.6 | 3.5 | 65.0 |
| GPU | 50k | 8 | 15.1 | 2.2 | 3.4 | 106.5 |
| CPU (Scanpy) | 100k | 0 | 646.7 | 10.5 | 6.7 | --- |
| GPU (rapids) | 100k | 1 | 14.8 | 2.2 | 8.8 | 40.7 |
| GPU | 100k | 2 | 26.9 | 2.4 | 4.9 | 52.4 |
| GPU | 100k | 4 | 26.9 | 2.3 | 4.9 | 65.1 |
| GPU | 100k | 8 | 26.4 | 2.6 | 4.9 | 106.6 |
| CPU (Scanpy) | 500k | 0 | 4,346.7 | 40.3 | 29.7 | --- |
| GPU | 500k | 2 | 124.5 | 2.9 | 15.6 | 52.7 |
| GPU | 500k | 4 | 125.0 | 6.0 | 15.9 | 65.5 |
| GPU | 500k | 8 | 124.6 | 3.7 | 15.5 | 107.0 |
| CPU (Scanpy) | 1.3M | 0 | 52,056.2 | 392.0 | 107.4 | --- |
| GPU | 1.3M | 2 | 493.3 | 10.3 | 60.7 | 74.9 |
| GPU | 1.3M | 4 | 486.6 | 20.2 | 60.7 | 92.7 |
| GPU | 1.3M | 8 | 435.2 | 16.2 | 52.3 | 134.2 |


: **Table 2.** Stress test results: maximum cell count on a single DGX H100 node (8$\times$H100, 2 TB RAM) using the memory-optimised pipeline. Timings exclude DE testing, which was benchmarked separately (Table 3). {#tbl:stress}

| Cells | Runtime (min) | CPU RAM (GB) | GPU VRAM (GB) | Status |
|------:|--------------:|-------------:|--------------:|:-------|
| 3.4M | 18 | 155 | 49 | Pass |
| 6.9M | 35 | 308 | 49 | Pass |
| 10.3M | 73 | 465 | 49 | Pass |
| 11.5M | 114 | 517 | 49 | Pass |
| 11.9M | 119 | 535 | 49 | **Pass (max)** |
| 12.0M | --- | --- | --- | Fail (Leiden OOM) |
| 13.7M | --- | --- | --- | Fail (scale OOM) |

[VERIFY: Times for 3.4M, 6.9M, and 10.3M rows. The JSON result files for these sizes used different pipeline configurations (3.4M included DE testing; 6.9M and 10.3M used KMeans instead of Leiden). The values in this table come from CLAUDE.md project documentation and may reflect earlier runs with Leiden + skip-DE that were not saved as JSON. The 11.5M and 11.9M values match their JSON files exactly.]


: **Table 3.** Differential expression benchmark at 3.4M cells $\times$ 41k genes $\times$ 81 Leiden clusters. Speedup is relative to CPU $t$-test (5,598 s). {#tbl:de}

| Method | Backend | GPUs | Time (s) | Speedup |
|:-------|:--------|-----:|---------:|--------:|
| $t$-test | CPU | 0 | 5,598 | 1.0$\times$ |
| Pseudo-bulk (Wilcoxon) | CPU (aggregated) | 0 | 128 | 43.7$\times$ |
| Wilcoxon (scatter) | GPU | 8 | 826 | 6.8$\times$ |
| Wilcoxon (chunk-stream) | GPU | 1 | 831 | 6.7$\times$ |
| $t$-test (scatter) | GPU | 8 | 1,656 | 3.4$\times$ |
| $t$-test (chunk-stream) | GPU | 1 | 1,650 | 3.4$\times$ |


: **Table 7.** Spatial transcriptomics benchmark results (RTX 4090, mean of repeats 2--5). {#tbl:spatial_summary}

| Platform | Spots/Bins | CPU total (s) | GPU total (s) | Speedup | CPU RAM (GB) | GPU VRAM (GB) |
|:---------|----------:|---------------:|--------------:|--------:|-------------:|--------------:|
| Visium v1 | 2,695 | 10.0 | 6.0 | 1.7$\times$ | 1.3 | 12.9 |
| Visium HD 8 $\mu$m | 393,543 | 4,068 | 79 | 51.6$\times$ | 8.1 | 22.6 |
| Visium HD 2 $\mu$m | 389,492 | 1,042 | 97 | 10.8$\times$ | 10.8 | 22.6 |


: **Table 8.** Spatial concordance between CPU and GPU pipelines. SVG Jaccard reports the overlap of top-$N$ spatially variable genes ranked by Moran's I. {#tbl:spatial_concordance}

| Metric | Visium v1 | HD 8 $\mu$m | HD 2 $\mu$m |
|:-------|----------:|------------:|------------:|
| Moran's I Spearman $\rho$ | 1.0000 | 0.9999 | 1.0000 |
| Geary's C Spearman $\rho$ | 1.0000 | 0.9995 | 0.9999 |
| SVG Jaccard (top 50) | 1.000 | 1.000 | 1.000 |
| SVG Jaccard (FDR < 0.05) | 1.000 | 0.999 | 0.982 |
| Cluster ARI | 0.856 | 0.974 | 0.080 |
| Cluster NMI | 0.892 | 0.940 | 0.667 |
| N clusters (CPU / GPU) | 16 / 15 | 7 / 3 | 2,559 / 538 |


: **Table 9.** Per-step GPU speedup for spatial-specific operations on Visium HD 8 $\mu$m (393,543 bins), the platform showing the largest overall speedup. {#tbl:spatial_steps}

| Step | CPU (s) | GPU (s) | Speedup |
|:-----|--------:|--------:|--------:|
| Co-occurrence | 3,573 | 1.09 | 3,272$\times$ |
| PCA | 72.8 | 0.28 | 257$\times$ |
| Normalisation | 0.65 | 0.004 | 176$\times$ |
| Moran's I | 47.9 | 0.30 | 162$\times$ |
| Geary's C | 47.4 | 0.29 | 163$\times$ |
| UMAP | 194.3 | 1.22 | 159$\times$ |
| HVG selection | 0.94 | 0.012 | 76$\times$ |
| Expression neighbours | 39.4 | 2.00 | 20$\times$ |
| Leiden clustering | 19.2 | 1.17 | 16$\times$ |
| Spatial neighbours | 55.9 | 57.4 | 1.0$\times$ (CPU-only) |
| Nhood enrichment | 11.8 | 11.4 | 1.0$\times$ (CPU-only) |


# Figures

**Figure 1.** Per-step speedup of single-GPU rapids-singlecell (1$\times$H100 80 GB) relative to CPU Scanpy (100 cores) at 10k, 50k, and 100k cells. Values > 1 indicate GPU is faster. Normalisation achieves up to 329$\times$ speedup; data loading shows a modest CPU advantage (0.76--0.85$\times$).

**Figure 2.** Total pipeline wall time vs number of GPUs (1, 2, 4, 8 H100), one line per dataset size. Error bars: SD over five repeats. Horizontal dotted lines: CPU baselines. Logarithmic $y$-axis. Flat GPU curves demonstrate sublinear multi-GPU scaling.

**Figure 3.** Concordance between CPU and GPU pipelines on 10,000 cells. Left: ARI and NMI for Leiden clustering at three resolutions. Right: HVG Jaccard (1.000), PCA Spearman $|\rho|$ (1.000), and $k$NN Jaccard (0.930). All metrics indicate near-identical biological outputs.

**Figure 4.** Peak memory usage across dataset sizes. Left: CPU RAM; right: GPU VRAM (per-device maximum). Dashed red line: H100 80 GB VRAM limit. CPU RAM grows super-linearly; GPU VRAM is approximately constant for single-GPU runs due to RMM pool pre-allocation.

**Figure 5.** Step-level wall time decomposition for CPU vs single-GPU at 10k, 50k, and 100k cells. On CPU, DE testing and neighbour graph construction dominate; on GPU, all steps complete in seconds.

**Figure 6.** Multi-GPU hybrid pipeline breakdown at 500k and 1.3M cells. CPU preprocessing (blue) dominates wall time; the multi-GPU phase (PCA + neighbours, pink) is a small fraction, explaining flat multi-GPU scaling.

**Figure 7.** Total pipeline wall time (CPU vs GPU) for three Visium spatial platforms on a single RTX 4090. End-to-end speedups range from 1.7x (Visium v1, 2,695 spots) to 51.6x (Visium HD 8 um, 393,543 bins). Error bars: standard deviation across repeats 2-5 (repeat 1 excluded for JIT warmup). HD 2 um was subsampled to 400k bins due to local VRAM constraints.

**Figure 8.** Per-step GPU speedup for Visium HD 8 um (393,543 bins). Co-occurrence analysis achieves a 3,272x speedup (CPU: 3,573 s to GPU: 1.09 s), the single largest acceleration measured in this study. Spatial autocorrelation (Moran's I, Geary's C) shows 162-163x speedup. Steps without GPU implementations (spatial_neighbors, nhood_enrichment) remain at 1.0x.

**Figure 9.** Concordance between CPU and GPU spatial analysis pipelines across three Visium platforms. Spatial autocorrelation statistics (Moran's I, Geary's C) show near-perfect agreement (Spearman rho >= 0.9995). SVG Jaccard overlap of the top 50 genes equals 1.0 for all platforms. Cluster concordance (ARI) degrades at HD 2 um resolution (0.080) due to algorithmic differences between cugraph and leidenalg Leiden implementations at high granularity.


# References
