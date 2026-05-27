"""KV / window policy abstraction (spec §11).

Defines a common interface for context-window / KV-cache retention policies
plus four placeholder implementations. The first requirement (AC-5) is that
policies can be *selected, called, and logged* through one interface — not
that they perform real eviction.

For v0 every policy is a no-op: ``on_step`` returns the cache unchanged. Real
KV eviction is deliberately deferred until a long-context failure is observed
(AC-6), per CLAUDE.md. Subclasses may record their intent in logs, but must
not mutate or replace the cache object.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Type

logger = logging.getLogger("jmoshi_long_context.kv_policy")


class KVPolicy:
    """Base policy. Selectable by ``name``, called via ``on_step``.

    Parameters
    ----------
    logger:
        Optional logger; defaults to the module logger so the policy name is
        always recorded somewhere observable.
    **config:
        Arbitrary policy knobs (e.g. ``window_size``). Stored on ``config`` and
        surfaced by :meth:`describe` for reproducibility / logging.
    """

    name: str = "kv_policy"

    def __init__(self, logger: Optional[logging.Logger] = None, **config: Any):
        self._logger = logger if logger is not None else globals()["logger"]
        self.config: Dict[str, Any] = dict(config)

    def on_step(self, cache: Any, metadata: Optional[Dict[str, Any]] = None) -> Any:
        """Hook called once per generation step.

        ``cache`` is the model-specific KV cache, ``metadata`` carries step /
        audio_time_sec / token info. Returns the (here, unchanged) cache.
        """
        step = (metadata or {}).get("step")
        self._logger.debug("kv_policy=%s step=%s (placeholder no-op)", self.name, step)
        return cache

    def describe(self) -> Dict[str, Any]:
        """Reproducibility record: policy name plus its config knobs."""
        return {"policy": self.name, **self.config}

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"{type(self).__name__}(name={self.name!r}, config={self.config!r})"


class DefaultPolicy(KVPolicy):
    """Baseline: do nothing, keep the full cache (the control condition)."""

    name = "default"


class NoOpLoggingPolicy(KVPolicy):
    """Like the baseline, but logs every step at INFO for observability."""

    name = "noop_logging"

    def on_step(self, cache: Any, metadata: Optional[Dict[str, Any]] = None) -> Any:
        meta = metadata or {}
        self._logger.info(
            "kv_policy=%s step=%s audio_time_sec=%s kv_tokens=%s",
            self.name,
            meta.get("step"),
            meta.get("audio_time_sec"),
            meta.get("kv_tokens"),
        )
        return cache


class SlidingWindowPolicy(KVPolicy):
    """Placeholder for a fixed-size sliding context window.

    Records the *intended* window size but performs no eviction in v0.
    """

    name = "sliding_window"

    def on_step(self, cache: Any, metadata: Optional[Dict[str, Any]] = None) -> Any:
        meta = metadata or {}
        self._logger.debug(
            "kv_policy=%s step=%s window_size=%s (placeholder, no eviction)",
            self.name,
            meta.get("step"),
            self.config.get("window_size"),
        )
        return cache


class RotatingKVPolicy(KVPolicy):
    """Placeholder for a rotating / ring-buffer KV cache.

    Records the *intended* capacity but performs no rotation in v0.
    """

    name = "rotating_kv"

    def on_step(self, cache: Any, metadata: Optional[Dict[str, Any]] = None) -> Any:
        meta = metadata or {}
        self._logger.debug(
            "kv_policy=%s step=%s capacity=%s (placeholder, no rotation)",
            self.name,
            meta.get("step"),
            self.config.get("capacity"),
        )
        return cache


# Config-name -> policy class. "baseline" is an alias for the baseline.yaml
# config, which uses the DefaultPolicy control condition.
POLICY_REGISTRY: Dict[str, Type[KVPolicy]] = {
    "default": DefaultPolicy,
    "baseline": DefaultPolicy,
    "noop_logging": NoOpLoggingPolicy,
    "sliding_window": SlidingWindowPolicy,
    "rotating_kv": RotatingKVPolicy,
}


def get_policy(name: str, **config: Any) -> KVPolicy:
    """Instantiate a policy by config name (case-insensitive).

    Raises ``KeyError`` for unknown names, listing the valid options.
    """
    key = str(name).strip().lower()
    try:
        cls = POLICY_REGISTRY[key]
    except KeyError:
        valid = ", ".join(sorted(POLICY_REGISTRY))
        raise KeyError(f"unknown KV policy {name!r}; valid options: {valid}") from None
    return cls(**config)


def available_policies() -> Dict[str, Type[KVPolicy]]:
    """Return a copy of the config-name -> policy-class registry."""
    return dict(POLICY_REGISTRY)
