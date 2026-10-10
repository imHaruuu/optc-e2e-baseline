#!/bin/bash
cd E:/Code/optc-e2e-baseline/optc-explain-pack
export PYTHONIOENCODING=utf-8 HF_HUB_OFFLINE=1 HF_HUB_DISABLE_SYMLINKS_WARNING=1
.venv/Scripts/python.exe results/_runners/run_task21.py "$@" >> results/adgen/task21_small_models/logs/runner.out 2>&1
