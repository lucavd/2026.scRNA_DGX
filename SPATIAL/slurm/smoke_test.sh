#!/bin/bash
#SBATCH --job-name spatial_smoke
#SBATCH --partition dgx12cluster
#SBATCH --account dctv_dgx
#SBATCH --output /home/u0044/sc-gpu-benchmark/SPATIAL/logs/slurm-smoke_%j.out
#SBATCH --error /home/u0044/sc-gpu-benchmark/SPATIAL/logs/slurm-smoke_%j.err
#SBATCH --nodes 1
#SBATCH --ntasks 1
#SBATCH --cpus-per-task 16
#SBATCH --mem 64G
#SBATCH --gres=gpu:1
#SBATCH --time 00:30:00
#SBATCH --nodelist=poddgx02
#SBATCH --export=NONE

# ── Module loading ──────────────────────────────────────────────────────
module load go/1.22.7
module load singularity/4.2.0
module load slurm/slurm/23.02.7

# ── Detect workdir ──────────────────────────────────────────────────────
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

DATA_DIR=${WORKDIR}/SPATIAL/data
OUTPUT_DIR=${WORKDIR}/SPATIAL/results

run_in_container() {
    "${SINGULARITY}" exec --nv "${BIND_ARGS[@]}" "${CONTAINER}" "$@"
}

echo "=== Spatial Smoke Test ==="
echo "Container: ${CONTAINER}"
echo "Data dir:  ${DATA_DIR}"
echo "Output:    ${OUTPUT_DIR}"
echo "Node:      $(hostname)"
echo "GPUs:      ${CUDA_VISIBLE_DEVICES}"
echo ""

# ── 1. CPU benchmark: Visium v1 ────────────────────────────────────────
echo ">>> [1/2] CPU benchmark — Visium v1 (2,695 spots)"
run_in_container python ${WORKDIR}/SPATIAL/scripts/benchmark_spatial_cpu.py \
    --data-dir "${DATA_DIR}" \
    --output-dir "${OUTPUT_DIR}" \
    --platform visium \
    --n-repeats 1 \
    --n-cpus 16
CPU_EXIT=$?
echo "CPU exit code: ${CPU_EXIT}"
echo ""

# ── 2. GPU benchmark: Visium v1 ────────────────────────────────────────
echo ">>> [2/2] GPU benchmark — Visium v1 (2,695 spots)"
run_in_container python ${WORKDIR}/SPATIAL/scripts/benchmark_spatial_gpu.py \
    --data-dir "${DATA_DIR}" \
    --output-dir "${OUTPUT_DIR}" \
    --platform visium \
    --n-repeats 1 \
    --device 0
GPU_EXIT=$?
echo "GPU exit code: ${GPU_EXIT}"
echo ""

# ── Summary ─────────────────────────────────────────────────────────────
echo "=== Smoke Test Done ==="
echo "CPU exit: ${CPU_EXIT}"
echo "GPU exit: ${GPU_EXIT}"
if [ ${CPU_EXIT} -eq 0 ] && [ ${GPU_EXIT} -eq 0 ]; then
    echo "ALL PASSED"
else
    echo "FAILURES DETECTED"
    exit 1
fi
