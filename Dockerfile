# Dockerfile for scRNA-seq + spatial omics GPU vs CPU benchmark
# Base: RAPIDS 24.06 / CUDA 12.2 — compatible with DGX driver 535.183.01
# Validated with Dockerfile.test (CuPy, RMM, rapids-singlecell all PASS)
FROM nvcr.io/nvidia/rapidsai/base:24.06-cuda12.2-py3.11

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies (run as root for apt)
USER root
RUN mkdir -p /var/lib/apt/lists/partial && \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# constraints.txt pins RAPIDS 24.06 base packages (dask, numpy, etc.)
# to prevent pip from upgrading them and breaking cuDF/dask_cudf
COPY constraints.txt /tmp/constraints.txt
COPY requirements-squidpy.txt /tmp/requirements-squidpy.txt

RUN pip install --no-cache-dir --no-deps rapids-singlecell && \
    pip install --no-cache-dir -c /tmp/constraints.txt \
    docrep \
    scanpy \
    anndata

RUN pip install --no-cache-dir -c /tmp/constraints.txt \
    scvi-tools \
    cellxgene-census \
    tiledbsoma

RUN pip install --no-cache-dir -c /tmp/constraints.txt \
    scikit-learn \
    matplotlib \
    seaborn \
    psutil \
    nvidia-ml-py \
    h5py \
    leidenalg \
    igraph

RUN pip install --no-cache-dir -c /tmp/constraints.txt -r /tmp/requirements-squidpy.txt && \
    pip install --no-cache-dir --no-deps squidpy==1.6.5 \
    && pip cache purge \
    && chmod -R o+rX /opt/conda

# Set working directory
WORKDIR /workspace

# Default command: open a shell
CMD ["/bin/bash"]
