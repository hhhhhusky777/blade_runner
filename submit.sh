#!/usr/bin/env bash
# Defaults to a read-only check. Only --submit-one / --loop create or submit.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd -- "$project_dir/game_solver"
export PYTHONDONTWRITEBYTECODE=1
if [[ -x "$project_dir/game_solver/.venv/bin/python" ]]; then
  exec "$project_dir/game_solver/.venv/bin/python" -m solver.runner "$@"
fi
exec uv run --frozen --project "$project_dir/game_solver" python -m solver.runner "$@"
