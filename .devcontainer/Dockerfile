# Base: CUDA + cuDNN with development headers. Moshi pulls PyTorch via pip.
# Bumping the patch tag is safe; bumping the major CUDA version requires checking
# moshi / torchaudio compatibility.
FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

ARG USER_UID=1000
ARG USER_GID=1000

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System packages:
#   - python3.10 (Moshi's tested version) + venv + headers
#   - build-essential + ffmpeg + libsndfile1 + sox: audio I/O & encoding
#   - open-jtalk + HTS voice: free local Japanese TTS fallback
#   - git, curl, ca-certificates: scripts & HF Hub
#   - locales: ensure UTF-8 for Japanese text
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3.10 python3.10-venv python3.10-dev python3-pip \
      build-essential pkg-config \
      git curl wget ca-certificates gnupg \
      ffmpeg libsndfile1 sox \
      open-jtalk open-jtalk-mecab-naist-jdic hts-voice-nitech-jp-atr503-m001 \
      locales tzdata \
      jq tmux htop \
    && sed -i 's/^# *\(ja_JP.UTF-8\)/\1/' /etc/locale.gen \
    && locale-gen \
    && rm -rf /var/lib/apt/lists/*

# Non-root user matches the host UID/GID so bind-mounted files keep correct ownership.
RUN groupadd --gid ${USER_GID} vscode \
 && useradd  --uid ${USER_UID} --gid ${USER_GID} -m -s /bin/bash vscode \
 && mkdir -p /workspace /opt/venv /opt/hf-cache /opt/torch-cache \
 && chown -R vscode:vscode /workspace /opt/venv /opt/hf-cache /opt/torch-cache

USER vscode
WORKDIR /workspace

# A dedicated venv keeps the project deps isolated from system Python
# and is friendlier to Claude Code re-running `pip install` in the same shell.
RUN python3.10 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}" \
    VIRTUAL_ENV=/opt/venv

# Pin baseline tooling. Moshi-specific deps are installed by post-create.sh
# so they live in a layer the user controls.
RUN pip install --upgrade pip setuptools wheel \
 && pip install \
      "torch==2.5.1" "torchaudio==2.5.1" --index-url https://download.pytorch.org/whl/cu124 \
 && pip install \
      "transformers>=4.45" \
      "accelerate>=1.0" \
      "huggingface_hub[hf_transfer]>=0.26" \
      "sentencepiece" \
      "soundfile>=0.12" \
      "librosa>=0.10" \
      "numpy<2.0" \
      "pyyaml" \
      "click" \
      "rich" \
      "pytest>=8" "pytest-asyncio" "pytest-timeout" \
      "ruff" "mypy" \
      "requests" "httpx" \
      "pandas" \
      "ollama"

CMD ["/bin/bash", "-l"]
