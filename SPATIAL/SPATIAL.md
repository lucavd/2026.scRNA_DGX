# SPATIAL.md — GPU-Accelerated Spatial Omics Benchmark (Phase 2)

> **STATUS**: Local benchmarks DONE (Visium + Visium HD 8µm + 2µm). DGX full-scale runs pending.

## Goal

Extend the GPU vs CPU benchmark to spatial transcriptomics, using the same DGX H100 infrastructure and container. This adds a second "arm" to the study, making the paper a comprehensive GPU benchmark for both single-cell AND spatial omics — directly matching the CIBB 2026 special session scope.

The spatial benchmark answers:
1. **Speed**: GPU vs CPU speedup for spatial-specific analysis steps
2. **Scalability**: How do spatial pipelines scale with number of spots/bins?
3. **Concordance**: Do CPU and GPU produce the same spatially variable genes and spatial statistics?
4. **Platform comparison**: How do results differ across Visium vs Visium HD resolutions?

---

## Progress

### Completed (local, RTX 4090)

- [x] Dockerfile updated with squidpy 1.8.1, spatialdata 0.7.2, spatialdata-io
- [x] Download script: Visium v1 Mouse Brain + Visium HD Mouse Brain (Tiny + full)
- [x] CPU benchmark script (`benchmark_spatial_cpu.py`)
- [x] GPU benchmark script (`benchmark_spatial_gpu.py`)
- [x] Concordance script (`compare_spatial_results.py`)
- [x] Container pushed to Docker Hub, pulled on DGX

### Local Benchmark Results

#### Visium v1 (2,695 spots × 32,285 genes)

| Step | CPU | GPU | Speedup |
|------|-----|-----|---------|
| normalization | 2.57s | 0.09s | **29×** |
| expression_neighbors | 9.40s | 2.34s | **4.0×** |
| umap | 2.56s | 0.17s | **15×** |
| spatial_autocorr_moran | 1.63s | 3.56s | 0.46× (JIT overhead) |
| spatial_autocorr_geary | 1.67s | 0.24s | **7.0×** |
| co_occurrence | 8.23s | 1.57s | **5.2×** |
| **TOTAL** | **39.7s** | **24.9s** | **1.6×** |

Concordance: Moran's I ρ = 1.0, Geary's C ρ = 1.0, Cluster ARI = 0.856

#### Visium HD 8µm (393,543 bins → 139,927 after QC)

| Step | CPU | GPU | Speedup |
|------|-----|-----|---------|
| pca | 22.3s | 0.74s | **30×** |
| expression_neighbors | 43.4s | 2.74s | **16×** |
| umap | 58.2s | 0.28s | **208×** |
| spatial_neighbors | 20.6s | 20.3s | ~1× (CPU-only) |
| spatial_autocorr_moran | 12.5s | 3.6s | **3.5×** |
| spatial_autocorr_geary | 12.5s | 0.56s | **22×** |
| co_occurrence | 20.3s | 1.59s | **13×** |
| **TOTAL** | **268s** | **97s** | **2.8×** |

Concordance: Moran's I ρ = 1.0, Geary's C ρ = 1.0, SVG Jaccard (top50) = 1.0, Cluster ARI = 0.627

#### Visium HD 2µm (6.3M bins → 487k after subsample + QC)

| Step | CPU | GPU | Speedup |
|------|-----|-----|---------|
| pca | 31.2s | 1.0s | **31×** |
| expression_neighbors | 81.0s | 5.6s | **14.5×** |
| umap | **1176s** | **10.5s** | **112×** |
| spatial_neighbors | 77.9s | 75.9s | ~1× (CPU-only) |
| spatial_autocorr_moran | 45.4s | 4.3s | **10.6×** |
| spatial_autocorr_geary | 45.7s | 0.6s | **72×** |
| **TOTAL** | **1504s** | **134s** | **11.2×** |

Concordance: Moran's I ρ = 1.0, Geary's C ρ = 0.9999, SVG Jaccard (top50) = 1.0

### Key Findings (local)

1. **Speedup scales with data size**: 1.6× (3k spots) → 2.8× (140k spots) → 11.2× (487k spots)
2. **UMAP is the biggest beneficiary**: 112× at 487k spots (20 min → 10 sec)
3. **Spatial autocorrelation**: 10-72× GPU speedup (after JIT warmup)
4. **Bottlenecks**: `spatial_neighbors` (CPU-only in Squidpy, ~76s) and `ligrec` (CPU-only)
5. **Concordance is excellent**: Moran's I and Geary's C are numerically identical (ρ ≥ 0.9999)
6. **Cluster concordance lower than scRNA-seq**: ARI 0.63-0.86 (vs 0.96 for scRNA-seq) — expected, spatial data is sparser

### RESOLVED: Driver incompatibility (discovered 2026-03-25, fixed 2026-03-26)

**DGX driver 535.183.01 (CUDA 12.2) is incompatible with RAPIDS 26.02 (CUDA 12.8+).**

Root cause: RAPIDS 26.02 / RMM 26.02 requires driver 570+ for advanced CUDA VMM APIs. Driver 535 only supports CUDA 12.2.

**Fix: Rebuild container on RAPIDS 24.06 (CUDA 12.2).** Verified with minimal test container (`Dockerfile.test`):
- CuPy 13.2.0: PASS
- RMM 24.06: PASS (pool init + allocation)
- rapids-singlecell (anndata_to_GPU + normalize + log1p): PASS

Next step: rebuild full container with all spatial dependencies on `rapidsai/base:24.06-cuda12.2-py3.11`.

### Pending (DGX) — blocked until driver/container fix

- [ ] Smoke test GPU spatial on DGX (Visium v1, 1 repeat)
- [ ] Full-scale Visium HD 2µm (6.3M bins, no subsampling) — needs DGX RAM
- [ ] Multi-GPU scaling (1/2/4/8 GPU on Visium HD)
- [ ] 5 repeats for all configurations
- [ ] Analysis + figures for spatial section

---

## Spatial Platforms

### Tier 1 (benchmarked)
- **10x Visium v1** — 2,695 spots, 55 µm resolution
- **10x Visium HD** — 393k bins (8µm) / 6.3M bins (2µm)

### Tier 2 (not pursued)
- **10x Xenium** — would need additional data download + different loading logic
- **MERFISH / seqFISH** — similar complexity, deferred

---

## Datasets

### Visium v1 Mouse Brain Sagittal Anterior
- Source: 10x Genomics public datasets
- Files: `filtered_feature_bc_matrix.h5` + `spatial/` folder
- Size: ~2,695 spots × 32,285 genes
- Downloaded via `download_spatial_data.py`

### Visium HD Mouse Brain (CytAssist, FFPE)
- Source: 10x Genomics public datasets
- Files: `binned_outputs/` with square_002um, square_008um, square_016um
- Sizes: 6.3M bins (2µm) / 393k bins (8µm) / 99k bins (16µm) × 19,059 genes
- Feature slice H5 (462 MB) + Binned outputs (4.62 GB)

---

## Pipeline Steps

### Expression steps (shared with scRNA-seq, GPU-accelerated)
1. Data loading (`sc.read_visium` / `sc.read_10x_h5`)
2. QC & filtering (min_genes=200 for Visium, min_genes=1 for Visium HD)
3. Normalization (`normalize_total` + `log1p`)
4. HVG selection (2000 genes)
5. PCA (50 components)
6. Expression neighbors (k=15)
7. Leiden clustering (resolution adaptive: 1.0 for <100k, 0.1 for >100k spots)
8. UMAP

### Spatial steps
9. **Spatial neighbors** — `sq.gr.spatial_neighbors(delaunay=True)` — CPU-only
10. **Moran's I** — `sq.gr.spatial_autocorr(mode="moran")` — GPU via rsc
11. **Geary's C** — `sq.gr.spatial_autocorr(mode="geary")` — GPU via rsc
12. **Co-occurrence** — `sq.gr.co_occurrence()` / `rsc.gr.co_occurrence()` — GPU
13. **Nhood enrichment** — `sq.gr.nhood_enrichment()` — CPU-only
14. **Ligrec** — `sq.gr.ligrec()` — CPU-only (GPU fails on dense matrix)

### Scale-dependent skips
- Co-occurrence / nhood enrichment: SKIP when >500 clusters (O(k²) memory)
- Ligrec: SKIP when >100k spots (too slow, not informative)

---

## Software Stack

### In container (lucavd/sc-benchmark:latest)
- `scanpy` — CPU expression analysis
- `rapids-singlecell` — GPU expression analysis + spatial autocorrelation
- `squidpy 1.8.1` — CPU spatial analysis (baseline)
- `spatialdata 0.7.2` — spatial data format
- `spatialdata-io` — data loading (Visium HD)

### GPU support matrix

| Function | CPU (Squidpy) | GPU (rsc) | Status |
|----------|--------------|-----------|--------|
| spatial_neighbors | ✅ | ❌ | CPU-only (Squidpy) |
| spatial_autocorr (Moran/Geary) | ✅ | ✅ | GPU 10-72× faster |
| co_occurrence | ✅ | ✅ | GPU 5-13× faster |
| nhood_enrichment | ✅ | ❌ | CPU-only |
| ligrec | ✅ | ❌ (bug) | rsc.gr.ligrec fails on dense CuPy matrix |

---

## QC Strategy for Visium HD

Visium HD 2µm bins have very few genes per bin (median ~9). Standard `min_genes=200` filters nearly everything. Strategy:
- **Visium v1**: `min_genes=200` (standard)
- **Visium HD (all bin sizes)**: `min_genes=1` — Space Ranger already filtered on-tissue barcodes

At 2µm, random subsampling destroys spatial contiguity → many disconnected Leiden clusters even at low resolution. This is a known limitation of subsampling spatial data.

---

## Concordance Metrics

- **Moran's I Spearman ρ**: per-gene spatial autocorrelation correlation
- **Geary's C Spearman ρ**: per-gene spatial autocorrelation correlation
- **SVG Jaccard**: overlap of top-N spatially variable genes (N = 50, 100, 200)
- **SVG Jaccard (FDR < 0.05)**: overlap of significant SVGs
- **Cluster ARI/NMI**: expression-based Leiden cluster agreement
- **Co-occurrence Spearman ρ**: correlation of co-occurrence matrices (when same n_clusters)

---

## Project Structure

```
SPATIAL/
├── SPATIAL.md                         # This file
├── scripts/
│   ├── download_spatial_data.py       # Download Visium + Visium HD datasets
│   ├── benchmark_spatial_cpu.py       # CPU spatial pipeline (Scanpy + Squidpy)
│   ├── benchmark_spatial_gpu.py       # GPU spatial pipeline (rsc + Squidpy fallback)
│   └── compare_spatial_results.py     # Concordance analysis
├── data/
│   ├── visium/                        # Visium v1 Mouse Brain
│   │   ├── filtered_feature_bc_matrix.h5
│   │   └── spatial/
│   └── visium_hd/                     # Visium HD Mouse Brain
│       ├── binned_outputs/
│       │   ├── square_002um/
│       │   ├── square_008um/
│       │   └── square_016um/
│       └── spatial/
└── results/                           # Benchmark outputs (JSON + CSV)
```

---

## Open Questions (resolved)

- [x] **rapids-singlecell spatial support?** — YES: spatial_autocorr (Moran/Geary) and co_occurrence have GPU acceleration. spatial_neighbors and nhood_enrichment are CPU-only.
- [x] **Squidpy as CPU baseline?** — YES, it's the standard and most comprehensive spatial analysis library.
- [x] **Visium HD format compatibility?** — YES, `sc.read_10x_h5()` + parquet spatial coords work well. No need for spatialdata-io for loading.
- [x] **Image-based analysis?** — NOT included. Would add complexity without clear GPU benchmark value.
- [x] **Deconvolution?** — NOT included. Different algorithm class (probabilistic model), not comparable to the preprocessing pipeline benchmark.

## Open Questions (remaining)

- [ ] Xenium: worth adding? Different data structure (molecules, not spots), would need separate loading logic.
- [ ] On DGX, can we run 6.3M bins without subsampling? Estimated ~60 GB RAM for PCA.
- [ ] Multi-GPU for spatial: does Dask-CUDA help for spatial_autocorr on 6M bins?
