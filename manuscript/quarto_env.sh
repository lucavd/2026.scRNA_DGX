#!/usr/bin/env bash
# Source this before calling quarto in the conda 'docbuild' env.
# The conda-forge quarto build on arm64 mis-detects tool paths; these overrides fix it.
: "${CONDA_PREFIX:?activate the docbuild env first}"
export QUARTO_SHARE_PATH="$CONDA_PREFIX/share/quarto"
export QUARTO_DENO="$CONDA_PREFIX/bin/deno"
export QUARTO_DENO_DOM="$CONDA_PREFIX/lib/deno_dom.dylib"
export QUARTO_DART_SASS="$CONDA_PREFIX/bin/sass"
export QUARTO_ESBUILD="$CONDA_PREFIX/bin/esbuild"
export QUARTO_TYPST="$CONDA_PREFIX/bin/typst"
export QUARTO_PANDOC="$CONDA_PREFIX/bin/pandoc"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/tmp/qcache}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-/tmp/qdata}"
mkdir -p "$XDG_CACHE_HOME" "$XDG_DATA_HOME"
