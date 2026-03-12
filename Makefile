DOCKER_USER ?= lucavd
IMAGE_NAME ?= sc-benchmark
TAG ?= latest
FULL_IMAGE = $(DOCKER_USER)/$(IMAGE_NAME):$(TAG)

# Local development
build:
	docker build -t $(FULL_IMAGE) .

run:
	docker run --rm -it --gpus all \
		-v $(PWD):/workspace \
		$(FULL_IMAGE)

run-cpu:
	docker run --rm -it \
		-v $(PWD):/workspace \
		$(FULL_IMAGE)

# Test: verify GPU visibility and key imports
test:
	docker run --rm --gpus all $(FULL_IMAGE) \
		bash -c "nvidia-smi && python -c 'import scanpy; import rapids_singlecell; import cupy; print(\"scanpy:\", scanpy.__version__); print(\"rapids_singlecell:\", rapids_singlecell.__version__); print(\"cupy:\", cupy.__version__); print(\"All imports OK\")'"

# Data download (runs inside container, no GPU needed)
download-data:
	docker run --rm \
		-v $(PWD):/workspace \
		$(FULL_IMAGE) \
		python -u scripts/download_data.py --data-dir /workspace/data --max-cells 100000

# Benchmarks
bench-cpu:
	docker run --rm \
		-v $(PWD):/workspace \
		$(FULL_IMAGE) \
		python -u scripts/benchmark_cpu.py \
			--data-dir /workspace/data \
			--output-dir /workspace/results \
			--n-cells 10000

bench-gpu:
	docker run --rm --gpus all \
		-v $(PWD):/workspace \
		$(FULL_IMAGE) \
		python -u scripts/benchmark_gpu.py \
			--data-dir /workspace/data \
			--output-dir /workspace/results \
			--n-cells 10000

concordance:
	docker run --rm \
		-v $(PWD):/workspace \
		$(FULL_IMAGE) \
		python -u scripts/compare_results.py \
			--results-dir /workspace/results \
			--n-cells 10000

# Docker Hub
push:
	docker push $(FULL_IMAGE)

# Singularity (run on DGX login node)
pull-singularity:
	singularity pull $(IMAGE_NAME).sif docker://$(FULL_IMAGE)
	singularity cache clean

.PHONY: build run run-cpu test download-data bench-cpu bench-gpu concordance push pull-singularity
