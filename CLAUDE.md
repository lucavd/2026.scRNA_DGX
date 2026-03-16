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

1. **Dockerfile**: Build and test locally with `docker run --gpus all`. Verify `import scanpy`, `import rapids_singlecell`, GPU visibility (`nvidia-smi` inside container).
2. **Data download script**: Download the 1.3M brain dataset, run subsampling. Verify file sizes and cell counts.
3. **CPU benchmark script**: Run Scanpy pipeline on 10k cells locally. Verify timing, memory, and output JSON format.
4. **GPU benchmark script**: Run rapids-singlecell pipeline on 10k cells locally (RTX 4090). Verify timing, memory, and output JSON.
5. **Concordance script**: Compare CPU vs GPU results from steps 3–4. Verify ARI, NMI, HVG overlap.
6. **Push to Docker Hub, pull on DGX as Singularity**: First contact with the DGX. Run a minimal smoke test (10k cells, 1 GPU).
7. **SLURM jobs for full-scale CPU benchmark**: Run on DGX with all dataset sizes.
8. **SLURM jobs for GPU scaling**: 1/2/4/8 GPU on large datasets.
9. **Analysis and figures**: Generate publication-ready plots.

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

For this project we left `--nodelist` unset and let SLURM schedule freely. For future studies where node affinity matters, use `--nodelist=poddgx02` to pin jobs to our node.

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
#SBATCH --partition dgx12cluster
#SBATCH --account dctv_dgx
```

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
│   ├── compare_results.py    # Concordance + stability analysis
│   └── generate_figures.py   # Publication-ready plots
├── slurm/
│   ├── download.sh           # SLURM job: data download
│   ├── cpu_benchmark.sh      # SLURM job: CPU benchmarks
│   ├── gpu_1.sh              # SLURM job: 1 GPU
│   ├── gpu_2.sh              # SLURM job: 2 GPUs
│   ├── gpu_4.sh              # SLURM job: 4 GPUs
│   ├── gpu_8.sh              # SLURM job: 8 GPUs
│   └── analysis.sh           # SLURM job: compare results
├── data/                     # Downloaded datasets (in home dir — 500 GB available)
├── results/                  # Benchmark outputs (JSON/CSV)
└── figures/                  # Generated plots
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

---

## Execution Order

Follow the **Suggested Step Sequence** in the "Development Rules" section above. Summary:

**LOCAL PHASE** (steps 1–5):
1. Dockerfile → build + test locally with RTX 4090
2. Data download + subsampling script → verify locally
3. CPU benchmark script → run on 10k cells locally, check outputs
4. GPU benchmark script → run on 10k cells locally (RTX 4090), check outputs
5. Concordance script → compare CPU vs GPU, verify metrics

**DGX PHASE** (steps 6–9):
6. Push container to Docker Hub, pull on DGX, smoke test (10k cells, 1 GPU)
7. Full-scale CPU benchmarks (all dataset sizes, 5 repeats)
8. GPU scaling benchmarks (1/2/4/8 GPUs on 500k and 1.3M, 5 repeats)
9. Analysis and figure generation

**Each step requires user approval before proceeding to the next.** Steps 7–8 can run in parallel on the DGX if cluster capacity allows.

---

## Docker Hub Configuration

In the Makefile, set the following variables (ask user for their Docker Hub username):
```makefile
DOCKER_USER ?= lucavd
IMAGE_NAME ?= sc-benchmark
TAG ?= latest
```
