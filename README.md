# 2026.scRNA_DGX

GPU-accelerated single-cell and spatial transcriptomics benchmark on NVIDIA DGX H100, comparing the CPU-based Scanpy stack against rapids-singlecell (GPU) for speed, biological concordance, and scale. Companion repository for the CIBB 2026 short paper.

Key findings (scRNA-seq, mouse brain 1.3M cells):

- 120x end-to-end speedup on 1 to 8 H100 GPUs vs 100-core CPU (14.5 h to 7.3 min).
- Biological concordance is high: HVG Jaccard = 1.000, PCA Spearman rho = 1.000, Leiden ARI 0.908 to 0.963.
- CPU-side preprocessing, not GPU VRAM, is the binding constraint at extreme scale (maximum processable: 11.9M cells on a single DGX H100 node).
- For spatial (Visium HD 8 um, 393k bins): 51.6x overall speedup, 3,272x speedup for co-occurrence analysis, near-perfect Moran/Geary concordance (rho >= 0.9995).

## Repository structure

```
.
|-- Dockerfile                # RAPIDS 26.02 / CUDA 12 / Python 3.12 base
|-- Makefile                  # build / run / test / bench targets
|-- constraints.txt           # pinned pip constraints
|-- requirements-squidpy.txt  # extra deps for the spatial benchmark
|-- scripts/                  # Python benchmarks and analyses
|-- slurm/                    # SLURM submission scripts for the DGX cluster
|-- SPATIAL/                  # spatial-omics benchmark (self-contained)
|-- data/                     # downloaded datasets (gitignored)
|-- results/                  # benchmark JSON outputs
|-- figures/                  # publication-ready PNGs + LEGENDS.md
|-- manuscript/               # Pandoc Markdown source + BibTeX + build.sh
|-- README.md                 # this file
`-- CLAUDE.md                 # full project notebook (development log)
```

## Requirements

- NVIDIA GPU with CUDA 12 support (tested on RTX 4090 locally and H100 SXM on the DGX).
- NVIDIA driver version that supports the CUDA 12.8 runtime (native or via forward-compatibility). The DGX cluster used for the paper runs driver 535.183.01, which is compatible via CUDA forward-compatibility for scRNA-seq workloads.
- Docker with the NVIDIA Container Toolkit (`nvidia-docker`) for GPU passthrough.
- Disk: ~50 GB for the container image plus datasets.
- RAM: 16 GB minimum to run on the 10k-cell tier; 64 GB+ recommended for 100k+.

## Quickstart with Docker

1. Clone the repository and enter it:

   ```bash
   git clone https://github.com/lucavd/2026.scRNA_DGX.git
   cd 2026.scRNA_DGX
   ```

2. Build the image (or pull the pre-built one from Docker Hub):

   ```bash
   make build
   # or:
   docker pull lucavd/sc-benchmark:latest
   ```

3. Smoke-test that Docker sees the GPU and all libraries import:

   ```bash
   make test
   ```

   Expected output: `nvidia-smi` table plus library version strings (scanpy, rapids-singlecell, cupy).

4. Run the full benchmark pipeline on a small dataset (10k cells). The commands below use the Makefile targets; each one runs the corresponding Python script inside the container with the correct bind mounts.

   ```bash
   make download-data        # fetches the 1.3M mouse-brain dataset and subsamples
   make bench-cpu            # CPU baseline (Scanpy)
   make bench-gpu            # single-GPU GPU pipeline (rapids-singlecell)
   make concordance          # CPU vs GPU biological agreement
   ```

   All results land in `results/` as JSON.

### Opening an interactive shell inside the container

```bash
make run        # interactive shell with GPU access
make run-cpu    # interactive shell, CPU only
```

The current working directory is bind-mounted at `/workspace` inside the container.

## Running specific benchmarks

### scRNA-seq

CPU baseline and GPU single-device, 10k cells (default):

```bash
make bench-cpu
make bench-gpu
```

Larger scale (set `N_CELLS` to 10000, 50000, 100000, 500000, or 1300000):

```bash
docker run --rm --gpus all -v $(pwd):/workspace lucavd/sc-benchmark:latest \
    python -u scripts/benchmark_gpu.py \
        --data-dir /workspace/data \
        --output-dir /workspace/results \
        --n-cells 100000
```

Multi-GPU (requires 2, 4, or 8 devices):

```bash
docker run --rm --gpus all -v $(pwd):/workspace lucavd/sc-benchmark:latest \
    python -u scripts/benchmark_multigpu.py \
        --data-dir /workspace/data \
        --output-dir /workspace/results \
        --n-cells 500000 \
        --n-gpus 4
```

### Differential expression

The factorial DE benchmark (7 configurations, 3.4M cells):

```bash
docker run --rm --gpus all -v $(pwd):/workspace lucavd/sc-benchmark:latest \
    python -u scripts/test_de_benchmark.py \
        --data-dir /workspace/data \
        --output-dir /workspace/results
```

### Maximum-capacity stress test

Binary search for the largest processable cell count:

```bash
docker run --rm --gpus all -v $(pwd):/workspace lucavd/sc-benchmark:latest \
    python -u scripts/benchmark_maxpower.py \
        --data-dir /workspace/data \
        --output-dir /workspace/results \
        --find-limit
```

Chunked variant (Step 10c, ScaleSC-inspired):

```bash
docker run --rm --gpus all -v $(pwd):/workspace lucavd/sc-benchmark:latest \
    python -u scripts/benchmark_maxpower_chunked.py \
        --data-dir /workspace/data \
        --output-dir /workspace/results \
        --target-cells 12000000
```

### Spatial transcriptomics

Visium v1, Visium HD 8 um, and Visium HD 2 um benchmarks (Makefile targets):

```bash
# Visium v1 (classical)
make bench-spatial-cpu SPATIAL_PLATFORM=visium SPATIAL_BIN_SIZE=
make bench-spatial-gpu SPATIAL_PLATFORM=visium SPATIAL_BIN_SIZE=

# Visium HD 8 um
make bench-spatial-cpu SPATIAL_PLATFORM=visium_hd SPATIAL_BIN_SIZE=square_008um
make bench-spatial-gpu SPATIAL_PLATFORM=visium_hd SPATIAL_BIN_SIZE=square_008um

# Visium HD 2 um (subsample if VRAM is limited)
make bench-spatial-cpu SPATIAL_PLATFORM=visium_hd SPATIAL_BIN_SIZE=square_002um SPATIAL_MAX_SPOTS=400000
make bench-spatial-gpu SPATIAL_PLATFORM=visium_hd SPATIAL_BIN_SIZE=square_002um SPATIAL_MAX_SPOTS=400000

make spatial-concordance SPATIAL_PLATFORM=visium_hd SPATIAL_BIN_SIZE=square_008um
```

See `SPATIAL/SPATIAL.md` for the spatial-pipeline specifics.

### Figures

After the JSON outputs are produced in `results/`, regenerate all figures used in the manuscript:

```bash
docker run --rm -v $(pwd):/workspace lucavd/sc-benchmark:latest \
    python -u scripts/generate_figures.py \
        --results-dir /workspace/results \
        --figures-dir /workspace/figures
```

## Running on the DGX H100 cluster (SLURM)

The cluster does not allow user-installable software; benchmarks run inside a Singularity container converted from the same Docker image.

1. On the login node, pull and convert the image:

   ```bash
   cd /mnt/home/$USER
   singularity pull sc-benchmark.sif docker://lucavd/sc-benchmark:latest
   singularity cache clean
   ```

2. Submit the SLURM job scripts in `slurm/` (edit paths and account as needed):

   ```bash
   sbatch slurm/cpu_benchmark.sh     # 100-core CPU run
   sbatch slurm/gpu_1.sh             # 1 GPU
   sbatch slurm/gpu_4.sh             # 4 GPUs
   sbatch slurm/gpu_8.sh             # 8 GPUs
   sbatch slurm/maxpower.sh          # stress test
   sbatch slurm/de_benchmark.sh      # DE factorial
   ```

Each SLURM script bind-mounts `/mnt/home/$USER` into the container so that `data/` and `results/` are visible.

## Reproducibility

- All stochastic steps use seed `42`: `numpy.random.choice` for subsampling, `sc.pp.pca` / `rsc.pp.pca`, `sc.tl.leiden` / `rsc.tl.leiden`, `sc.tl.umap` / `rsc.tl.umap`.
- Container and package versions are pinned by the `Dockerfile` (`nvcr.io/nvidia/rapidsai/base:26.02-cuda12-py3.12`) and `constraints.txt`.
- Key versions: Scanpy 1.12, rapids-singlecell 0.14.1, CuPy 13.6.0, RMM 26.2.0, NumPy 2.2.6, Python 3.12.
- GPU floating-point arithmetic is non-deterministic (non-associative parallel reductions); bit-identical outputs are not expected. The concordance metrics in `results/concordance_*.json` quantify the resulting numerical drift.

## Citation

Please cite the CIBB 2026 short paper once published. Bibliography entries for all tools and datasets used are in `manuscript/bibliography/cibb2026_references.bib`.

## License

See `LICENSE.md`.
