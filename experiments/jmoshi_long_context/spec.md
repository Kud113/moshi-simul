# J-Moshi Long-Context KV / Window Evaluation Spec

## 1. Purpose

This project evaluates long-context behavior of Japanese Moshi/J-Moshi in long full-duplex spoken dialogue.

The initial goal is **not** to train a new model and **not** to implement a new memory method immediately.

The initial goal is to build a reproducible experiment harness that can answer:

1. Does pretrained J-Moshi break in Japanese conversations longer than 5 minutes?
2. If it breaks, how does it break?
3. Can simple context-window / KV-cache policies improve long-dialogue stability?
4. Is the failure only a generic long-context KV problem, or does full-duplex spoken dialogue require a different retention policy?

---

## 2. Scope

### In scope

- Use a fork of `kyutai-labs/moshi`.
- Install and run J-Moshi from `nu-dialogue/j-moshi` / `nu-dialogue/j-moshi-ext`.
- Generate Japanese test inputs automatically.
- Use local LLM generation via Ollama and optionally Hugging Face Transformers.
- Use free/local TTS to synthesize Japanese input audio.
- Run long input audio through J-Moshi.
- Log runtime, memory, token/cache length, generated text/audio metadata, and failures.
- Compare baseline and simple KV/window policies.
- Use TDD.
- Keep changes isolated under `experiments/jmoshi_long_context/` as much as possible.

### Out of scope for v0

- Fine-tuning J-Moshi.
- Pretraining Moshi/J-Moshi.
- Implementing RMT or memory tokens.
- Implementing a novel KV compression method.
- Manual microphone-based evaluation.
- Cloud API dependency.
- UI-only evaluation without logs.
- Claims about final SOTA performance.

---

## 3. Working Hypothesis

Moshi/J-Moshi can handle local, short-term full-duplex interaction because immediate user input is already streamed into the model.

The unresolved question is whether long conversations fail because the model relies on ordinary Transformer context / KV-cache mechanisms for long-term conversational context.

Therefore, the first experiment should test whether existing context-window or KV-cache policies are sufficient before introducing any new state or memory mechanism.

---

## 4. System Overview

```text
[Ollama or HF local LLM]
        ↓
[Japanese test script]
        ↓
[Local/free TTS]
        ↓
[input.wav]
        ↓
[J-Moshi pretrained]
        ↓
[logs + metrics + generated output]
        ↓
[policy comparison]
```

---

## 5. Repository Layout

Add the following structure:

```text
experiments/
  jmoshi_long_context/
    README.md
    spec.md
    run_baseline.py
    run_long_dialogue.py

    configs/
      baseline.yaml
      sliding_window.yaml
      rotating_kv.yaml
      ollama.yaml
      hf.yaml

    kv_policy.py

    input_generation/
      __init__.py
      providers.py
      scenarios.py
      generate_script.py
      synthesize_tts.py

      generated/
        scripts/
        audio/

    logs/
    outputs/

    tests/
      test_env.py
      test_input_generation.py
      test_long_run.py
      test_kv_policy.py
```

Add this at repository root if using Ollama Docker:

```text
docker-compose.ollama.yml
```

---

## 6. Environment Assumptions

### Hardware

Available hardware:

```text
3 × GPU with 48GB VRAM
```

Suggested allocation:

```text
GPU0: J-Moshi inference / long-dialogue evaluation
GPU1: Ollama or HF script generation
GPU2: spare / parallel run / TTS / future experiments
```

### Software

Minimum assumptions:

```text
Linux
NVIDIA GPU
Docker with NVIDIA runtime
Python environment capable of running moshi
J-Moshi model available via Hugging Face repo
```

J-Moshi target repo:

```text
nu-dialogue/j-moshi-ext
```

Default J-Moshi launch command for manual smoke test:

```bash
python -m moshi.server --hf-repo nu-dialogue/j-moshi-ext
```

---

## 7. Input Generation

Manual input is not used.

All evaluation audio must be generated automatically.

### 7.1 Script generation

Script generation uses local LLM.

Two providers must be supported:

```text
ollama
hf
```

Provider abstraction:

```python
class LLMProvider:
    def generate(self, prompt: str, **kwargs) -> str:
        ...
```

Required implementations:

```text
OllamaProvider
HFTransformersProvider
```

### 7.2 Ollama backend

Requirements:

- Use local Ollama HTTP API.
- Default base URL: `http://localhost:11434`.
- Model name comes from config or CLI.
- No external cloud API calls.
- Save prompt, seed, model name, scenario name, and generated script.

Example:

```bash
docker compose -f docker-compose.ollama.yml up -d
docker exec -it ollama ollama pull qwen2.5:32b
```

Example script generation:

```bash
python experiments/jmoshi_long_context/input_generation/generate_script.py   --provider ollama   --base-url http://localhost:11434   --model qwen2.5:32b   --scenario long_context_recall   --seed 42   --out experiments/jmoshi_long_context/input_generation/generated/scripts/recall_seed42.json
```

### 7.3 Hugging Face backend

Requirements:

- Use `transformers` `AutoModelForCausalLM` / `AutoTokenizer`.
- Model name comes from config or CLI.
- Device can be specified, e.g. `cuda:1`.
- Tests skip if model is unavailable locally.
- No cloud API calls during tests.

Example:

```bash
CUDA_VISIBLE_DEVICES=1 python experiments/jmoshi_long_context/input_generation/generate_script.py   --provider hf   --model <local-or-hf-model-name>   --device cuda:0   --scenario long_context_recall   --seed 42   --out experiments/jmoshi_long_context/input_generation/generated/scripts/recall_seed42.json
```

### 7.4 Generated script JSON

Output format:

```json
{
  "scenario": "long_context_recall",
  "seed": 42,
  "provider": "ollama",
  "model": "qwen2.5:32b",
  "prompt": "...",
  "script": "最初に合言葉を伝えます。合言葉は青い鳥です。..."
}
```

---

## 8. Test Scenarios

Define scenarios in:

```text
experiments/jmoshi_long_context/input_generation/scenarios.py
```

Required scenarios:

### 8.1 long_monologue_5min

Purpose:

```text
Measure whether long continuous Japanese input causes runtime, memory, or context degradation.
```

Structure:

```text
Generate roughly 5 minutes of Japanese spoken text.
No explicit recall task.
```

### 8.2 long_context_recall

Purpose:

```text
Test whether information introduced early in the dialogue remains available after several minutes.
```

Structure:

```text
At the beginning, state a key fact.
Continue unrelated Japanese talk for about 5 minutes.
At the end, ask about the key fact.
```

Example:

```text
合言葉は青い鳥です。
...
さっきの合言葉は何でしたか。
```

### 8.3 interruption_after_long_context

Purpose:

```text
Test whether long-context processing degrades full-duplex interruption handling.
```

Structure:

```text
Long Japanese speech continues.
After several minutes, insert an interruption-like utterance.
Observe whether the system continues incorrectly, stops, or updates.
```

### 8.4 topic_shift

Purpose:

```text
Test whether the system follows explicit topic shifts after a long context.
```

Structure:

```text
Discuss topic A for several minutes.
Explicitly switch to topic B.
Observe whether the model follows topic B or drifts back to topic A.
```

---

## 9. TTS Generation

TTS converts generated Japanese scripts into WAV files.

### Required engines

Support at least one local/free engine.

Preferred order:

```text
1. VOICEVOX
2. Open JTalk
3. pyttsx3 or system fallback
```

### synthesize_tts.py requirements

- Read generated script JSON.
- Synthesize WAV.
- Save WAV metadata JSON.
- Resample to J-Moshi expected sample rate if needed.
- Compute and save duration.
- Warn if duration is less than the target scenario duration.

Output files:

```text
generated/audio/<scenario>_seed<seed>.wav
generated/audio/<scenario>_seed<seed>.meta.json
```

Example metadata:

```json
{
  "script_path": ".../recall_seed42.json",
  "audio_path": ".../recall_seed42.wav",
  "tts_engine": "voicevox",
  "duration_sec": 312.4,
  "sample_rate": 24000
}
```

---

## 10. J-Moshi Evaluation Harness

### run_long_dialogue.py requirements

CLI arguments:

```text
--audio
--script-meta
--config
--hf-repo
--out
```

Default HF repo:

```text
nu-dialogue/j-moshi-ext
```

Minimum behavior:

- Load config.
- Load audio file.
- Run long input through J-Moshi or through a placeholder runner until model integration is complete.
- Log wall time, GPU memory, audio duration, policy name, and run metadata.
- Write JSONL logs.
- Write summary CSV.

---

## 11. KV / Window Policy Interface

Create:

```text
experiments/jmoshi_long_context/kv_policy.py
```

Interface:

```python
class KVPolicy:
    name: str

    def on_step(self, cache, metadata):
        return cache
```

Expected meaning:

```text
cache: model-specific KV cache object
metadata: dict containing step, audio_time_sec, stream info, token info
return: modified cache or unchanged cache
```

Required policies:

```text
DefaultPolicy
NoOpLoggingPolicy
SlidingWindowPolicy
RotatingKVPolicy
```

For v0, policies may be placeholders if Moshi cache internals are not yet accessible.

The first requirement is that policies can be selected, called, and logged through a common interface.

Real KV eviction comes later.

---

## 12. Logging

Each run writes JSONL.

Required event format:

```json
{
  "timestamp": "...",
  "run_id": "...",
  "scenario": "long_context_recall",
  "policy": "baseline",
  "step": 1234,
  "audio_time_sec": 98.4,
  "wall_time_sec": 76.3,
  "gpu_mem_allocated_mb": 12345,
  "gpu_mem_reserved_mb": 16000,
  "kv_tokens": null,
  "rtf": 0.73,
  "event": "generation_step"
}
```

Required metrics:

```text
audio_time_sec
wall_time_sec
real_time_factor
GPU allocated memory
GPU reserved memory
step count
audio token step count if available
text token count if available
KV/cache length if available
generated text if available
crash/OOM/context overflow events
```

---

## 13. Summary Output

For each experiment group, generate:

```text
outputs/summary.csv
```

Columns:

```text
run_id
scenario
policy
duration_sec
max_gpu_mem_mb
avg_rtf
crashed
oom
context_overflow
recall_success
interruption_success
notes
```

For v0, `recall_success` and `interruption_success` may be manually annotated or placeholder fields.

---

## 14. Test-Driven Development

All implementation must begin with tests.

Required tests:

### test_env.py

Acceptance:

- CUDA availability can be checked.
- GPU memory can be logged.
- `moshi` import is checked.
- Tests skip gracefully if GPU or model is unavailable.

### test_input_generation.py

Acceptance:

- Ollama provider test skips if `localhost:11434` is unavailable.
- HF provider test skips if model is unavailable locally.
- Scenario prompt can be produced.
- Script JSON can be written.
- TTS function can be called or skipped if engine unavailable.
- WAV metadata can be written if TTS succeeds.

### test_long_run.py

Acceptance:

- 30-second dummy/audio fixture run does not crash.
- 5-minute metadata path can be accepted.
- JSONL log is created.
- Summary CSV is created.
- GPU memory is logged if CUDA is available.

### test_kv_policy.py

Acceptance:

- All required policies can be instantiated.
- All policies expose `name`.
- `on_step(cache, metadata)` returns without error.
- Policy name appears in logs.

---

## 15. Acceptance Conditions

### AC-1: Repository setup

Pass if:

- `experiments/jmoshi_long_context/` exists.
- `spec.md` exists.
- All required scripts and config directories exist.
- Test suite can be discovered by `pytest`.

### AC-2: Input generation

Pass if:

- A Japanese script JSON can be generated by Ollama when Ollama is running.
- Ollama tests skip cleanly when Ollama is absent.
- HF backend exists and skips cleanly if no local model is available.
- Generated script JSON contains scenario, seed, provider, model, prompt, and script.

### AC-3: TTS generation

Pass if:

- At least one configured local/free TTS engine can synthesize WAV, or tests skip with clear message.
- WAV metadata includes path, engine, duration, and sample rate.
- Audio can be resampled or validated for J-Moshi input.

### AC-4: Baseline J-Moshi run

Pass if:

- `run_long_dialogue.py` accepts a generated WAV.
- The script runs without manual microphone input.
- Logs are written as JSONL.
- Summary CSV is produced.
- GPU memory and wall time are recorded.

### AC-5: KV policy abstraction

Pass if:

- `DefaultPolicy`, `NoOpLoggingPolicy`, `SlidingWindowPolicy`, and `RotatingKVPolicy` are selectable by config.
- Policies run through a common interface.
- Policy name is recorded in logs.
- No core Moshi model modification is required for placeholder policies.

### AC-6: Long-context smoke test

Pass if:

- A 5-minute generated Japanese input can be run through the harness.
- The run either completes or fails with a logged failure reason.
- The output includes max GPU memory, RTF, duration, and policy.

### AC-7: Reproducibility

Pass if:

- Every run stores config, script metadata, TTS metadata, model repo, seed, and logs.
- Same generated script/audio can be reused across policies.
- Output paths are deterministic or include run IDs.

---

## 16. First Codex / Claude Code Prompt

Use this as the first implementation request.

```text
You are working in my fork of kyutai-labs/moshi.

Create a reproducible experiment harness for long-context J-Moshi evaluation.

Do not modify Moshi model internals yet.
Do not implement real KV compression yet.
Do not fine-tune.

Create:
- experiments/jmoshi_long_context/spec.md
- experiments/jmoshi_long_context/README.md
- experiments/jmoshi_long_context/run_baseline.py
- experiments/jmoshi_long_context/run_long_dialogue.py
- experiments/jmoshi_long_context/kv_policy.py
- experiments/jmoshi_long_context/configs/baseline.yaml
- experiments/jmoshi_long_context/configs/sliding_window.yaml
- experiments/jmoshi_long_context/configs/rotating_kv.yaml
- experiments/jmoshi_long_context/input_generation/providers.py
- experiments/jmoshi_long_context/input_generation/scenarios.py
- experiments/jmoshi_long_context/input_generation/generate_script.py
- experiments/jmoshi_long_context/input_generation/synthesize_tts.py
- experiments/jmoshi_long_context/tests/test_env.py
- experiments/jmoshi_long_context/tests/test_input_generation.py
- experiments/jmoshi_long_context/tests/test_long_run.py
- experiments/jmoshi_long_context/tests/test_kv_policy.py
- docker-compose.ollama.yml

Requirements:
1. Use TDD. Write tests first.
2. Keep changes isolated under experiments/jmoshi_long_context unless adding docker-compose.ollama.yml.
3. Add Ollama and Hugging Face provider abstraction for Japanese script generation.
4. Add scenario templates for:
   - long_monologue_5min
   - long_context_recall
   - interruption_after_long_context
   - topic_shift
5. Add local/free TTS wrapper supporting VOICEVOX and Open JTalk if available.
6. All unavailable external services must cause tests to skip gracefully.
7. Add KVPolicy abstraction with placeholder policies:
   - DefaultPolicy
   - NoOpLoggingPolicy
   - SlidingWindowPolicy
   - RotatingKVPolicy
8. run_long_dialogue.py must accept:
   - --audio
   - --script-meta
   - --config
   - --hf-repo
   - --out
9. Write JSONL logs and summary.csv.
10. Do not call cloud APIs.
11. Do not require manual microphone input.
12. Document how to run the tests and a baseline experiment.
```

---

## 17. Second Codex / Claude Code Prompt

Use after AC-1 to AC-5 pass.

```text
Extend the J-Moshi long-context harness to run the first 5-minute generated Japanese evaluation.

Tasks:
1. Generate a long_context_recall script using Ollama.
2. Synthesize it to WAV with the available local TTS engine.
3. Run baseline J-Moshi inference on the generated WAV.
4. Save JSONL logs and summary.csv.
5. Add a short report.md containing:
   - model repo
   - input duration
   - max GPU memory
   - average RTF
   - crash/OOM status
   - any generated text if available
6. Do not implement KV eviction yet.
7. Keep all generated artifacts under experiments/jmoshi_long_context/outputs or input_generation/generated.
```

---

## 18. Non-goals

Do not spend time on these in v0:

```text
- Novel memory architecture
- RMT implementation
- LoRA fine-tuning
- Pretraining
- Human user study
- MOS or subjective naturalness evaluation
- Web UI polishing
- Cloud LLM input generation
```

---

## 19. Current Decision

The immediate next step is:

```text
Build the automated evaluation harness first.
Then verify whether existing J-Moshi fails on 5-minute-plus Japanese generated audio.
Only after observing failure should we implement real KV/window modifications.
```
