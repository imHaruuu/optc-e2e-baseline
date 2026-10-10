#!/bin/bash
# Goi newrun.py cua worktree nhung ghi vao results/ cua repo goc; run.json ghi commit cua worktree (--code).
W="E:/Code/optc-e2e-baseline/.claude/worktrees/optc-file-analysis-305df4/optc-explain-pack"
"E:/Code/optc-e2e-baseline/optc-explain-pack/.venv/Scripts/python.exe" -c "
import sys; from pathlib import Path
sys.path.insert(0, r'$W'); import newrun
newrun.RESULTS = Path(r'E:/Code/optc-e2e-baseline/optc-explain-pack/results')
newrun.main(sys.argv[1:] + ['--code', r'$W'])" "$@"
