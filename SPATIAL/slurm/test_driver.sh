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

CONTAINER=${WORKDIR}/sc-benchmark-test.sif
SINGULARITY=/cm/shared/apps/singularity/4.2.0/bin/singularity
BIND_ARGS=(-B /home/u0044:/home/u0044)
[ -d /mnt/home/u0044 ] && BIND_ARGS+=(-B /mnt/home/u0044:/mnt/home/u0044)

echo "=== Driver test with RAPIDS 24.06 NGC base container ==="
echo "Container: ${CONTAINER}"
echo "Node: $(hostname)"
echo ""

# Show GPU info from host
nvidia-smi

echo ""
echo "=== Fixing permissions + installing + testing ==="
"${SINGULARITY}" exec --nv --writable-tmpfs "${BIND_ARGS[@]}" "${CONTAINER}" \
    bash -lc '
echo "Python: $(which python3)"
python3 --version
echo ""
echo "=== Running GPU driver test ==="
python3 '"${WORKDIR}"'/scripts/test_gpu_driver.py
'
