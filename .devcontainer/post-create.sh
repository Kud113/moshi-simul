#!/usr/bin/env bash
# Runs once after the devcontainer is first built / rebuilt.
# Idempotent: safe to re-run.

set -euo pipefail

echo "==> post-create.sh"
echo "==> Python: $(python --version) at $(which python)"
echo "==> CUDA visible to PyTorch:"
python - <<'PY'
import torch
print(f"  torch              : {torch.__version__}")
print(f"  torch.cuda.is_available(): {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"  device_count       : {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        p = torch.cuda.get_device_properties(i)
        print(f"  GPU{i}: {p.name}  {p.total_memory/1024**3:.1f} GiB")
PY

# Install Moshi from the local fork (editable). This repo IS the moshi source
# of truth and diverges from upstream, so we never pull from PyPI. Runs from the
# bind-mounted root (/workspace); egg-info lands in ./moshi and is gitignored.
echo "==> Installing moshi (editable) from ./moshi"
pip install -e ./moshi

# Ollama Python client (already in Dockerfile, but ensure latest behaviour).
pip install --upgrade ollama >/dev/null

# Pre-create the experiment tree if missing. The harness lives entirely under
# experiments/jmoshi_long_context/ per spec section 2.
mkdir -p \
  experiments/jmoshi_long_context/{configs,input_generation/{generated/{scripts,audio}},logs,outputs,tests} \
  experiments/jmoshi_long_context/input_generation

# Smoke check: can we reach the sidecars?
echo "==> Reachability check"
for url in "${OLLAMA_BASE_URL:-http://localhost:11434}/api/tags" \
           "${VOICEVOX_BASE_URL:-http://localhost:50021}/version"; do
  if curl -fsS --max-time 2 "${url}" >/dev/null 2>&1; then
    echo "  OK   ${url}"
  else
    echo "  MISS ${url}   (start with: docker compose -f docker-compose.ollama.yml up -d)"
  fi
done

echo "==> Done. Try: claude   or:   pytest experiments/jmoshi_long_context/tests -q"
