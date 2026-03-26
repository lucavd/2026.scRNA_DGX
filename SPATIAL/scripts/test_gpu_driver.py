#!/usr/bin/env python3
"""Minimal GPU driver compatibility test.

Tests three levels of GPU access:
1. CuPy — direct CUDA (works even with old drivers)
2. RMM — RAPIDS memory manager (fails with driver 535 + RAPIDS 26.02)
3. rapids-singlecell — actual GPU-accelerated analysis

If all three pass, the container is compatible with the DGX driver.
Run inside the container with --nv flag:
    singularity exec --nv container.sif python test_gpu_driver.py
"""

import sys


def test_cupy() -> bool:
    """Test 1: CuPy basic GPU operation."""
    print("=" * 60)
    print("TEST 1: CuPy (direct CUDA)")
    print("=" * 60)
    try:
        import cupy as cp
        print(f"  CuPy version: {cp.__version__}")
        print(f"  CUDA version: {cp.cuda.runtime.runtimeGetVersion()}")
        a = cp.arange(1000, dtype=cp.float32)
        result = float(cp.sum(a))
        print(f"  GPU sum(0..999) = {result} (expected 499500.0)")
        assert abs(result - 499500.0) < 1.0
        print("  PASS\n")
        return True
    except Exception as e:
        print(f"  FAIL: {e}\n")
        return False


def test_rmm() -> bool:
    """Test 2: RMM memory manager (the usual failure point)."""
    print("=" * 60)
    print("TEST 2: RMM (RAPIDS memory manager)")
    print("=" * 60)
    try:
        import rmm
        print(f"  RMM version: {rmm.__version__}")
        # This is what fails with driver 535 + RAPIDS 26.02
        rmm.reinitialize(pool_allocator=True, initial_pool_size=256 * 1024 * 1024)
        print("  RMM pool initialized (256 MB)")
        # Allocate via RMM
        import cupy as cp
        x = cp.ones(1_000_000, dtype=cp.float32)
        result = float(cp.sum(x))
        print(f"  RMM allocation + sum = {result} (expected 1000000.0)")
        del x
        print("  PASS\n")
        return True
    except Exception as e:
        print(f"  FAIL: {e}\n")
        return False


def test_rapids_singlecell() -> bool:
    """Test 3: rapids-singlecell GPU transfer + basic operation."""
    print("=" * 60)
    print("TEST 3: rapids-singlecell (anndata_to_GPU)")
    print("=" * 60)
    try:
        import numpy as np
        import anndata as ad
        import rapids_singlecell as rsc
        print(f"  rapids-singlecell version: {rsc.__version__}")

        # Create tiny synthetic AnnData (100 cells × 200 genes)
        np.random.seed(42)
        X = np.random.poisson(1, size=(100, 200)).astype(np.float32)
        adata = ad.AnnData(X)

        # Transfer to GPU
        rsc.get.anndata_to_GPU(adata)
        print("  anndata_to_GPU: OK")

        # Run a GPU operation
        rsc.pp.normalize_total(adata)
        rsc.pp.log1p(adata)
        print("  normalize_total + log1p on GPU: OK")

        # Transfer back
        rsc.get.anndata_to_CPU(adata)
        print("  anndata_to_CPU: OK")
        print(f"  Result shape: {adata.X.shape}, dtype: {adata.X.dtype}")
        print("  PASS\n")
        return True
    except Exception as e:
        print(f"  FAIL: {e}\n")
        return False


def main() -> int:
    print("\nGPU Driver Compatibility Test")
    print(f"{'=' * 60}\n")

    # Print driver info
    try:
        import subprocess
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=driver_version,cuda_version,name",
             "--format=csv,noheader"],
            text=True,
        ).strip()
        print(f"GPU info: {out}\n")
    except Exception:
        print("nvidia-smi not available\n")

    results = {
        "CuPy": test_cupy(),
        "RMM": test_rmm(),
        "rapids-singlecell": test_rapids_singlecell(),
    }

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")

    all_pass = all(results.values())
    print(f"\nOverall: {'ALL PASS — container is compatible!' if all_pass else 'SOME FAILED'}")

    if not results["RMM"] and results["CuPy"]:
        print("\nDiagnosis: RMM fails but CuPy works → driver too old for this RAPIDS version.")
        print("Solution: use a RAPIDS version compatible with the installed driver.")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
