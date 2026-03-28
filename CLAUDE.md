# CLAUDE.md — GPU vs CPU Single-Cell RNA-seq Benchmark on DGX H100

## Project Goal

Build and run a reproducible benchmark study comparing GPU-accelerated vs CPU-based single-cell RNA-seq analysis pipelines on an NVIDIA DGX H100 node (8×H100 GPUs). The study targets a 4–6 page short paper submission to CIBB 2026 (deadline: May 3, 2026), special session "GPU-Accelerated Analysis of Single-Cell and Spatial Omics".

The benchmark answers four questions simultaneously:
1. **Speed**: How much faster is GPU vs CPU for each pipeline step?
2. **Numerical reproducibility**: Do CPU and GPU produce identical results, or do floating-point differences cause divergence?
3. **Scalability**: How do pipelines degrade as cell count grows? Where does CPU break? Where does single-GPU break? How does multi-GPU scale?
4. **Biological concordance**: Do CPU and GPU pipelines find the same cell types, clusters, and differentially expressed genes?

---

## Development Rules (MUST FOLLOW)

### Code Quality
- Every script must be working, tested code. No pseudocode, no "TODO" stubs, no placeholder functions.
- Every script must include docstrings, inline comments for non-obvious logic, and a `--help` CLI interface (use `argparse`).
- Every script must have at least basic tests (use `pytest`). Test with small synthetic data before running on real datasets.
- Use type hints in Python functions.

### Local-First Development
All code is developed and validated LOCALLY before ever touching the DGX. The user's local machine specs:

- **CPU**: 100 cores
- **GPU**: NVIDIA RTX 4090, 24 GB VRAM
- **RAM**: 256 GB
- **OS**: Ubuntu Linux

The local machine can run the full pipeline on small datasets (10k–50k cells) and single-GPU benchmarks. Use this for:
- Dockerfile build and test (`docker run` locally with `--gpus all`)
- All script development and debugging
- Verifying that Scanpy and rapids-singlecell produce outputs correctly
- Testing timing/memory measurement logic
- Generating and inspecting output JSON/CSV format

Only after local tests pass do we deploy to DGX. The DGX is for the full-scale runs (500k–1.3M cells, multi-GPU scaling) that the local machine cannot handle.

### Step-by-Step Workflow (CRITICAL)
The user is NOT a DGX/HPC expert. This is one of the first times using this infrastructure. Proceed one step at a time:

1. Claude Code proposes and implements ONE step (e.g., "build the Dockerfile").
2. The user reviews the code, runs it locally, and reports back.
3. We fix any issues together.
4. The user explicitly approves the step.
5. ONLY THEN do we move to the next step.

**Never skip ahead. Never implement multiple steps at once unless the user asks.** If something fails, we debug it before moving on.

### Suggested Step Sequence

1. **Dockerfile**: Build and test locally with `docker run --gpus all`. ✅ DONE
2. **Data download script**: Download the 1.3M brain dataset, run subsampling. ✅ DONE
3. **CPU benchmark script**: Run Scanpy pipeline on 10k cells locally. ✅ DONE
4. **GPU benchmark script**: Run rapids-singlecell pipeline on 10k cells locally (RTX 4090). ✅ DONE
5. **Concordance script**: Compare CPU vs GPU results from steps 3–4. ✅ DONE
6. **Push to Docker Hub, pull on DGX as Singularity**: Smoke test (10k cells, 1 GPU). ✅ DONE
7. **SLURM jobs for full-scale CPU benchmark**: All dataset sizes × 5 repeats. ✅ DONE
8. **SLURM jobs for GPU scaling**: 1/2/4/8 GPU on all datasets × 5 repeats. ✅ DONE (note: 8-GPU Dask worker count reporting bug FIXED — all runs used 8 workers, only the readiness check was wrong)
9. **Analysis and figures**: 6 publication-ready figures + summary table. ✅ DONE (locally)
10. **Max-power stress test**: ✅ DONE — **11.9M cells** is the DGX limit (8×H100, 2 TB RAM). Bottleneck is CPU RAM (535/2048 GB at 11.9M), not GPU VRAM (49/640 GB = 7.6%). Optimizations: scatter covariance PCA, lean GPU transfer, RMM pool 2GB. Binary search: 12M FAIL (leiden OOM), 13.7M FAIL (scale OOM). KMeans GPU tested: same limit (CPU preprocessing, not clustering). Sparse-scatter tested at 14M: HVG selection OOM (scanpy preprocessing is the bottleneck).
10b. **DE benchmark at scale**: ✅ DONE — 7 tests on 3.4M cells × 41k genes × 81 clusters. Pseudo-bulk fastest (128s, 44× vs CPU t-test). Wilcoxon GPU (826s) beats t-test GPU (1656s). Multi-GPU ≈ single-GPU for DE (I/O bound).
10c. **Chunked preprocessing stress test**: ✅ DONE — Inspired by ScaleSC (Hu et al. 2025), implemented chunked HVG selection and batch-wise PCA covariance accumulation to bypass dense matrix creation. 12M cells PASS (862 GB RAM, 10 GB VRAM, 9363s). 15M cells FAIL (OOM during CSR→CSC conversion at 1071 GB). Root cause: `adata.raw = adata.copy()` doubled RAM + full CSC conversion. Fixes applied (reference-only raw, batch column extraction) but not re-tested — diminishing returns (12M vs 11.9M = marginal improvement). VRAM dropped from 49 GB (Step 10) to 10 GB (1.5%) thanks to chunked GPU operations.
11. **Manuscript (scRNA-seq part)**: Write the single-cell sections of the full-length paper. ⏳ TODO
12. **Spatial omics benchmark**: ✅ DONE (locally) — Visium v1, HD 8um, HD 2um benchmarked on RTX 4090 (5 repeats each). See `SPATIAL/SPATIAL.md`. Key results: 1.7x speedup (Visium v1, 3k spots), **51.6x** (HD 8um, 393k bins), **10.8x** (HD 2um, 389k bins). co_occurrence **3,272x** at HD 8um. Spatial autocorrelation concordance: Moran/Geary rho >= 0.9995, SVG Jaccard top50 = 1.0. Cluster ARI degrades at 2um (0.08) due to cugraph vs leidenalg algorithmic differences. DGX full-scale runs blocked by driver 535 incompatibility.
13. **Manuscript (spatial part + finalize)**: Add spatial sections, condense to 4–5 pages for CIBB 2026. ⏳ TODO
14. ~~**GPU-native scRNA tool**~~: CANCELLED — rapids-singlecell v0.14+ already provides GPU-native preprocessing (QC, HVG, normalize on sparse CuPy) AND GPU-native DE (Wilcoxon with custom CUDA kernels, t-test, wilcoxon_binned for Dask). Our v0.14.1 container already uses these. No gap to fill.

### Local Machine Setup
- **Docker**: Must be installed with NVIDIA Container Toolkit (`nvidia-docker`) for GPU passthrough.
- **Test command**: `docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi` should show the RTX 4090.
- **Working directory**: The user will clone/create the project repo locally. All development happens there.

---

## HPC Infrastructure: UPSCALE / CONVECS @ UniPD

### Hardware (per DGX H100 node)
- **GPUs**: 8× NVIDIA H100 SXM, 80 GB HBM3 each, 640 GB total GPU memory, NVLink 4.0 interconnect
- **CPUs**: Dual Intel Xeon Platinum 8480C, 112 cores total (100 usable per job), 2.0 GHz base / 3.8 GHz boost
- **RAM**: 2 TB DDR5 system memory
- **Storage**: 32 TB NVMe RAID0 per node; NFS shared storage available
- **Cluster**: 5 DGX H100 nodes total (BasePOD configuration)

### Access
- **Login node**: `logindgx.hpc.ict.unipd.it` (SSH from UNIPD network)
- **Username**: `u0044`
- **Login shell landing**: When you SSH in, you land on the login node. This is NOT where your 500 GB storage lives.
- **Your data home**: `/mnt/home/u0044` (500 GB) — this is mounted on compute nodes. All datasets, containers, results go here.
- **Project storage**: `/mnt/projects/dctv/` (check exact path with `ls /mnt/projects/`)
- **Admin portal**: https://upscaleadmin.hpc.ict.unipd.it (SSO login for account info)

**CRITICAL PATH DISTINCTION**: The path where you land when you SSH in and `/mnt/home/u0044` may NOT be the same. Your 500 GB allocation is at `/mnt/home/u0044`. Always use this full path when referencing data directories. Verify with:
```bash
df -h /mnt/home/u0044
ls -la /mnt/home/u0044
```

### SLURM Configuration
- **Partition**: `dgx12cluster`
- **Account**: `dctv_dgx`
- **Job scheduler**: SLURM with Singularity containers
- **Module system**: lmod (minimal — Singularity, HPC SDK, OpenMPI)
- **Our node**: `poddgx02` — this is the node assigned to our group. Jobs should preferentially run here.

### Node Affinity (for future studies)

Our group's primary node is **poddgx02**. SLURM does NOT support soft node preferences — `--nodelist` is a hard constraint. Options:
- `#SBATCH --nodelist=poddgx02` — run ONLY on poddgx02; if busy, job waits in queue
- `#SBATCH --nodelist=poddgx02,poddgx01` — accept either node, no preference order guaranteed
- No `--nodelist` — SLURM picks the best available node across the cluster (5 DGX nodes total)

**For this project all jobs MUST use `--nodelist=poddgx02`** to pin to our node. Only remove if the user explicitly asks.

### SLURM Essentials

Check cluster status:
```bash
sinfo                          # partitions and node states
squeue                         # all running/queued jobs
squeue -u u0044                # your jobs only
sacct -u u0044                 # job history with exit codes
```

Submit a job:
```bash
sbatch submit.sh
```

Cancel a job:
```bash
scancel <JOBID>
```

Every job script MUST include:
```bash
#SBATCH --partition=dgx12cluster
#SBATCH --account=dctv_dgx
#SBATCH --export=NONE
#SBATCH --chdir=/home/u0044
#SBATCH --output=/home/u0044/sc-gpu-benchmark/logs/slurm-%x_%j.out
#SBATCH --error=/home/u0044/sc-gpu-benchmark/logs/slurm-%x_%j.err
#SBATCH --nodelist=poddgx02
```

And MUST follow this boilerplate (see `slurm/gpu_8.sh` as reference):
```bash
# Load required modules
module load go/1.22.7
module load singularity/4.2.0
module load slurm/slurm/23.02.7

# Detect workdir (path differs between login and compute nodes)
if [ -d /mnt/home/u0044/sc-gpu-benchmark ]; then
    WORKDIR=/mnt/home/u0044/sc-gpu-benchmark
elif [ -d /home/u0044/sc-gpu-benchmark ]; then
    WORKDIR=/home/u0044/sc-gpu-benchmark
else
    echo "FAILED: sc-gpu-benchmark not found"; exit 1
fi

CONTAINER=${WORKDIR}/sc-benchmark.sif
SINGULARITY=/cm/shared/apps/singularity/4.2.0/bin/singularity
BIND_ARGS=(-B /home/u0044:/home/u0044)
[ -d /mnt/home/u0044 ] && BIND_ARGS+=(-B /mnt/home/u0044:/mnt/home/u0044)

run_in_container() {
    "${SINGULARITY}" exec --nv "${BIND_ARGS[@]}" "${CONTAINER}" "$@"
}
```

**NOTE**: `--mail-type ALL` does NOT work — the cluster has no mail service configured. Monitor jobs with `squeue -u u0044` and `sacct`.

### Container Workflow (CRITICAL)

The DGX nodes do NOT have user-installable software. Everything runs inside Singularity containers. The workflow is:

1. Build a Docker image locally (or use a Dockerfile)
2. Push to Docker Hub
3. On the login node, pull and convert to Singularity .sif format:
   ```bash
   cd /mnt/home/u0044/sc-gpu-benchmark
   singularity pull sc-benchmark.sif docker://lucavd/sc-benchmark:latest
   # After successful pull, clean cache to reclaim disk space (conversion uses ~2x space):
   singularity cache clean
   ```
4. Run via SLURM with Singularity:
   ```bash
   srun singularity exec --nv sc-benchmark.sif python script.py
   ```

The `--nv` flag is REQUIRED to enable GPU access inside the container.

**DATA ACCESS FROM INSIDE THE CONTAINER**: The Singularity container CANNOT see the host filesystem unless you explicitly bind-mount paths with `-B`. You MUST bind-mount your data directory:

```bash
singularity exec --nv \
  -B /mnt/home/u0044:/mnt/home/u0044 \
  sc-benchmark.sif python script.py --data-dir /mnt/home/u0044/sc-gpu-benchmark/data
```

This makes `/mnt/home/u0044` visible inside the container at the same path. All scripts should reference data using absolute paths under `/mnt/home/u0044/`.

**DO NOT assume any path is automatically visible inside the container.** If a script fails with "file not found", the most likely cause is a missing `-B` bind mount.


### Reference Repository

The team already has a working container + SLURM template at:
https://github.com/UBESP-DCTV/laims-dgx

Key files in that repo:
- `Dockerfile` — base image `nvidia/tensorflow:25.01-tf2-py3` with R + tidyverse (we need a DIFFERENT Dockerfile for this project)
- `Makefile` — targets: `make build`, `make run`, `make push`, `make pull-singularity`, `make run-singularity`
- `submit.sh` — SLURM submission script template
- `run.R` — example R training script (we will use Python instead)

Adapt the Makefile and submit.sh pattern for this project. Do NOT use the R/TensorFlow Dockerfile.

---

## Software Stack

### Dockerfile

Create a Dockerfile based on the NVIDIA RAPIDS base container. The image must include:

**Base image**: `nvcr.io/nvidia/rapidsai/base:25.02-cuda12.8-py3.12` (or latest available stable tag — check https://catalog.ngc.nvidia.com/orgs/nvidia/teams/rapidsai/containers/base for current tags)

**If the RAPIDS base image is not available or has issues**, fall back to:
`nvcr.io/nvidia/cuda:12.4.0-runtime-ubuntu22.04` and install conda/mamba + RAPIDS from conda-forge.

**Required Python packages** (install via pip or conda inside the container):
- `scanpy` — CPU-based single-cell analysis (the baseline)
- `rapids-singlecell` (or `rapids-singlecell-cu12`) — GPU-accelerated drop-in replacement for Scanpy
- `anndata` — data format
- `scvi-tools` — variational inference models (uses PyTorch, runs on GPU)
- `cellxgene-census` — programmatic dataset download from CZ CELLxGENE
- `tiledbsoma` — dependency for cellxgene-census
- `scikit-learn` — for ARI, NMI metrics
- `scipy` — for statistical comparisons
- `pandas`, `numpy`, `matplotlib`, `seaborn` — standard data science
- `psutil`, `pynvml` (or `nvidia-ml-py`) — for memory monitoring
- `h5py` — for reading 10x HDF5 files
- `leidenalg`, `igraph` — for Leiden clustering (CPU version)
- `dask`, `dask-cuda` — for multi-GPU / out-of-core experiments

**IMPORTANT**: `rapids-singlecell` precompiled wheels are available as `rapids-singlecell-cu12` on PyPI. If installing via pip, use:
```
pip install rapids-singlecell-cu12
```
If inside a RAPIDS conda environment, just `pip install rapids-singlecell`.

### Docker build & push (local machine)

```bash
docker build -t lucavd/sc-benchmark:latest .
docker push lucavd/sc-benchmark:latest
```

The Docker Hub username is `lucavd`.

### Singularity conversion (on login node)

```bash
singularity pull sc-benchmark.sif docker://lucavd/sc-benchmark:latest
```

This creates a single `.sif` file (~10-20 GB).

**CRITICAL: Singularity conversion disk space**. When converting Docker → Singularity, the system temporarily stores BOTH the Docker layers AND the resulting .sif file, so disk usage is roughly 2× the final container size. With 500 GB home:
- Keep the container image lean (target < 200 GB to be safe, realistically 15-25 GB)
- After conversion is complete, clean up temporary Docker/Singularity cache:
  ```bash
  # Clean up singularity cache after pull
  singularity cache clean
  # If any docker temp files remain
  rm -rf /tmp/singularity-*
  ```
- Monitor disk usage: `du -sh /mnt/home/u0044/`

---

## Datasets

All datasets must be downloaded PROGRAMMATICALLY inside a script. No manual downloads.

### Strategy: One large dataset, subsample to create size tiers

Use a single large dataset and subsample to create consistent benchmarking tiers. This is methodologically cleaner than using different datasets because the biology stays constant.

### Primary Dataset: 10x Genomics 1.3M Mouse Brain Cells

Pre-processed h5ad file available from NVIDIA's RAPIDS examples S3 bucket:
```bash
wget https://rapids-single-cell-examples.s3.us-east-2.amazonaws.com/1M_brain_cells_10X.sparse.h5ad
```
- ~1.3 million cells, mouse brain (E18)
- Already in AnnData-compatible h5ad format (sparse matrix)
- File size: ~5 GB
- This is the canonical large-scale single-cell benchmark dataset

### Secondary Dataset: Human Lung Cell Atlas (~580k cells)

Pre-processed h5ad file:
```bash
wget https://rapids-single-cell-examples.s3.us-east-2.amazonaws.com/krasnow_hlca_10x.sparse.h5ad
```
- ~580,000 cells, human lung
- Good for mid-range benchmarking

### Alternative: CZ CELLxGENE Census API (programmatic)

If the above URLs are not reachable from the DGX network (check allowed domains!), use the CELLxGENE Census Python API to fetch data:

```python
import cellxgene_census

with cellxgene_census.open_soma() as census:
    adata = cellxgene_census.get_anndata(
        census=census,
        organism="Mus musculus",
        obs_value_filter="tissue_general == 'brain' and is_primary_data == True",
        column_names={"obs": ["cell_type", "assay", "tissue", "disease"]},
    )
```

**IMPORTANT**: CELLxGENE downloads can be very large and require significant RAM. If network restrictions on the DGX prevent external downloads, prepare datasets locally and scp them to the project directory.

### Subsampling Tiers

From the 1.3M dataset, create reproducible subsamples:
- **10k cells** — small baseline, fast iteration
- **50k cells** — medium
- **100k cells** — medium-large
- **500k cells** — large
- **1.3M cells** — full dataset (CPU may struggle here)

Use a fixed random seed (42) for all subsampling to ensure reproducibility.

```python
import numpy as np
import scanpy as sc

adata = sc.read_h5ad("1M_brain_cells_10X.sparse.h5ad")

for n_cells in [10000, 50000, 100000, 500000]:
    np.random.seed(42)
    idx = np.random.choice(adata.n_obs, size=n_cells, replace=False)
    subset = adata[sorted(idx)].copy()
    subset.write_h5ad(f"brain_{n_cells}.h5ad")
```

### Data Download Script

Create a script `scripts/download_data.sh` (or `.py`) that:
1. Creates a `data/` directory in the project space
2. Downloads all datasets with wget (or Python requests)
3. Runs the subsampling script
4. Verifies file integrity (file sizes, cell counts)

This can be run as a SLURM job on the login node or as a CPU-only job:
```bash
#SBATCH --partition dgx12cluster
#SBATCH --account dctv_dgx
#SBATCH --ntasks 1
#SBATCH --cpus-per-task 4
#SBATCH --mem 256G
#SBATCH --time 02:00:00
#SBATCH --job-name download_data
```

NOTE: the download job needs significant RAM (256G+) for loading and subsampling the 1.3M cell dataset.

---

## Experimental Design

### Pipelines to Compare

| Pipeline | Backend | Library | Notes |
|----------|---------|---------|-------|
| CPU-Scanpy | CPU only | `scanpy` | Baseline; uses all available CPU cores via NumPy/SciPy threading |
| GPU-RAPIDS | Single GPU | `rapids_singlecell` | Drop-in Scanpy replacement on GPU |
| GPU-RAPIDS-multiGPU | 1/2/4/8 GPUs | `rapids_singlecell` + `dask_cuda` | Multi-GPU scaling via Dask |

### Pipeline Steps to Profile

Each step must be timed independently using `time.perf_counter()` (wall clock). Memory (RAM and VRAM) must be logged before and after each step.

1. **Data loading**: `sc.read_h5ad()` / `rsc.get.anndata_to_GPU()`
2. **QC & filtering**: `sc.pp.filter_cells()`, `sc.pp.filter_genes()`, calculate QC metrics
3. **Normalization**: `sc.pp.normalize_total()`, `sc.pp.log1p()`
4. **HVG selection**: `sc.pp.highly_variable_genes()`
5. **PCA**: `sc.pp.pca()` (50 components)
6. **Neighbor graph**: `sc.pp.neighbors()`
7. **Clustering**: `sc.tl.leiden()` (multiple resolutions: 0.5, 1.0, 1.5)
8. **UMAP**: `sc.tl.umap()`
9. **Differential expression**: `sc.tl.rank_genes_groups()` (Wilcoxon test)

For GPU pipeline, the equivalent calls are:
```python
import rapids_singlecell as rsc

rsc.get.anndata_to_GPU(adata)  # transfer to GPU
rsc.pp.filter_cells(adata, ...)
rsc.pp.filter_genes(adata, ...)
rsc.pp.normalize_total(adata)
rsc.pp.log1p(adata)
rsc.pp.highly_variable_genes(adata)
rsc.pp.pca(adata)
rsc.pp.neighbors(adata)
rsc.tl.leiden(adata)
rsc.tl.umap(adata)
rsc.tl.rank_genes_groups(adata)
rsc.get.anndata_to_CPU(adata)  # transfer back for saving/comparison
```

### Metrics to Collect

For each (pipeline × dataset_size × n_gpu) combination:

**Performance metrics**:
- Wall clock time per step (seconds)
- Total pipeline time (seconds)
- Peak CPU RAM usage (GB) — use `psutil.Process().memory_info().rss`
- Peak GPU VRAM usage (GB) — use `pynvml` or `nvidia-smi`

**Concordance metrics** (comparing GPU results to CPU results):
- Adjusted Rand Index (ARI) between CPU and GPU cluster assignments
- Normalized Mutual Information (NMI) between cluster assignments
- Jaccard index of top-N HVGs (N = 2000)
- Spearman correlation of PCA loadings (first 10 PCs)
- Spearman correlation of DE log-fold-changes (top 100 genes per cluster)
- UMAP Procrustes distance (after alignment)

**Stability metrics** (run each configuration 5 times with different seeds):
- Coefficient of variation of cluster assignments (ARI across runs)
- Standard deviation of timing measurements

### GPU Scaling Experiment

Test with 1, 2, 4, and 8 GPUs on the 500k and 1.3M datasets.

For multi-GPU with rapids-singlecell + Dask:
```python
from dask_cuda import LocalCUDACluster
from dask.distributed import Client

cluster = LocalCUDACluster(
    CUDA_VISIBLE_DEVICES="0,1,2,3",  # adjust for n_gpus
    rmm_pool_size="10GB",
    rmm_maximum_pool_size="70GB",
)
client = Client(cluster)
```

SLURM `--gres=gpu:N` controls how many GPUs are visible. Create separate submit scripts for each GPU count.

**KNOWN ISSUE (FIXED) — Dask-CUDA worker count reporting**: `client.scheduler_info()["workers"]` returned only 5 out of 8 workers, but all 8 were actually running and used in computation. Root cause: stale/incomplete client-side cache — a **reporting bug only**, not an execution bug. **Fix**: replaced `client.scheduler_info()["workers"]` with `client.run_on_scheduler()` that reads worker state directly from the scheduler, filtering only `Status.running` workers. Applied to `benchmark_maxpower.py` and `benchmark_multigpu.py`. SLURM 8-GPU scripts also updated to `--cpus-per-task=200` (from 100). **All Step 8 "8 GPU" benchmarks correctly used 8 workers** — only the readiness check was wrong.

---

## Project Structure

```
sc-gpu-benchmark/
├── CLAUDE.md                 # This file
├── Dockerfile                # Container definition
├── Makefile                  # Build, push, pull, run targets
├── README.md                 # Project documentation
├── scripts/
│   ├── download_data.py      # Download + subsample datasets
│   ├── benchmark_cpu.py      # CPU-only Scanpy pipeline
│   ├── benchmark_gpu.py      # Single-GPU RAPIDS pipeline
│   ├── benchmark_multigpu.py # Multi-GPU RAPIDS + Dask pipeline
│   ├── benchmark_maxpower.py         # Max-power stress test (find DGX cell limit)
│   ├── benchmark_maxpower_chunked.py # Chunked preprocessing stress test (Step 10c)
│   ├── compare_results.py            # Concordance + stability analysis
│   └── generate_figures.py           # Publication-ready plots
├── slurm/
│   ├── download.sh                   # SLURM job: data download (1.3M)
│   ├── download_full.sh              # SLURM job: download full ~3.6M mouse brain
│   ├── cpu_benchmark.sh              # SLURM job: CPU benchmarks
│   ├── gpu_1.sh                      # SLURM job: 1 GPU
│   ├── gpu_2.sh                      # SLURM job: 2 GPUs
│   ├── gpu_4.sh                      # SLURM job: 4 GPUs
│   ├── gpu_8.sh                      # SLURM job: 8 GPUs
│   ├── maxpower.sh                   # SLURM job: max-power stress test (8 GPU, --find-limit)
│   ├── maxpower_chunked.sh           # SLURM job: chunked stress test (Step 10c)
│   └── maxpower_chunked_single.sh    # SLURM job: single-target chunked test
├── manuscript/
│   └── bibliography/         # BibTeX references for the paper
├── data/                     # Downloaded datasets (in home dir — 500 GB available)
├── results/                  # Benchmark outputs (JSON/CSV)
└── figures/                  # Generated plots (PNG only) + LEGENDS.md + summary_table.csv
```

---

## SLURM Job Templates

### CPU Benchmark Job
```bash
#!/bin/bash
#SBATCH --job-name cpu_bench
#SBATCH --partition dgx12cluster
#SBATCH --account dctv_dgx
#SBATCH --output logs/cpu_%j.out
#SBATCH --error logs/cpu_%j.err
#SBATCH --mail-user luca.vedovelli@unipd.it
#SBATCH --mail-type ALL
#SBATCH --nodes 1
#SBATCH --ntasks 1
#SBATCH --cpus-per-task 100
#SBATCH --mem 1800G
#SBATCH --time 24:00:00
# NOTE: NO --gres=gpu for CPU-only job

cd $SLURM_SUBMIT_DIR

singularity exec \
  -B /mnt/home/u0044:/mnt/home/u0044 \
  sc-benchmark.sif \
  python scripts/benchmark_cpu.py \
    --data-dir /mnt/home/u0044/sc-gpu-benchmark/data \
    --output-dir /mnt/home/u0044/sc-gpu-benchmark/results \
    --n-repeats 5
```

### GPU Benchmark Job (parameterized)
```bash
#!/bin/bash
#SBATCH --job-name gpu_bench_${N_GPUS}
#SBATCH --partition dgx12cluster
#SBATCH --account dctv_dgx
#SBATCH --output logs/gpu${N_GPUS}_%j.out
#SBATCH --error logs/gpu${N_GPUS}_%j.err
#SBATCH --mail-user luca.vedovelli@unipd.it
#SBATCH --mail-type ALL
#SBATCH --nodes 1
#SBATCH --ntasks 1
#SBATCH --cpus-per-task 16
#SBATCH --mem 256G
#SBATCH --gres=gpu:${N_GPUS}
#SBATCH --time 08:00:00

cd $SLURM_SUBMIT_DIR

singularity exec --nv \
  -B /mnt/home/u0044:/mnt/home/u0044 \
  sc-benchmark.sif \
  python scripts/benchmark_gpu.py \
    --data-dir /mnt/home/u0044/sc-gpu-benchmark/data \
    --output-dir /mnt/home/u0044/sc-gpu-benchmark/results \
    --n-gpus ${N_GPUS} \
    --n-repeats 5
```

Since SLURM does not expand `${N_GPUS}` in `#SBATCH` directives, create separate scripts for each GPU count (gpu_1.sh, gpu_2.sh, gpu_4.sh, gpu_8.sh) with the values hardcoded.

---

## Output Format

All benchmark results should be saved as JSON files with the following structure:

```json
{
  "metadata": {
    "pipeline": "cpu_scanpy",
    "n_cells": 100000,
    "n_gpus": 0,
    "n_cpus": 100,
    "ram_total_gb": 2000,
    "repeat_id": 1,
    "random_seed": 42,
    "timestamp": "2026-03-15T10:30:00",
    "software_versions": {
      "scanpy": "1.10.x",
      "rapids_singlecell": "0.x.x",
      "python": "3.12.x"
    }
  },
  "timings": {
    "data_loading": 12.34,
    "qc_filtering": 5.67,
    "normalization": 2.34,
    "hvg_selection": 3.45,
    "pca": 8.90,
    "neighbors": 15.67,
    "leiden_0.5": 4.56,
    "leiden_1.0": 5.67,
    "leiden_1.5": 6.78,
    "umap": 20.12,
    "de_testing": 30.45,
    "total": 115.95
  },
  "memory": {
    "peak_ram_gb": 45.6,
    "peak_vram_gb": 12.3
  },
  "results_summary": {
    "n_cells_after_qc": 98000,
    "n_hvgs": 2000,
    "n_clusters_0.5": 15,
    "n_clusters_1.0": 22,
    "n_clusters_1.5": 30,
    "hvg_list_hash": "sha256:abc123...",
    "cluster_labels_hash": "sha256:def456..."
  }
}
```

Save cluster assignments and HVG lists as separate .csv files for concordance analysis.

---

## Figures for the Paper

Generate the following publication-ready figures:

1. **Speedup heatmap**: Rows = pipeline steps, Columns = dataset sizes. Cell values = GPU speedup factor (GPU time / CPU time). Color-coded.
2. **Scaling plot**: X-axis = number of GPUs (1, 2, 4, 8). Y-axis = total wall time. One line per dataset size. Ideal linear scaling shown as dashed reference.
3. **Concordance bar chart**: ARI, NMI, HVG Jaccard for each dataset size. Should be very high (>0.95) if results are concordant.
4. **Memory profile**: Peak RAM (CPU) vs Peak VRAM (GPU) across dataset sizes. Highlight where CPU runs out of memory.
5. **Step-level timing breakdown**: Stacked bar charts showing time per step for CPU vs GPU at each dataset size.

Use matplotlib with a clean, publication-ready style. Save as both PDF and PNG (300 DPI).

---

## Important Notes and Pitfalls

1. **Network restrictions**: The DGX login node may not have unrestricted internet access. Test `wget` to external URLs first. If blocked, download datasets locally and `scp` them to `/mnt/home/u0044/sc-gpu-benchmark/data/`.

2. **Storage strategy**: Your home `/mnt/home/u0044` has 500 GB. Budget roughly: container .sif ~20 GB, datasets ~10 GB, results ~5 GB, subsamples ~5 GB = ~40 GB used. Plenty of room, but monitor with `du -sh /mnt/home/u0044/sc-gpu-benchmark/`.

3. **Singularity --nv flag**: Always use `--nv` when GPU access is needed. Without it, GPUs are invisible inside the container.

4. **Bind mounts**: The container cannot see the host filesystem unless you explicitly bind-mount paths with `-B`.

5. **SLURM resource requests**: Request only what you need. Over-requesting delays your job AND other users' jobs. The scheduler prioritizes jobs that use resources efficiently.

6. **CPU benchmark fairness**: For the CPU benchmark, request all 100 usable cores and enough RAM. NumPy/SciPy will use threading automatically. Set environment variables if needed:
   ```bash
   export OMP_NUM_THREADS=100
   export MKL_NUM_THREADS=100
   export OPENBLAS_NUM_THREADS=100
   ```

7. **Random seeds**: CRITICAL for reproducibility. Set seeds for NumPy, Python random, and CUDA (if applicable). Document exact seed values. Note that GPU floating-point operations may be non-deterministic even with the same seed — this IS part of the research question.

8. **rapids-singlecell API compatibility**: The API mirrors Scanpy almost exactly. The main difference is the `anndata_to_GPU()` / `anndata_to_CPU()` transfer step. This ensures minimal code differences between CPU and GPU scripts.

9. **Container size and conversion**: The RAPIDS-based container will be ~15-25 GB as .sif. **CRITICAL**: During `singularity pull` (Docker → Singularity conversion), disk usage is roughly 2× because both the Docker cache and the .sif coexist temporarily. So a 20 GB container needs ~40 GB free during conversion. After conversion completes, immediately run `singularity cache clean` to reclaim the Docker cache space. Budget max ~200 GB for the container build+conversion process to be safe.

10. **CUDA version compatibility**: The DGX H100 nodes run CUDA 12.x. Ensure the container's CUDA version is compatible (12.x). Do not use CUDA 11.x containers — H100 requires CUDA 12+.

11. **GPU memory bottleneck at scale (3.4M cells — SOLVED)**: The original pipeline put the entire dense HVG matrix on GPU 0 via `anndata_to_GPU()`. After scale, GPU 0 held ~36 GB (10 GB RMM pool + 27 GB data). PCA tried to allocate ~51 GB for SVD → OOM (87 GB > 80 GB). **Fix**: distributed covariance PCA — scale on CPU, scatter data chunks across all 8 GPUs (~3.2 GB each), compute local covariance contributions (2000×2000 = 16 MB), sum, eigendecompose, project. Reduces per-GPU memory from 36→6.7 GB. Validated at 3.4M cells. See `_distributed_covariance_pca()` in `benchmark_maxpower.py`.

---

## Memory Optimization Strategy (Step 10) — SOLVED

**Goal**: maximize cells × genes on 8×H100 without sacrificing scientific rigor.

**Previous limit**: ~1.7M cells (PCA OOM on GPU 0: scale + SVD exceeded 80 GB).
**Final limit**: **11.9M cells** on 8×H100 (2 TB RAM). Bottleneck is CPU RAM (535/2048 GB at 11.9M), not GPU VRAM (49/640 GB = 7.6%).

### Two pipeline configurations (IMPORTANT for paper)

The project uses TWO pipeline configurations. They produce **scientifically equivalent results** (same HVG, same clusters, same DE) — the only differences are memory layout optimizations.

| Aspect | Standard pipeline (Steps 7–8) | Optimized pipeline (Step 10) |
|--------|-------------------------------|------------------------------|
| Scale | GPU (`rsc.pp.scale`) | CPU (`sc.pp.scale`) |
| PCA | Single-GPU truncated SVD (cuML) | Scatter covariance across 8 GPUs (CuPy `eigh`) |
| GPU transfer | Full `adata.X` to GPU 0 | Lean: only `X_pca` (empty sparse X) |
| RMM pool | 10 GB/GPU | 2 GB/GPU |
| Neighbors/Leiden/UMAP | GPU 0 (full X in memory) | GPU 0 (only X_pca + graph) |
| DE | GPU (`rsc.tl.rank_genes_groups`) | Separate: chunk-GPU or CPU |
| Cell limit | ~1.7M | **11.9M** |
| Used for | Benchmark results (10k–1.3M, 5 repeats) | Stress test (3.4M–11.9M) |

**For the paper**: Steps 7–8 benchmark results (up to 1.3M cells) use the standard pipeline — this is the canonical rapids-singlecell workflow users would run. The optimized pipeline is presented separately as "how far can we push the hardware with memory-aware engineering". No need to re-run Steps 7–8.

**PCA numerical difference**: truncated SVD (standard) vs covariance method `eigh(X.T @ X / (n-1))` (optimized) are mathematically equivalent but differ at ~10⁻⁶ due to floating-point. At 2000 genes × 50 components, this is negligible.

### Root cause
`anndata_to_GPU()` + `rsc.pp.scale()` put the entire dense matrix on GPU 0. PCA via SVD needed ~2× the matrix as workspace → GPU 0 exceeded 80 GB. Other 7 GPUs sat idle.

### Solution: Distributed covariance PCA (validated 2026-03-16)

Implemented in `_distributed_covariance_pca()` in `benchmark_maxpower.py`:

1. **Scale on CPU** — `sc.pp.scale()` on 2 TB RAM (trivial)
2. **Scatter** — split dense matrix into 8 chunks, transfer each to its own GPU (~3.2 GB/GPU)
3. **Local covariance** — each GPU computes `X_i.T @ X_i` (2000×2000 = 16 MB)
4. **Sum + eigendecompose** — on GPU 0 (2000×2000 matrix, sub-second)
5. **Project** — each GPU: `X_i @ eigenvectors` → chunk_rows × 50
6. **Gather** — PCA coordinates to CPU, store in `adata.obsm["X_pca"]`

**Result at 3.4M cells**: each GPU used 6.6–6.8 GB (vs 36 GB on GPU 0 before). PCA completed in ~2s. 73 GB free per GPU.

Mathematically equivalent to standard PCA (covariance method = `eigh(X.T @ X / (n-1))`).

### Test results

| Test | Cells | Result | GPU peak | Notes |
|------|-------|--------|----------|-------|
| RMM 2GB | 2M | PASS | 18.8 GB | PCA only on GPU 0 |
| RMM 2GB | 3.4M | FAIL | 28.8 GB | PCA SVD still too large |
| Scatter (cuml.dask) | 3.4M | FAIL | — | Container linking bug |
| Scatter (covariance) | 3.4M | **PASS** | 6.7 GB | 73 GB free per GPU |

### Lean GPU transfer (validated 2026-03-17)

After PCA, replace `adata.X` (25 GB dense) with empty sparse matrix before `anndata_to_GPU()`. Neighbors only uses `X_pca` (0.6 GB in obsm), not X. Result: GPU 0 drops from ~29 GB to **4.1 GB** for neighbors/leiden/UMAP.

### DE at scale (raw.X = 121 GB sparse)

`adata.raw.X` at 3.4M × 41k genes has 10.8B non-zeros = **121 GB** sparse CSR. Too large for a single GPU (80 GB). Options tested:
- **GPU DE**: FAIL — 121 GB > 80 GB VRAM
- **CPU DE**: works but slow (hours at 3.4M cells with 69 clusters)

Strategy: `--skip-de` flag for binary search (DE is not the GPU bottleneck). Run DE separately on the final successful attempt. DE on CPU with `sc.tl.rank_genes_groups(use_raw=True)`.

### Binary search results (validated 2026-03-20)

| Cells | Tempo | RAM | VRAM (total) | Throughput | Status |
|------:|------:|----:|-------------:|-----------:|--------|
| 3.4M | 18 min | 155 GB | 49 GB | 3,250/s | PASS |
| 6.9M | 35 min | 308 GB | 49 GB | 3,255/s | PASS |
| 10.3M | 73 min | 465 GB | 49 GB | 2,362/s | PASS |
| 11.1M | 94 min | 500 GB | 49 GB | — | PASS |
| 11.5M | 114 min | 517 GB | 49 GB | — | PASS |
| 11.9M | 119 min | 535 GB | 49 GB | — | **PASS (max)** |
| 12.0M | — | — | — | — | FAIL (leiden OOM, signal 9) |
| 13.7M | — | 493+ GB | — | — | FAIL (scale OOM, signal 9) |

### Remaining bottlenecks
- **CPU RAM is the limit**: 535/2048 GB at 11.9M → ~45 GB per million cells. Leiden at 12M pushed past available memory.
- Neighbors on GPU 0: 28.8/80 GB at 12M → still has headroom
- PCA scatter: 11.2 GB/GPU at 12M → still has headroom
- GPU VRAM is NOT the bottleneck: flat at 49 GB (7.6%) from 3.4M to 11.9M
- DE: must run separately (raw.X too large for GPU), see Step 10b

### KMeans GPU as Leiden alternative (tested 2026-03-22)

Tested `cuml.KMeans` (GPU-native) as a replacement for Leiden to bypass the 12M OOM. Result: **same crash at 13.7M** — the OOM happens during CPU preprocessing (scale: sparse→dense conversion), NOT during clustering. KMeans never gets a chance to run. This confirms the bottleneck is CPU RAM during preprocessing, not the clustering algorithm. Leiden's OOM at 12M is a tighter limit only because leiden's internal data structures add ~50 GB on top of the preprocessing cost.

### Sparse-scatter optimization (tested 2026-03-23)

Attempted to bypass the dense matrix bottleneck by fusing scale+scatter: compute mean/std from the sparse matrix on CPU (O(nnz) memory, no dense copy), then each GPU densifies+scales only its chunk (~13 GB per GPU instead of 103 GB on CPU). The dense matrix would NEVER exist on CPU.

**Result**: OOM at 14M cells during **HVG selection** (before our code even runs). RAM was at 629 GB after resize, and `sc.pp.highly_variable_genes()` creates internal temporaries that pushed past the 1800 GB SLURM limit. The bottleneck is **scanpy's preprocessing**, not our GPU pipeline.

**Conclusion for the paper**: The DGX H100 limit of **11.9M cells** is imposed by scanpy's CPU preprocessing memory footprint (~45 GB/million cells), not by GPU capacity. GPU VRAM is used at only 7.6% (49/640 GB). Future work could optimize scanpy's memory usage (chunked QC, out-of-core HVG selection) or use alternative preprocessing frameworks.

### Capacity limit is cells × genes (manuscript point)

The memory limit is **cells × genes**, not cells alone. With 2000 HVGs (standard), the dense matrix is `n_cells × 2000 × 4B`. More HVGs → fewer cells, and vice versa:
- 2000 HVGs: ~11.9M cells (validated)
- 5000 HVGs: estimated ~4M cells
- 1000 HVGs: estimated ~20M cells

This tradeoff MUST be discussed in the manuscript.

**Constraints preserved**: 2000 HVGs, float32, same pipeline steps. All changes are memory layout optimizations → scientifically equivalent results.

---

## Chunked Preprocessing Stress Test (Step 10c)

### Motivation

Inspired by ScaleSC (Hu et al. 2025, Bioinformatics Advances), which claims 10–20M cells on a single A100 via chunked preprocessing. We implemented ScaleSC-style optimizations to see if we could push beyond the 11.9M limit from Step 10.

### Optimizations implemented (in `benchmark_maxpower_chunked.py`)

Three key differences from the Step 10 optimized pipeline:

1. **Chunked HVG selection**: accumulate per-gene mean and variance across 100k-cell batches from the sparse matrix. Never creates the full dense matrix. Uses Seurat v1 method (same as standard pipeline) on accumulated statistics.

2. **Batch-wise column extraction**: instead of converting the entire 15M × 44k sparse matrix to CSC format (~420 GB copy), extract the 2000 HVG columns in row-batches of 100k cells. Each batch is tiny (~3 GB CSC temporary) vs the full ~420 GB.

3. **Fused scale+PCA via chunked covariance**: compute per-gene mean/std from sparse batches (pass 1), then accumulate `X.T @ X` covariance on 8 GPUs from scaled sparse batches (pass 2), eigendecompose (2000×2000), project (pass 3). Identical to Step 10's `_distributed_covariance_pca()` but fed from sparse batches instead of a pre-materialized dense matrix.

### Results

| Cells | Time | RAM | VRAM (total 8 GPU) | Status |
|------:|-----:|----:|-------------------:|--------|
| 12M | 9,363s (156 min) | 862 GB (42%) | 10 GB (1.5%) | **PASS** |
| 15M | — | 1,071 GB (53%) | 4.8 GB | **FAIL** (OOM at CSR→CSC conversion) |

### Comparison with Step 10 at 11.9M cells

| Metric | Step 10 (optimized) | Step 10c (chunked) at 12M |
|:-------|--------------------:|--------------------------:|
| Cell limit | 11.9M | 12M (+0.8%) |
| Peak RAM | 535 GB (26%) | 862 GB (42%) |
| Peak VRAM | 49 GB (7.6%) | 10 GB (1.5%) |
| Time | 119 min | 156 min |

### Root cause of 15M failure

The 15M crash happened during CSR→CSC conversion (full-matrix `tocsc()`). RAM was already at 1,071 GB after HVG selection due to:
- `adata.raw = adata.copy()` duplicating the ~420 GB sparse matrix (fix: use reference instead of copy)
- Full CSC conversion adding another ~420 GB (fix: batch column extraction)

Fixes were implemented but NOT re-tested on DGX — diminishing returns (12M vs 11.9M is marginal, and the 15M failure suggests the next bottleneck would appear around 16–18M anyway due to other Scanpy internals).

### Key finding for the paper

The chunked preprocessing reduced **VRAM from 49 GB to 10 GB** (5× reduction), confirming that GPU memory is not the bottleneck at any scale. However, it did NOT significantly increase the cell limit because **CPU RAM remains the constraint**: Scanpy's sparse matrix + metadata at ~35 GB per million cells (QC metrics, obs DataFrame, raw copy) consumes most of the 2 TB.

### ScaleSC comparison (for Discussion section)

ScaleSC (Hu et al. 2025) claims 10–20M cells on a single A100 (80 GB) by:
- Chunked batch reader (`max_cell_batch=100k`)
- Two-pass PCA (same covariance method as our scatter PCA)
- Custom CUDA kernels for sparse mean/variance
- Seurat v3 HVG (different from our v1)
- No `adata.raw` copy (key difference)

Their claim of 20M cells on 80 GB GPU suggests they also avoid Scanpy's metadata overhead — they use a custom `AnnDataBatchReader` that never holds the full AnnData in memory. Our pipeline keeps the full AnnData on CPU (for compatibility with downstream rapids-singlecell steps), which is why CPU RAM remains the bottleneck.

---

## DE Benchmark at Scale (Step 10b)

### Problem

`adata.raw.X` at 3.4M cells × 41k genes has 10.8B non-zeros = **121 GB** sparse CSR. This exceeds single-GPU VRAM (80 GB), so GPU DE via `rsc.tl.rank_genes_groups()` fails. CPU Wilcoxon works but takes hours at 3.4M cells with 69 Leiden clusters. We need a faster strategy.

### Factorial Experimental Design

Eight combinations testing three axes: **test type** (Wilcoxon vs t-test vs pseudo-bulk) × **GPU strategy** (none / scatter / chunk-and-stream).

| Test | Method | Backend | GPUs | Description |
|------|--------|---------|------|-------------|
| 1 | Wilcoxon | CPU | 0 | Baseline — `sc.tl.rank_genes_groups(method="wilcoxon")` |
| 2 | t-test | CPU | 0 | `sc.tl.rank_genes_groups(method="t-test")` |
| 3 | Pseudo-bulk | CPU | 0 | Aggregate by donor×cluster, Wilcoxon on pseudo-bulk matrix |
| 4 | Wilcoxon | scatter by genes | 8 | Split 41k genes across 8 GPUs (~5k/GPU), run Wilcoxon per GPU |
| 5 | Wilcoxon | chunk-and-stream | 1 | Load gene chunks to GPU, compute, free, next chunk |
| 6 | t-test | scatter by genes | 8 | Same gene scatter, but t-test instead of Wilcoxon |
| 7 | t-test | chunk-and-stream | 1 | Same streaming, but t-test |
| 8 | t-test | scatter + cleanup | 8 | Test 6 + aggressive memory cleanup between chunks |

### Results (validated 2026-03-20, 3.4M cells × 41k genes × 81 clusters)

| Test | Method | Backend | Time | Speedup vs CPU t-test |
|------|--------|---------|-----:|----------------------:|
| ttest_cpu | t-test | CPU | 5,598s (93 min) | 1× (baseline) |
| **pseudobulk** | Wilcoxon | CPU (aggregated) | **128s (2 min)** | **44×** |
| **wilcoxon_scatter** | Wilcoxon | 8 GPU | **826s (14 min)** | **6.8×** |
| wilcoxon_chunk | Wilcoxon | 1 GPU | 831s (14 min) | 6.7× |
| ttest_scatter | t-test | 8 GPU | 1,656s (28 min) | 3.4× |
| ttest_chunk | t-test | 1 GPU | 1,650s (28 min) | 3.4× |
| ttest_scatter_clean | t-test | 8 GPU + cleanup | 1,649s (28 min) | 3.4× |

**Key findings:**
- Pseudo-bulk is fastest AND statistically most correct (avoids pseudoreplication)
- Wilcoxon GPU (826s) beats t-test GPU (1,656s) — ranking is faster than mean+var on sparse data
- Multi-GPU scatter ≈ single-GPU chunk — bottleneck is CSR→dense conversion (I/O), not compute
- Gene chunk size 500 (not 5000) needed to fit on GPU: 500 × 3.4M × 4B = 6.4 GB per chunk

### Key Implementation Notes

- **Gene chunk size**: 500 genes per chunk (5000 caused OOM: 5000 × 3.4M × 4B = 64 GB > 80 GB VRAM)
- **T-test validity at large n**: At 3.4M cells the CLT guarantees normality of means. T-test only needs mean + variance (no ranking), so it is ~10× cheaper than Wilcoxon per gene. Scientifically valid at this sample size. However, GPU Wilcoxon is actually faster due to sparse data handling.
- **Pseudo-bulk**: Aggregate raw counts by (donor_id × cluster), then run DE on the aggregated matrix (~hundreds of samples instead of millions of cells). This is the **statistically correct approach** for multi-donor scRNA-seq — avoids pseudoreplication. Note: clusters with only 1 donor are skipped (8 of 81 clusters in our data).
- **Scatter by genes**: DE tests are independent per gene. Split 41k genes across 8 GPUs in rounds of 8 chunks. Each GPU gets a dense slice of raw.X for its gene subset + the full cluster labels vector.
- **Chunk-and-stream**: Load a chunk of genes (e.g., 500) to GPU, compute test statistics, free GPU memory, load next chunk. Fits on a single GPU regardless of total gene count.
- **CSR → CSC conversion**: `raw.X` is stored as CSR (row-major). Efficient column (gene) slicing requires CSC format. Convert once on CPU before scattering: `raw_csc = adata.raw.X.tocsc()`.
- **Preprocessed data caching**: CPU preprocessing (load + QC + HVG + PCA + neighbors + leiden) takes ~2h at 3.4M. Cached to `data/de_preprocessed_3400000.h5ad` to avoid repeating for each test.
- **Script**: `scripts/test_de_benchmark.py`

### Manuscript Discussion Point (IMPORTANT)

The paper MUST discuss the statistical limitations of cell-level DE at scale:
1. scRNA-seq raw counts follow a negative binomial distribution, not Gaussian
2. After log-normalization the data is continuous but zero-inflated and skewed
3. Wilcoxon is distribution-free (robust); t-test relies on CLT (valid at large n)
4. At 3.4M cells, p-values are meaningless — virtually every gene is "significant". Effect size (logFC) matters more than p-values
5. Pseudo-bulk with proper count models (DESeq2/edgeR) is the gold standard for multi-donor experiments but requires R and doesn't benefit from GPU acceleration
6. The benchmark tests standard scanpy methods because they represent current practice, while acknowledging that pseudo-bulk is statistically superior

---

## Execution Order

Follow the **Suggested Step Sequence** in the "Development Rules" section above. Summary:

**LOCAL PHASE** (steps 1–5): ✅ ALL DONE
1. Dockerfile → build + test locally with RTX 4090
2. Data download + subsampling script → verify locally
3. CPU benchmark script → run on 10k cells locally, check outputs
4. GPU benchmark script → run on 10k cells locally (RTX 4090), check outputs
5. Concordance script → compare CPU vs GPU, verify metrics

**DGX PHASE** (steps 6–10):
6. Push container to Docker Hub, pull on DGX, smoke test ✅ DONE
7. Full-scale CPU benchmarks (all dataset sizes, 5 repeats) ✅ DONE
8. GPU scaling benchmarks (1/2/4/8 GPUs, all sizes, 5 repeats) ✅ DONE
9. Analysis and figure generation ✅ DONE (6 figures + summary table)
10. Max-power stress test ✅ DONE — **11.9M cells** is the DGX limit (8×H100, 2 TB RAM). Bottleneck is CPU RAM (535/2048 GB at 11.9M), not GPU VRAM (49/640 GB = 7.6%). Optimizations: scatter covariance PCA, lean GPU transfer, RMM pool 2GB. Binary search: 12M FAIL (leiden OOM), 13.7M FAIL (scale OOM). KMeans GPU tested: same limit (CPU preprocessing, not clustering). Sparse-scatter tested at 14M: HVG selection OOM (scanpy preprocessing is the bottleneck).
10b. DE benchmark at scale ✅ DONE — 7 tests on 3.4M cells × 41k genes × 81 clusters. Pseudo-bulk fastest (128s, 44× vs CPU t-test). Wilcoxon GPU (826s) beats t-test GPU (1656s). Multi-GPU ≈ single-GPU for DE (I/O bound).
10c. Chunked preprocessing stress test ✅ DONE — ScaleSC-inspired chunked HVG + batch PCA. 12M PASS (862 GB RAM, 10 GB VRAM). 15M FAIL (CSR→CSC OOM). Marginal improvement over Step 10 (12M vs 11.9M). VRAM dropped 5× (49→10 GB). CPU RAM remains the bottleneck.
11. Manuscript — scRNA-seq sections ⏳ TODO
12. Spatial omics benchmark ✅ DONE (locally) — Visium v1 (1.7x), HD 8um (51.6x), HD 2um (10.8x). co_occurrence 3,272x. Moran/Geary rho >= 0.9995. DGX blocked (driver 535).
13. Manuscript — spatial sections + finalize → condense for CIBB 2026
14. ~~GPU-native scRNA tool~~ — CANCELLED (rapids-singlecell v0.14+ already covers this)

**Each step requires user approval before proceeding to the next.**

---

## Manuscript Writing Workflow

### Target Venue
- **CIBB 2026** — Special session: "GPU-Accelerated Analysis of Single-Cell and Spatial Omics"
- **Deadline**: May 3, 2026
- **Format**: 4–6 page short paper (extended abstract / proceedings style)
- **Strategy**: Write a full-length paper first, then condense to 4–5 pages for CIBB submission

### Toolchain: Markdown + BibTeX + Pandoc
The manuscript is written in Pandoc Markdown with citation keys. Pandoc compiles to DOCX (for submission) or PDF (for review).

```
manuscript/
├── manuscript.md          # Main text (Pandoc Markdown)
├── bibliography/
│   └── cibb2026_references.bib  # Master BibTeX — ALL citations
├── build.sh               # pandoc build script (docx/pdf/both)
└── csl/                   # Citation style files (if needed)
```

### How Citations Work
1. **In manuscript.md**: use `[@citation_key]` syntax, e.g., `[@Wolf2018]`, `[@Dicks2026; @Traag2019]`
2. **In bibliography/cibb2026_references.bib**: every cited key must have a BibTeX entry with correct DOI
3. **Pandoc** resolves keys → numbered/author-year references, auto-generates bibliography
4. **Key naming convention**: `Firstauthor_Year` (e.g., `Wolf2018`, `Dicks2026`, `Traag2019`)

### Operational Rules for Claude
- **NEVER invent DOIs or references**. If a citation is needed and not in the .bib file, flag it with `TODO_CITE` and describe what's needed.
- **Adding new references**: add to `bibliography/cibb2026_references.bib` with full metadata (authors, title, journal, year, volume, pages, DOI). Verify DOI exists via the source documents or web search.
- **Zotero integration**: the user can export from Zotero → BibTeX → paste into the .bib file. Keys may need renaming to match convention.

### Building the Manuscript
```bash
# DOCX for submission (default)
./manuscript/build.sh

# PDF for review
./manuscript/build.sh pdf

# Both formats
./manuscript/build.sh both
```

---

## Docker Hub Configuration

In the Makefile, set the following variables (ask user for their Docker Hub username):
```makefile
DOCKER_USER ?= lucavd
IMAGE_NAME ?= sc-benchmark
TAG ?= latest
```
