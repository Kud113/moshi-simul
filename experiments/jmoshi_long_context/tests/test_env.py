"""Environment checks (AC-1, spec §6 / §14).

These tests verify that the harness can introspect the runtime (CUDA, GPU
memory, ``moshi`` import) without ever hard-failing when the GPU or model is
unavailable. On a host that lacks them the tests skip with a clear reason.
"""

import importlib.util
import logging

import pytest


def _have(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def test_cuda_availability_is_checkable():
    if not _have("torch"):
        pytest.skip("torch not installed in this environment")
    import torch

    available = torch.cuda.is_available()
    assert isinstance(available, bool)


def test_gpu_memory_can_be_logged(caplog):
    if not _have("torch"):
        pytest.skip("torch not installed in this environment")
    import torch

    if not torch.cuda.is_available():
        pytest.skip("CUDA not available on this host")

    log = logging.getLogger("jmoshi_long_context.env")
    with caplog.at_level(logging.INFO):
        allocated_mb = torch.cuda.memory_allocated() / (1024**2)
        reserved_mb = torch.cuda.memory_reserved() / (1024**2)
        log.info(
            "gpu_mem_allocated_mb=%.1f gpu_mem_reserved_mb=%.1f",
            allocated_mb,
            reserved_mb,
        )

    assert allocated_mb >= 0.0
    assert reserved_mb >= 0.0
    assert "gpu_mem_allocated_mb" in caplog.text


def test_moshi_import_is_checked():
    if not _have("moshi"):
        pytest.skip("moshi not importable in this environment")
    import moshi

    assert moshi is not None
