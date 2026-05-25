# J-Moshi long-context evaluation — Claude Code scaffolding

This bundle is **scaffolding only**. It contains no implementation code for the
J-Moshi evaluation harness. The point is to drop these files into your fork of
`kyutai-labs/moshi`, then let Claude Code write the implementation against the
spec.

## What's in here

```
.devcontainer/
  devcontainer.json     # CUDA 12.4 + Python 3.10 + claude-code feature, --gpus=all
  Dockerfile            # PyTorch 2.5, audio libs, Open JTalk Japanese voice
  post-create.sh        # installs moshi, prints CUDA + sidecar status
docker-compose.ollama.yml  # Ollama (GPU1) + VOICEVOX sidecars
CLAUDE.md               # the project guide Claude Code reads on every session
.claude/agents/
  test-runner.md
  script-generator.md
  tts-synthesizer.md
  experiment-runner.md
  policy-comparator.md
prompts/
  bootstrap.md          # what to paste as Claude Code's first message
```

## How to drop this into your repo

```bash
# from your fork's root
cp -r jmoshi-claude-setup/.devcontainer ./
cp -r jmoshi-claude-setup/.claude       ./
cp    jmoshi-claude-setup/docker-compose.ollama.yml ./
cp    jmoshi-claude-setup/CLAUDE.md     ./
mkdir -p prompts && cp jmoshi-claude-setup/prompts/bootstrap.md prompts/
mkdir -p experiments/jmoshi_long_context
cp spec.md experiments/jmoshi_long_context/spec.md   # your existing spec
git add .devcontainer .claude docker-compose.ollama.yml CLAUDE.md prompts experiments/jmoshi_long_context/spec.md
git commit -m "Add Claude Code scaffolding for J-Moshi long-context eval"
```

## The intended workflow

You described this as: **Claude Code writes the code partway → unit tests run
in Claude Code's remote env → verification runs on the local GPU host.**

That maps cleanly onto two phases (see `prompts/bootstrap.md`):

### Phase 1 — runs anywhere, including CPU-only remote

What Claude Code produces in Phase 1 is testable without GPU / Ollama /
VOICEVOX / J-Moshi:
- CLI argument parsing
- Provider abstraction (`OllamaProvider`, `HFTransformersProvider`)
- Scenario templates
- KV policy interface + placeholder policies
- JSONL writer + summary CSV writer
- Test files that skip-gracefully when a dependency is missing

You run Phase 1 with Claude Code in whatever env you've got. Every test that
needs an external dependency uses `pytest.skip(...)` with a specific reason, so
the suite returns "N passed, M skipped (...)" and nothing actually red.

### Phase 2 — runs on the GPU host only

```bash
# on the GPU box
docker compose -f docker-compose.ollama.yml up -d
docker exec -it ollama ollama pull qwen2.5:32b

# open the repo in VSCode + Dev Containers, or:
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . claude
```

Then paste the Phase 2 prompt. The same test suite from Phase 1 now has *fewer*
skips because the dependencies are present, and Claude Code orchestrates the
five sub-agents to run a real 5-minute eval.

## Why one devcontainer for both envs

The `.devcontainer/` config is identical for local and remote. CUDA flags like
`--gpus=all` are harmless when no GPU is attached — the container just starts
without GPU access, and `torch.cuda.is_available()` returns False, which the
tests already handle. So the same image runs unit tests in a CPU-only remote
and full experiments on the GPU host.

If your Claude Code remote env doesn't honor devcontainers at all and just
gives you a plain shell, the `.claude/agents/` and `CLAUDE.md` still work —
they are pure Markdown and don't depend on the container. You'd just need to
`pip install -r` the deps from the Dockerfile manually in that env.

## Where the spec lives

This bundle assumes `experiments/jmoshi_long_context/spec.md` is the source of
truth in your repo. `CLAUDE.md` references it explicitly and Phase 1's prompt
tells Claude Code to read it before writing anything.

If you change the spec, you do not need to change anything in this bundle —
the agents and CLAUDE.md defer to the spec for all behavioral details.
