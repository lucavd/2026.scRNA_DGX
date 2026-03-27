#!/bin/bash
#SBATCH --job-name test_driver
#SBATCH --partition dgx12cluster
#SBATCH --account dctv_dgx
#SBATCH --output /home/u0044/sc-gpu-benchmark/logs/slurm-%x_%j.out
#SBATCH --error /home/u0044/sc-gpu-benchmark/logs/slurm-%x_%j.err
#SBATCH --export=NONE
#SBATCH --chdir=/home/u0044
#SBATCH --nodelist=poddgx02
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --time=00:10:00

# Load required modules
module load go/1.22.7
module load singularity/4.2.0
module load slurm/slurm/23.02.7

# Detect workdir
if [ -d /mnt/home/u0044/sc-gpu-benchmark ]; then
    WORKDIR=/mnt/home/u0044/sc-gpu-benchmark
elif [ -d /home/u0044/sc-gpu-benchmark ]; then
    WORKDIR=/home/u0044/sc-gpu-benchmark
else
    echo "FAILED: sc-gpu-benchmark not found"; exit 1
fi

CONTAINER=${WORKDIR}/sc-benchmark-2406.sif
SINGULARITY=/cm/shared/apps/singularity/4.2.0/bin/singularity
BIND_ARGS=(-B /home/u0044:/home/u0044)
[ -d /mnt/home/u0044 ] && BIND_ARGS+=(-B /mnt/home/u0044:/mnt/home/u0044)

run_in_container() {
    "${SINGULARITY}" exec --nv "${BIND_ARGS[@]}" "${CONTAINER}" "$@"
}

CONTAINER_PYTHON=$(run_in_container bash -lc 'for py in python python3 /opt/conda/bin/python /usr/bin/python3; do
    if command -v "$py" >/dev/null 2>&1; then command -v "$py"; exit 0; fi
    if [[ "$py" = /* && -x "$py" ]]; then echo "$py"; exit 0; fi
done; exit 1')

if [ $? -ne 0 ] || [ -z "${CONTAINER_PYTHON}" ]; then
    echo "FAILED: no Python found in container"
    exit 1
fi

echo "=== Driver test with full RAPIDS 24.06 container ==="
echo "Container: ${CONTAINER}"
echo "Python: ${CONTAINER_PYTHON}"
echo "Node: $(hostname)"
echo ""

nvidia-smi

echo ""
echo "=== Running GPU driver test ==="

run_in_container bash -lc "${CONTAINER_PYTHON} ${WORKDIR}/scripts/test_gpu_driver.py"
