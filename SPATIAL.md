# SPATIAL.md — GPU-Accelerated Spatial Omics Benchmark (Phase 2)

> **STATUS**: Not started. Begin only after the scRNA-seq part of the manuscript is complete.
> **Dependency**: Steps 1–10 of the scRNA-seq benchmark + submitted manuscript.

## Goal

Extend the GPU vs CPU benchmark to spatial transcriptomics, using the same DGX H100 infrastructure and container. This adds a second "arm" to the study, making the paper a comprehensive GPU benchmark for both single-cell AND spatial omics — directly matching the CIBB 2026 special session scope.

The spatial benchmark answers:
1. **Speed**: GPU vs CPU speedup for spatial-specific analysis steps
2. **Scalability**: How do spatial pipelines scale with number of spots/cells and with tissue area (high-resolution platforms)?
3. **Concordance**: Do CPU and GPU produce the same spatial patterns, domains, and spatially variable genes?
4. **Platform comparison**: How do results differ across spatial platforms (spot-based vs molecule-based)?

---

## Spatial Platforms to Benchmark

### Tier 1 (must-have): Spot-based
- **10x Visium** — ~5,000 spots, 55 µm resolution, well-established
- **10x Visium HD** — ~500,000+ bins at 8 µm, much larger, tests scalability

### Tier 2 (nice-to-have): Molecule-based
- **10x Xenium** — subcellular resolution, millions of transcripts, ~100k cells
- **MERFISH / seqFISH** — similar to Xenium, alternative platform

### Tier 3 (stretch goal):
- **Slide-seq / HDST** — very high resolution, large datasets

---

## Datasets

All datasets must be publicly available and downloadable programmatically.

### Primary: Mouse Brain (same tissue as scRNA-seq benchmark)
This creates a direct narrative connection: "we benchmarked scRNA-seq on mouse brain, now we benchmark spatial on the same tissue."

| Dataset | Platform | Size | Source |
|---------|----------|------|--------|
| Mouse brain sagittal (anterior) | Visium | ~3,000 spots | 10x Genomics public datasets |
| Mouse brain Visium HD | Visium HD | ~500k bins | 10x Genomics public datasets |
| Mouse brain Xenium | Xenium | ~100k cells | 10x Genomics public datasets |

### Secondary: Human datasets
| Dataset | Platform | Size | Source |
|---------|----------|------|--------|
| Human DLPFC | Visium | ~3,600 spots × 12 samples | spatialLIBD (Maynard et al. 2021) |
| Human breast cancer | Xenium | ~100k+ cells | 10x Genomics public datasets |

### Data Download
- 10x public datasets: direct download URLs from 10x Genomics website
- spatialLIBD: via `spatialLIBD` R/Python package or direct download
- CELLxGENE: some spatial datasets are available via Census API

---

## Pipeline Steps to Benchmark

### Spatial-specific steps (not in scRNA-seq pipeline)

| Step | CPU (Squidpy) | GPU (rapids-singlecell / cuSpatial) | Notes |
|------|--------------|--------------------------------------|-------|
| Spatial neighbors | `sq.gr.spatial_neighbors()` | `rsc.gr.spatial_neighbors()` | Based on coordinates, not expression |
| Spatial autocorrelation | `sq.gr.spatial_autocorr()` (Moran's I) | GPU equivalent | Per-gene spatial statistics |
| Spatially variable genes | `sq.gr.spatial_autocorr()` ranked | GPU equivalent | Key biological output |
| Spatial domains | `sq.gr.leiden()` on spatial graph | GPU leiden on spatial graph | Tissue segmentation |
| Niche/co-occurrence | `sq.gr.co_occurrence()` | GPU equivalent | Cell type spatial patterns |
| Deconvolution | cell2location / RCTD (CPU) | GPU-accelerated alternatives? | Map scRNA-seq → spatial |

### Shared steps (already benchmarked in scRNA-seq)
- QC & filtering
- Normalization
- HVG selection
- PCA
- Clustering (on expression, not spatial)
- DE testing

### Visium HD / Xenium specific
- Binning (HD: aggregate 2 µm bins → 8 µm → 16 µm)
- Transcript-level processing (Xenium: molecule → cell assignment)
- Large image handling

---

## Software Stack

### Existing (already in container)
- `scanpy` — expression analysis
- `rapids-singlecell` — GPU expression analysis

### To add to Dockerfile
- `squidpy` — spatial analysis framework (CPU baseline)
- `spatialdata` — unified spatial data format (AnnData extension)
- `cell2location` or `tangram` — deconvolution (optional, uses PyTorch GPU)

**CHECK**: Does `rapids-singlecell` already support spatial operations? Review docs before adding extra packages.

---

## Experimental Design

### Visium (small, fast iteration)
- CPU (Scanpy + Squidpy) vs GPU (rapids-singlecell) on ~3,000 spots
- All pipeline steps, 5 repeats
- Expected: GPU advantage minimal on small data (like 10k scRNA-seq)

### Visium HD (scalability test)
- ~500,000 bins — similar scale to our scRNA-seq 500k benchmark
- This is where GPU should shine: spatial neighbor computation on 500k points
- Multi-resolution: benchmark at 8 µm, 16 µm, 32 µm bin sizes

### Xenium (molecule-based, large)
- ~100,000 cells with subcellular resolution
- Millions of individual transcripts
- Tests GPU on fundamentally different data structure

### Scaling experiment
- Subsample Visium HD at different resolutions to create size tiers
- Compare: 10k, 50k, 100k, 500k bins
- Same methodology as scRNA-seq subsampling

---

## Concordance Metrics (spatial-specific)

- **SVG overlap**: Jaccard of top-N spatially variable genes (CPU vs GPU)
- **Spatial domain ARI/NMI**: cluster assignments on spatial graph
- **Moran's I correlation**: Spearman correlation of per-gene Moran's I values
- **Spatial neighbor Jaccard**: per-spot overlap of spatial neighbor sets (analogous to kNN Jaccard)

---

## Integration with scRNA-seq Benchmark

The paper narrative:
1. **scRNA-seq benchmark** (current work): established pipelines, well-understood
2. **Spatial omics benchmark** (this phase): emerging pipelines, less benchmarked
3. **Cross-modality**: deconvolution maps scRNA-seq reference → spatial data (both on GPU?)

### Shared infrastructure
- Same DGX H100 node (poddgx02)
- Same container (extended with squidpy/spatialdata)
- Same output format (JSON + CSV)
- Same figure generation pipeline

---

## Estimated Timeline

1. Add squidpy/spatialdata to Dockerfile, rebuild container (~1 day)
2. Download spatial datasets (~1 day)
3. CPU spatial benchmark script (~2 days)
4. GPU spatial benchmark script (~2 days)
5. Concordance script for spatial metrics (~1 day)
6. Run on DGX (~1-2 days)
7. Analysis + figures (~1 day)
8. Integrate into manuscript (~2-3 days)

**Total: ~10-12 working days**

---

## Open Questions

- [ ] Does rapids-singlecell have native spatial support, or do we need a separate GPU spatial library?
- [ ] Is Squidpy the right CPU baseline, or should we use SpatialDE / SPARK for SVG detection?
- [ ] Should we include image-based analysis (H&E alignment for Visium)?
- [ ] How to handle deconvolution benchmark — it's a different class of algorithm (probabilistic model vs linear algebra)
- [ ] Visium HD data format: is it compatible with standard AnnData workflows, or needs special handling?
