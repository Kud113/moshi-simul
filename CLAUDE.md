# Project Guide for Claude Code

This is a fork of `kyutai-labs/moshi`. The work for **this** project lives entirely
under `experiments/jmoshi_long_context/` (plus `docker-compose.ollama.yml` at repo
root). **Do not modify Moshi model internals** unless explicitly asked.

The full specification is at `experiments/jmoshi_long_context/spec.md`. Read it
once at the start of every fresh session. The summary below is just orientation.

---

## What we are building

A reproducible evaluation harness that answers: *does pretrained J-Moshi break
in Japanese full-duplex conversations longer than 5 minutes, and do simple
KV/window policies help?*

Out of scope for v0: fine-tuning, novel memory architectures, MOS evaluation.

---

## Environment (already provisioned by the devcontainer)

You are running inside a CUDA 12.4 / PyTorch 2.5 container with:

- **Repo root bind-mounted at `/workspace`.** Host edits are live in the
  container; nothing is baked into the image. `moshi` is installed editable
  (`pip install -e ./moshi`) from this bind mount.
- **3 × 48 GB GPUs.** Default allocation: GPU0 = J-Moshi, GPU1 = Ollama,
  GPU2 = spare/VOICEVOX. Honor this allocation in configs and CLI flags.
- **Ollama** and **VOICEVOX** run as **independent containers** (managed
  separately, not part of this devcontainer), reached over `--network=host` at
  `$OLLAMA_BASE_URL` (default `http://localhost:11434`) and `$VOICEVOX_BASE_URL`
  (default `http://localhost:50021`). They may even run outside Docker — only
  the URLs matter.
- **Open JTalk** installed as a fallback TTS at `/usr/bin/open_jtalk`
- HuggingFace caches at `/opt/hf-cache`, torch caches at `/opt/torch-cache`
  (Docker-managed named volumes, outside the bind-mounted repo).

If a sidecar is unreachable, the relevant tests must `pytest.skip(...)` with a
clear message — never hard-fail.

The sidecars are started independently (each can be brought up on its own):

```bash
docker compose -f docker-compose.ollama.yml up -d ollama    # or: up -d voicevox
docker exec -it ollama ollama pull qwen2.5:32b
```

---

## Repository layout (target — create what's missing)

```
experiments/jmoshi_long_context/
  spec.md                 # source of truth
  README.md
  run_baseline.py
  run_long_dialogue.py
  kv_policy.py
  configs/
    baseline.yaml
    sliding_window.yaml
    rotating_kv.yaml
    ollama.yaml
    hf.yaml
  input_generation/
    __init__.py
    providers.py          # OllamaProvider, HFTransformersProvider
    scenarios.py          # 4 scenarios per spec §8
    generate_script.py
    synthesize_tts.py
    generated/{scripts,audio}/
  logs/                   # JSONL per run
  outputs/                # summary.csv per sweep
  tests/
    test_env.py
    test_input_generation.py
    test_long_run.py
    test_kv_policy.py
```

---

## Working rules

1. **TDD.** Write or extend the relevant test in `experiments/jmoshi_long_context/tests/`
   **before** the implementation. A change without a covering test is incomplete.
2. **Isolation.** All new files go under `experiments/jmoshi_long_context/` except
   `docker-compose.ollama.yml`. If you think you need to touch Moshi internals,
   stop and ask.
3. **No cloud APIs.** No OpenAI, no Anthropic API calls for script generation.
   Local Ollama or local HF only.
4. **No microphone.** All inputs come from generated WAV files.
5. **Skip gracefully.** Tests must skip (not fail) when GPU / Ollama / VOICEVOX
   / J-Moshi model is unavailable, with a message naming what's missing.
6. **Reproducibility.** Every run writes the config, seed, model repo, script
   metadata, TTS metadata, and logs to a run-id-stamped directory under
   `experiments/jmoshi_long_context/outputs/`.
7. **Logging format.** JSONL with the fields in spec §12. Summary CSV with the
   columns in spec §13. Don't invent your own.

---

## Sub-agents available

Seven specialists live in `.claude/agents/`. **You** (the main session) are the
orchestrator — sub-agents cannot call other sub-agents. Delegate explicitly:

| Agent | When to use |
|---|---|
| `test-runner` | After any code change, or when the user says "run tests". |
| `script-generator` | To produce a Japanese script JSON for a scenario. |
| `tts-synthesizer` | To turn a script JSON into a WAV + metadata JSON. |
| `experiment-runner` | To run `run_long_dialogue.py` for one (config, audio) pair. |
| `policy-comparator` | After a sweep, to diff summary.csv across policies. |
| `progress-digest` | To regenerate `STATUS.md` from git history + spec §15 AC progress (read from claude.ai chat). |
| `moshi-explainer` | To draft/verify `docs/moshi-internals.md` from the Moshi source under `moshi/`. |

### Standard orchestration recipe

When the user says something like *"run the 5-minute long_context_recall eval
across all policies"*:

1. Delegate to **`script-generator`** with `scenario=long_context_recall`,
   `seed=42`, `provider=ollama`, `model=qwen2.5:32b`. Capture the output JSON path.
2. Delegate to **`tts-synthesizer`** with that script path. Capture WAV +
   metadata paths.
3. For each policy in {`baseline`, `sliding_window`, `rotating_kv`}, delegate to
   **`experiment-runner`** with the same WAV, that policy's config, and a unique
   `run_id`. Run them sequentially on GPU0 unless the user asks for parallel.
4. Delegate to **`policy-comparator`** with the list of `run_id`s. Surface its
   report to the user.
5. Finally, delegate to **`test-runner`** if any code changed during the sweep.

Spawn sub-agents in parallel via the Task tool whenever steps are independent
(e.g. generating scripts for 4 different scenarios at once).

---

## Common commands (also in Makefile)

```bash
# Tests
pytest experiments/jmoshi_long_context/tests -q

# Lint / format
ruff check experiments/jmoshi_long_context
ruff format experiments/jmoshi_long_context

# One-shot baseline
python -m experiments.jmoshi_long_context.run_long_dialogue \
  --config experiments/jmoshi_long_context/configs/baseline.yaml \
  --audio  experiments/jmoshi_long_context/input_generation/generated/audio/recall_seed42.wav \
  --script-meta experiments/jmoshi_long_context/input_generation/generated/scripts/recall_seed42.json \
  --hf-repo $JMOSHI_HF_REPO \
  --out    experiments/jmoshi_long_context/outputs/baseline_recall_seed42
```

---

## What "done" looks like for the current phase

Acceptance criteria are in spec §15 (AC-1 through AC-7). The current target is
**AC-1 → AC-5**: scaffold + tests + KV policy abstraction with placeholder
policies. **Do not implement real KV eviction until AC-6 has produced an
observed failure** worth fixing.
