#!/usr/bin/env python3
"""Generate publication-ready figures for GPU vs CPU scRNA-seq benchmark.

Reads JSON result files from the results/ directory and produces:
  1. Speedup heatmap (single-GPU vs CPU, per step × dataset size)
  2. Multi-GPU scaling plot (wall time vs n_GPUs)
  3. Concordance bar chart (ARI, NMI, HVG Jaccard from 10k data)
  4. Memory profile (peak RAM / VRAM across dataset sizes)
  5. Step-level timing breakdown (stacked bars)

Usage:
    python scripts/generate_figures.py --results-dir results/ --output-dir figures/
    python scripts/generate_figures.py --help
"""

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Global style
# ---------------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 9,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.1,
})

# Colour palette — distinguishable, colour-blind friendly
COLORS = {
    "cpu": "#4477AA",
    "gpu1": "#EE6677",
    "gpu2": "#228833",
    "gpu4": "#CCBB44",
    "gpu8": "#AA3377",
}

# Pipeline steps in execution order (for stacked bars and heatmap)
COMMON_STEPS = [
    "data_loading", "qc_filtering", "normalization", "hvg_selection",
    "pca", "neighbors", "leiden_0.5", "leiden_1.0", "leiden_1.5",
    "umap", "de_testing",
]

# Pretty labels
STEP_LABELS = {
    "data_loading": "Data loading",
    "qc_filtering": "QC & filtering",
    "normalization": "Normalization",
    "hvg_selection": "HVG selection",
    "pca": "PCA",
    "neighbors": "Neighbors",
    "leiden_0.5": "Leiden 0.5",
    "leiden_1.0": "Leiden 1.0",
    "leiden_1.5": "Leiden 1.5",
    "umap": "UMAP",
    "de_testing": "DE testing",
    "gpu_transfer": "GPU transfer",
    "scale": "Scale",
}

DATASET_SIZES = [10_000, 50_000, 100_000, 500_000, 1_300_000]
SIZE_LABELS = {10_000: "10k", 50_000: "50k", 100_000: "100k",
               500_000: "500k", 1_300_000: "1.3M"}

# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def _prefix(pipeline: str, n_cells: int, n_gpus: int = 0) -> str:
    """Build the file prefix used in result JSON filenames."""
    if pipeline == "cpu":
        return f"cpu_{n_cells}"
    if n_gpus == 1:
        return f"gpu_{n_cells}"
    return f"gpu{n_gpus}_{n_cells}"


def load_all_results(results_dir: Path) -> pd.DataFrame:
    """Load every *_results.json into a flat DataFrame.

    Each row is one (pipeline, n_cells, n_gpus, repeat) combination with
    columns for every timing step, memory, and metadata fields.

    Args:
        results_dir: Path to the results/ directory.

    Returns:
        DataFrame indexed by (pipeline, n_cells, n_gpus, repeat).
    """
    rows: list[dict[str, Any]] = []

    for jf in sorted(results_dir.glob("*_results.json")):
        data = json.loads(jf.read_text())
        meta = data["metadata"]

        row: dict[str, Any] = {
            "pipeline": meta["pipeline"],
            "n_cells": meta["n_cells_input"],
            "n_gpus": meta.get("n_gpus", 0),
            "repeat": meta.get("repeat_id", 1),
            "total_time": data["timings"].get("total", np.nan),
            "peak_ram_gb": data["memory"]["peak_ram_gb"],
            "peak_vram_gb": data["memory"]["peak_vram_gb"],
        }

        # Individual step timings
        for step in COMMON_STEPS:
            row[f"t_{step}"] = data["timings"].get(step, np.nan)

        # Multi-GPU extra steps
        for extra in ("gpu_transfer", "scale"):
            row[f"t_{extra}"] = data["timings"].get(extra, np.nan)

        rows.append(row)

    df = pd.DataFrame(rows)
    print(f"Loaded {len(df)} result files from {results_dir}")
    return df


def load_concordance(results_dir: Path) -> dict | None:
    """Load concordance JSON for 10k repeat 1 (the only one with full data)."""
    path = results_dir / "concordance_10000_r1.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def _mean_std(series: pd.Series) -> tuple[float, float]:
    """Return (mean, std) for a pandas Series, handling NaN."""
    return float(series.mean()), float(series.std(ddof=1)) if len(series) > 1 else 0.0


# ---------------------------------------------------------------------------
# Figure 1: Speedup heatmap — single GPU vs CPU
# ---------------------------------------------------------------------------

def fig_speedup_heatmap(df: pd.DataFrame, output_dir: Path) -> None:
    """Heatmap: rows = pipeline steps, cols = dataset sizes.

    Cell value = CPU_mean_time / GPU_mean_time (speedup factor).
    Only for single-GPU (n_gpus == 1) vs CPU.
    """
    # Sizes where single GPU exists
    gpu1_sizes = sorted(df.loc[df["n_gpus"] == 1, "n_cells"].unique())

    steps = COMMON_STEPS
    matrix = np.full((len(steps), len(gpu1_sizes)), np.nan)

    for j, size in enumerate(gpu1_sizes):
        cpu = df[(df["pipeline"] == "cpu_scanpy") & (df["n_cells"] == size)]
        gpu = df[(df["n_gpus"] == 1) & (df["n_cells"] == size)]
        if cpu.empty or gpu.empty:
            continue
        for i, step in enumerate(steps):
            cpu_mean = cpu[f"t_{step}"].mean()
            gpu_mean = gpu[f"t_{step}"].mean()
            if gpu_mean > 0:
                matrix[i, j] = cpu_mean / gpu_mean

    fig, ax = plt.subplots(figsize=(4.5, 5.5))

    # Custom colormap: red (<1 = GPU slower), white (1), blue (>1 = GPU faster)
    from matplotlib.colors import TwoSlopeNorm
    vmin = np.nanmin(matrix[matrix > 0]) if np.any(matrix > 0) else 0.1
    vmax = np.nanmax(matrix)
    norm = TwoSlopeNorm(vmin=vmin, vcenter=1.0, vmax=vmax)

    im = ax.imshow(matrix, aspect="auto", cmap="RdYlBu", norm=norm)

    # Annotate cells
    for i in range(len(steps)):
        for j in range(len(gpu1_sizes)):
            val = matrix[i, j]
            if np.isnan(val):
                ax.text(j, i, "—", ha="center", va="center", fontsize=8,
                        color="gray")
            else:
                color = "white" if val > vmax * 0.7 or val < 0.3 else "black"
                label = f"{val:.1f}×" if val >= 10 else f"{val:.2f}×"
                ax.text(j, i, label, ha="center", va="center", fontsize=7.5,
                        fontweight="bold", color=color)

    ax.set_xticks(range(len(gpu1_sizes)))
    ax.set_xticklabels([SIZE_LABELS[s] for s in gpu1_sizes])
    ax.set_yticks(range(len(steps)))
    ax.set_yticklabels([STEP_LABELS.get(s, s) for s in steps])
    ax.set_xlabel("Dataset size (cells)")

    cbar = fig.colorbar(im, ax=ax, shrink=0.6, label="Speedup (CPU time / GPU time)")

    fig.savefig(output_dir / "fig1_speedup_heatmap.png")
    plt.close(fig)
    print("  Figure 1: speedup heatmap saved")


# ---------------------------------------------------------------------------
# Figure 2: Multi-GPU scaling plot
# ---------------------------------------------------------------------------

def fig_scaling_plot(df: pd.DataFrame, output_dir: Path) -> None:
    """Line plot: x = n_GPUs, y = total wall time. One line per dataset size."""
    fig, ax = plt.subplots(figsize=(6, 4.5))

    # All GPU configs
    gpu_configs = sorted(df.loc[df["n_gpus"] > 0, "n_gpus"].unique())
    all_sizes = sorted(df["n_cells"].unique())

    markers = ["o", "s", "D", "^", "v"]
    cmap = plt.cm.viridis(np.linspace(0.15, 0.85, len(all_sizes)))

    for idx, size in enumerate(all_sizes):
        gpus_for_size = []
        means = []
        stds = []
        for ng in gpu_configs:
            subset = df[(df["n_gpus"] == ng) & (df["n_cells"] == size)]
            if subset.empty:
                continue
            m, s = _mean_std(subset["total_time"])
            gpus_for_size.append(ng)
            means.append(m)
            stds.append(s)

        if not gpus_for_size:
            continue

        means_arr = np.array(means)
        stds_arr = np.array(stds)

        ax.errorbar(gpus_for_size, means_arr, yerr=stds_arr,
                     marker=markers[idx % len(markers)],
                     color=cmap[idx], label=f"{SIZE_LABELS[size]} (GPU)",
                     linewidth=1.5, markersize=5, capsize=3)

    # Add CPU reference as separate markers at x=0 position
    for idx, size in enumerate(all_sizes):
        cpu_sub = df[(df["pipeline"] == "cpu_scanpy") & (df["n_cells"] == size)]
        if cpu_sub.empty:
            continue
        cpu_mean = cpu_sub["total_time"].mean()
        ax.axhline(y=cpu_mean, color=cmap[idx], linestyle=":", alpha=0.3,
                    linewidth=0.7)

    # Build a second legend for CPU lines
    from matplotlib.lines import Line2D
    cpu_handles = []
    for idx, size in enumerate(all_sizes):
        cpu_sub = df[(df["pipeline"] == "cpu_scanpy") & (df["n_cells"] == size)]
        if not cpu_sub.empty:
            cpu_handles.append(Line2D([0], [0], color=cmap[idx], linestyle=":",
                                       alpha=0.5, label=f"{SIZE_LABELS[size]} (CPU)"))

    ax.set_xlabel("Number of GPUs")
    ax.set_ylabel("Total wall time (seconds)")
    ax.set_yscale("log")
    ax.set_xticks(gpu_configs)
    ax.set_xticklabels([str(g) for g in gpu_configs])

    # Combined legend inside plot area
    handles1, labels1 = ax.get_legend_handles_labels()
    all_handles = handles1 + cpu_handles
    all_labels = labels1 + [h.get_label() for h in cpu_handles]
    ax.legend(all_handles, all_labels, fontsize=7, loc="center right",
              ncol=1, framealpha=0.9)

    ax.grid(True, alpha=0.3, which="both")
    ax.set_xlim(0.5, max(gpu_configs) + 0.5)

    fig.tight_layout()
    fig.savefig(output_dir / "fig2_scaling_plot.png")
    plt.close(fig)
    print("  Figure 2: scaling plot saved")


# ---------------------------------------------------------------------------
# Figure 3: Concordance bar chart
# ---------------------------------------------------------------------------

def fig_concordance(concordance: dict, output_dir: Path) -> None:
    """Grouped bar chart: ARI, NMI, HVG Jaccard for each Leiden resolution."""
    cluster = concordance["cluster_concordance"]
    hvg_j = concordance["hvg_concordance"]["jaccard"]
    pca_rho = concordance["pca_concordance"]["mean_abs_spearman_rho"]
    knn_j = concordance.get("knn_concordance", {}).get("mean_jaccard", np.nan)

    resolutions = ["leiden_0.5", "leiden_1.0", "leiden_1.5"]
    ari_vals = [cluster[r]["ari"] for r in resolutions]
    nmi_vals = [cluster[r]["nmi"] for r in resolutions]

    fig, axes = plt.subplots(1, 2, figsize=(8, 3.5), gridspec_kw={"width_ratios": [3, 2]})

    # Left panel: ARI and NMI per resolution
    ax = axes[0]
    x = np.arange(len(resolutions))
    w = 0.35
    bars1 = ax.bar(x - w / 2, ari_vals, w, label="ARI", color="#4477AA", edgecolor="white")
    bars2 = ax.bar(x + w / 2, nmi_vals, w, label="NMI", color="#EE6677", edgecolor="white")

    for bars in [bars1, bars2]:
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.005,
                    f"{h:.3f}", ha="center", va="bottom", fontsize=7)

    ax.set_xticks(x)
    ax.set_xticklabels(["res=0.5", "res=1.0", "res=1.5"])
    ax.set_ylim(0.85, 1.02)
    ax.set_ylabel("Score")
    ax.legend(loc="lower left")
    ax.axhline(1.0, color="gray", linestyle="--", linewidth=0.5, alpha=0.5)

    # Right panel: other metrics
    ax2 = axes[1]
    metrics = ["HVG\nJaccard", "PCA\nSpearman |ρ|", "kNN\nJaccard"]
    values = [hvg_j, pca_rho, knn_j]
    colors = ["#228833", "#CCBB44", "#66CCEE"]
    bars = ax2.bar(metrics, values, color=colors, edgecolor="white", width=0.6)
    for bar, val in zip(bars, values):
        if not np.isnan(val):
            ax2.text(bar.get_x() + bar.get_width() / 2, val + 0.005,
                     f"{val:.3f}", ha="center", va="bottom", fontsize=7)
    ax2.set_ylim(0.85, 1.05)
    ax2.axhline(1.0, color="gray", linestyle="--", linewidth=0.5, alpha=0.5)

    fig.tight_layout()
    fig.savefig(output_dir / "fig3_concordance.png")
    plt.close(fig)
    print("  Figure 3: concordance chart saved")


# ---------------------------------------------------------------------------
# Figure 4: Memory profile
# ---------------------------------------------------------------------------

def fig_memory_profile(df: pd.DataFrame, output_dir: Path) -> None:
    """Peak RAM (CPU) and peak VRAM (GPU) across dataset sizes."""
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.5))

    # --- Left: Peak RAM ---
    ax = axes[0]
    configs = [
        ("cpu_scanpy", 0, "CPU (100 cores)", COLORS["cpu"]),
        ("gpu_rapids", 1, "1× GPU", COLORS["gpu1"]),
    ]
    # Add multi-GPU
    for ng, label, col in [(2, "2× GPU", COLORS["gpu2"]),
                            (4, "4× GPU", COLORS["gpu4"]),
                            (8, "8× GPU", COLORS["gpu8"])]:
        configs.append((f"gpu_rapids_{ng}gpu", ng, label, col))

    for pipe, ng, label, color in configs:
        sizes_plot = []
        means = []
        for size in DATASET_SIZES:
            if ng == 0:
                sub = df[(df["pipeline"] == pipe) & (df["n_cells"] == size)]
            elif ng == 1:
                sub = df[(df["n_gpus"] == ng) & (df["n_cells"] == size)]
            else:
                sub = df[(df["n_gpus"] == ng) & (df["n_cells"] == size)]
            if sub.empty:
                continue
            sizes_plot.append(size)
            means.append(sub["peak_ram_gb"].mean())
        if sizes_plot:
            ax.plot(sizes_plot, means, marker="o", label=label, color=color,
                    linewidth=1.5, markersize=4)

    ax.set_xscale("log")
    ax.set_xlabel("Dataset size (cells)")
    ax.set_ylabel("Peak RAM (GB)")
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: SIZE_LABELS.get(int(x), f"{int(x/1000)}k")))

    # --- Right: Peak VRAM ---
    ax2 = axes[1]
    for pipe, ng, label, color in configs[1:]:  # skip CPU (no VRAM)
        sizes_plot = []
        means = []
        for size in DATASET_SIZES:
            if ng == 1:
                sub = df[(df["n_gpus"] == ng) & (df["n_cells"] == size)]
            else:
                sub = df[(df["n_gpus"] == ng) & (df["n_cells"] == size)]
            if sub.empty:
                continue
            sizes_plot.append(size)
            means.append(sub["peak_vram_gb"].mean())
        if sizes_plot:
            ax2.plot(sizes_plot, means, marker="s", label=label, color=color,
                     linewidth=1.5, markersize=4)

    # H100 VRAM limit reference
    ax2.axhline(y=79.6, color="red", linestyle="--", linewidth=0.8, alpha=0.5)
    ax2.text(DATASET_SIZES[0], 80.5, "H100 80 GB VRAM limit", fontsize=7,
             color="red", alpha=0.7)

    ax2.set_xscale("log")
    ax2.set_xlabel("Dataset size (cells)")
    ax2.set_ylabel("Peak VRAM (GB)")
    ax2.legend(fontsize=7)
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: SIZE_LABELS.get(int(x), f"{int(x/1000)}k")))

    fig.tight_layout()
    fig.savefig(output_dir / "fig4_memory_profile.png")
    plt.close(fig)
    print("  Figure 4: memory profile saved")


# ---------------------------------------------------------------------------
# Figure 5: Step-level timing breakdown (stacked bars)
# ---------------------------------------------------------------------------

def fig_timing_breakdown(df: pd.DataFrame, output_dir: Path) -> None:
    """Stacked bar charts: time per step for CPU vs GPU at each dataset size.

    One panel per dataset size (where both CPU and single-GPU exist).
    """
    # Sizes with both CPU and single-GPU data
    gpu1_sizes = sorted(df.loc[df["n_gpus"] == 1, "n_cells"].unique())

    n_panels = len(gpu1_sizes)
    fig, axes = plt.subplots(1, n_panels + 1, figsize=(3 * n_panels + 2.5, 4.2),
                              sharey=False,
                              gridspec_kw={"width_ratios": [1] * n_panels + [0.6]})
    if n_panels == 1:
        axes = list(axes)

    step_colors = plt.cm.Set3(np.linspace(0, 1, len(COMMON_STEPS)))

    for panel_idx, size in enumerate(gpu1_sizes):
        ax = axes[panel_idx]
        cpu_sub = df[(df["pipeline"] == "cpu_scanpy") & (df["n_cells"] == size)]
        gpu_sub = df[(df["n_gpus"] == 1) & (df["n_cells"] == size)]

        cpu_means = [cpu_sub[f"t_{s}"].mean() for s in COMMON_STEPS]
        gpu_means = [gpu_sub[f"t_{s}"].mean() for s in COMMON_STEPS]

        # Stacked bars
        cpu_bottom = 0.0
        gpu_bottom = 0.0
        for i, step in enumerate(COMMON_STEPS):
            cpu_h = cpu_means[i] if not np.isnan(cpu_means[i]) else 0
            gpu_h = gpu_means[i] if not np.isnan(gpu_means[i]) else 0
            label = STEP_LABELS.get(step, step) if panel_idx == 0 else None
            ax.bar(0, cpu_h, bottom=cpu_bottom, color=step_colors[i],
                   edgecolor="white", linewidth=0.3, width=0.6, label=label)
            ax.bar(1, gpu_h, bottom=gpu_bottom, color=step_colors[i],
                   edgecolor="white", linewidth=0.3, width=0.6)
            cpu_bottom += cpu_h
            gpu_bottom += gpu_h

        # Leave headroom for total labels
        y_max = max(cpu_bottom, gpu_bottom)
        ax.set_ylim(0, y_max * 1.12)

        ax.text(0, cpu_bottom + y_max * 0.02, f"{cpu_bottom:.0f}s",
                ha="center", va="bottom", fontsize=7, fontweight="bold")
        ax.text(1, gpu_bottom + y_max * 0.02, f"{gpu_bottom:.0f}s",
                ha="center", va="bottom", fontsize=7, fontweight="bold")

        ax.set_xticks([0, 1])
        ax.set_xticklabels(["CPU", "1\u00d7 GPU"], fontsize=8)
        ax.set_xlabel(f"{SIZE_LABELS[size]} cells", fontsize=9)
        if panel_idx == 0:
            ax.set_ylabel("Wall time (seconds)")

    # Legend in the extra rightmost panel (invisible axes)
    ax_leg = axes[-1]
    ax_leg.set_axis_off()
    handles, labels = axes[0].get_legend_handles_labels()
    ax_leg.legend(handles, labels, loc="center left", fontsize=7,
                  title="Pipeline step", title_fontsize=8, frameon=False)

    fig.tight_layout()
    fig.subplots_adjust(wspace=0.35)
    fig.savefig(output_dir / "fig5_timing_breakdown.png")
    plt.close(fig)
    print("  Figure 5: timing breakdown saved")


# ---------------------------------------------------------------------------
# Bonus: Figure 6 — Multi-GPU timing breakdown for large datasets
# ---------------------------------------------------------------------------

def fig_multigpu_breakdown(df: pd.DataFrame, output_dir: Path) -> None:
    """Stacked bars for multi-GPU configs on 500k and 1.3M cells.

    Shows CPU steps vs GPU steps to illustrate why multi-GPU scaling is flat.
    """
    large_sizes = [s for s in [500_000, 1_300_000]
                   if not df[(df["n_gpus"] >= 2) & (df["n_cells"] == s)].empty]
    if not large_sizes:
        print("  Figure 6: skipped (no multi-GPU large dataset results)")
        return

    gpu_configs = sorted(df.loc[df["n_gpus"] >= 2, "n_gpus"].unique())

    # Steps split into phases
    cpu_phase = ["data_loading", "qc_filtering", "normalization", "hvg_selection"]
    transfer_phase = ["gpu_transfer", "scale"]
    multigpu_phase = ["pca", "neighbors"]
    singlegpu_phase = ["leiden_0.5", "leiden_1.0", "leiden_1.5", "umap", "de_testing"]

    phases = [
        ("CPU preprocessing", cpu_phase, "#4477AA"),
        ("GPU transfer + scale", transfer_phase, "#BBBBBB"),
        ("Multi-GPU (PCA, neighbors)", multigpu_phase, "#EE6677"),
        ("Single-GPU (leiden, UMAP, DE)", singlegpu_phase, "#228833"),
    ]

    n_panels = len(large_sizes)
    fig, axes = plt.subplots(1, n_panels + 1, figsize=(4 * n_panels + 2.5, 4.2),
                              sharey=False,
                              gridspec_kw={"width_ratios": [1] * n_panels + [0.7]})

    for panel_idx, size in enumerate(large_sizes):
        ax = axes[panel_idx]

        cpu_sub = df[(df["pipeline"] == "cpu_scanpy") & (df["n_cells"] == size)]
        cpu_total = cpu_sub["total_time"].mean() if not cpu_sub.empty else 0

        x_pos = list(range(len(gpu_configs)))
        x_labels = [f"{ng}\u00d7 GPU" for ng in gpu_configs]

        if cpu_total > 0:
            x_pos = list(range(len(gpu_configs) + 1))
            x_labels = ["CPU\n(100 cores)"] + x_labels

        bottoms = [0.0] * len(x_pos)
        for phase_name, phase_steps, phase_color in phases:
            heights = []
            if cpu_total > 0:
                if phase_name.startswith("CPU"):
                    h = sum(cpu_sub[f"t_{s}"].mean() for s in COMMON_STEPS
                            if not np.isnan(cpu_sub[f"t_{s}"].mean()))
                    heights.append(h)
                else:
                    heights.append(0)

            for ng in gpu_configs:
                sub = df[(df["n_gpus"] == ng) & (df["n_cells"] == size)]
                if sub.empty:
                    heights.append(0)
                    continue
                h = 0
                for s in phase_steps:
                    col = f"t_{s}"
                    if col in sub.columns:
                        val = sub[col].mean()
                        if not np.isnan(val):
                            h += val
                heights.append(h)

            ax.bar(x_pos, heights, bottom=bottoms, color=phase_color,
                   edgecolor="white", linewidth=0.3, width=0.6,
                   label=phase_name if panel_idx == 0 else None)
            bottoms = [b + h for b, h in zip(bottoms, heights)]

        # Total labels — above each bar, with enough room
        y_max = max(bottoms)
        ax.set_ylim(0, y_max * 1.12)
        for xp, total in zip(x_pos, bottoms):
            # Format large numbers with comma separator
            if total >= 1000:
                label = f"{total:,.0f}s"
            else:
                label = f"{total:.0f}s"
            ax.text(xp, total + y_max * 0.02, label,
                    ha="center", va="bottom", fontsize=7, fontweight="bold")

        ax.set_xticks(x_pos)
        ax.set_xticklabels(x_labels, fontsize=7.5)
        ax.set_xlabel(f"{SIZE_LABELS[size]} cells", fontsize=9)
        if panel_idx == 0:
            ax.set_ylabel("Wall time (seconds)")

    # Legend in rightmost panel
    ax_leg = axes[-1]
    ax_leg.set_axis_off()
    handles, labels = axes[0].get_legend_handles_labels()
    ax_leg.legend(handles, labels, loc="center left", fontsize=7,
                  title="Phase", title_fontsize=8, frameon=False)

    fig.tight_layout()
    fig.subplots_adjust(wspace=0.35)
    fig.savefig(output_dir / "fig6_multigpu_breakdown.png")
    plt.close(fig)
    print("  Figure 6: multi-GPU breakdown saved")


# ---------------------------------------------------------------------------
# Summary table (CSV export for the paper)
# ---------------------------------------------------------------------------

def export_summary_table(df: pd.DataFrame, output_dir: Path) -> None:
    """Export a CSV summary table with mean ± std for each configuration."""
    rows = []
    for (pipe, ncells, ngpus), grp in df.groupby(["pipeline", "n_cells", "n_gpus"]):
        m_time, s_time = _mean_std(grp["total_time"])
        m_ram = grp["peak_ram_gb"].mean()
        m_vram = grp["peak_vram_gb"].mean()
        n_reps = len(grp)
        rows.append({
            "pipeline": pipe,
            "n_cells": ncells,
            "n_gpus": ngpus,
            "n_repeats": n_reps,
            "total_time_mean_s": round(m_time, 1),
            "total_time_std_s": round(s_time, 1),
            "peak_ram_gb": round(m_ram, 1),
            "peak_vram_gb": round(m_vram, 1),
        })

    summary = pd.DataFrame(rows).sort_values(["n_cells", "n_gpus", "pipeline"])
    summary.to_csv(output_dir / "summary_table.csv", index=False)
    print(f"  Summary table: {len(summary)} rows saved to summary_table.csv")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate publication-ready figures for GPU vs CPU benchmark.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--results-dir", type=str, default="results",
        help="Directory containing benchmark JSON files (default: results/)",
    )
    parser.add_argument(
        "--output-dir", type=str, default="figures",
        help="Directory for output figures (default: figures/)",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()
    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading results from: {results_dir}")
    df = load_all_results(results_dir)

    if df.empty:
        print("ERROR: No result files found.")
        raise SystemExit(1)

    print(f"\nDataset sizes: {sorted(df['n_cells'].unique())}")
    print(f"Pipelines: {sorted(df['pipeline'].unique())}")
    print(f"GPU configs: {sorted(df['n_gpus'].unique())}")
    print(f"Total runs: {len(df)}")

    print("\n--- Generating figures ---")

    fig_speedup_heatmap(df, output_dir)
    fig_scaling_plot(df, output_dir)

    concordance = load_concordance(results_dir)
    if concordance:
        fig_concordance(concordance, output_dir)
    else:
        print("  Figure 3: SKIPPED (no concordance_10000_r1.json)")

    fig_memory_profile(df, output_dir)
    fig_timing_breakdown(df, output_dir)
    fig_multigpu_breakdown(df, output_dir)

    print("\n--- Exporting summary table ---")
    export_summary_table(df, output_dir)

    print(f"\nDone! All figures saved to: {output_dir}/")


if __name__ == "__main__":
    main()
