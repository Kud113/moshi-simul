# Bootstrap prompt for Claude Code

Paste the block below as your **first message** to Claude Code in a fresh session
on this repository. It assumes:

- `experiments/jmoshi_long_context/spec.md` exists (drop the spec there first)
- `CLAUDE.md` exists at the repo root
- `.claude/agents/*.md` exist
- You're either inside the devcontainer or in an environment with the same deps

---

## Phase 1 — Scaffold + tests (no real model runs needed)

```text
Read experiments/jmoshi_long_context/spec.md and CLAUDE.md fully.

Implement Phase 1: AC-1 through AC-5 from the spec.

Constraints:
- TDD strictly. For every file you create under experiments/jmoshi_long_context/,
  the matching test in tests/ must exist first and must fail for the right
  reason before the implementation closes it.
- Keep all changes under experiments/jmoshi_long_context/ except for
  docker-compose.ollama.yml (which already exists).
- No cloud APIs. No microphone. No fine-tuning. No Moshi internals touched.
- All external dependencies (CUDA, Ollama at $OLLAMA_BASE_URL, VOICEVOX at
  $VOICEVOX_BASE_URL, the J-Moshi HF model, Open JTalk) must trigger
  pytest.skip with a clear reason when missing, never a hard failure.
- KV policies (DefaultPolicy, NoOpLoggingPolicy, SlidingWindowPolicy,
  RotatingKVPolicy) are placeholders for now. Common interface, selectable by
  config, name appears in logs. No real KV eviction yet.
- run_long_dialogue.py accepts --audio, --script-meta, --config, --hf-repo,
  --out, and writes JSONL + appends to summary.csv even if J-Moshi inference
  is mocked by a placeholder runner.

Workflow:
1. Plan first. List the files you will create/modify in order, then ask me to
   confirm before writing code.
2. After each logical chunk (e.g. "providers + their tests done"), delegate
   to the test-runner sub-agent to run pytest and report.
3. Stop when AC-1 through AC-5 are demonstrably passing (or skipping for the
   right reasons) on this machine. Do not start Phase 2.
```

---

## Phase 2 — Run a real 5-minute evaluation

Use this only after Phase 1 is green and you're on the GPU host.

```text
Phase 1 is complete. Run the first real 5-minute long_context_recall
evaluation end-to-end.

Steps (delegate each to the appropriate sub-agent):

1. script-generator: scenario=long_context_recall, seed=42, provider=ollama,
   model=qwen2.5:32b. Confirm Ollama has the model pulled before starting.

2. tts-synthesizer: engine=auto (prefer VOICEVOX), speaker=3, target_sr from
   the J-Moshi expected rate documented in the project.

3. experiment-runner x3, sequentially on GPU0, with the same WAV:
   - configs/baseline.yaml
   - configs/sliding_window.yaml
   - configs/rotating_kv.yaml

4. policy-comparator with the three run_ids. Write the Markdown report.

5. test-runner once at the end to confirm nothing regressed.

Do not implement real KV eviction in this phase. If baseline fails (OOM,
context overflow, RTF blow-up, or obvious recall failure in the generated
text), surface that finding in the comparator report — that failure is what
unlocks the next phase of work.
```

---

## Notes on the "remote unit tests, local GPU verification" split

- **Claude Code remote / CI / CPU-only env:** runs Phase 1 in full. Every test
  that needs GPU, Ollama, VOICEVOX, or the J-Moshi model should skip with a
  clear reason. The harness's structure, configs, JSONL writers, CLI argument
  parsing, and KV policy abstraction are all testable without a GPU.

- **Local GPU host (3 × 48 GB):** runs Phase 2. Bring up the sidecars first:

  ```bash
  docker compose -f docker-compose.ollama.yml up -d
  docker exec -it ollama ollama pull qwen2.5:32b
  ```

  Then run the Phase 2 prompt. The same `experiments/jmoshi_long_context/tests`
  suite should now have *fewer* skips because the dependencies are present.
