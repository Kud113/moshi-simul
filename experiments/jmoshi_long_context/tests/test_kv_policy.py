"""KV/window policy abstraction (AC-5, spec §11 / §14).

For v0 every policy is a placeholder: it must run through the common
``on_step(cache, metadata)`` interface, expose a ``name``, be selectable by
config name, and record its name in logs — but it must NOT mutate or replace
the cache (no real eviction until a failure is observed, per CLAUDE.md).
"""

import logging

import pytest

import kv_policy as kvp

REQUIRED_POLICIES = [
    "DefaultPolicy",
    "NoOpLoggingPolicy",
    "SlidingWindowPolicy",
    "RotatingKVPolicy",
]


@pytest.fixture
def metadata():
    return {
        "step": 7,
        "audio_time_sec": 12.5,
        "kv_tokens": None,
        "run_id": "test-run",
    }


def _policy_classes():
    return [getattr(kvp, name) for name in REQUIRED_POLICIES]


def test_required_policies_exist():
    for name in REQUIRED_POLICIES:
        assert hasattr(kvp, name), f"missing policy class {name}"


@pytest.mark.parametrize("name", REQUIRED_POLICIES)
def test_policy_instantiates_and_exposes_name(name):
    policy = getattr(kvp, name)()
    assert isinstance(policy.name, str)
    assert policy.name


def test_policy_names_are_unique():
    names = [cls().name for cls in _policy_classes()]
    assert len(names) == len(set(names))


@pytest.mark.parametrize("name", REQUIRED_POLICIES)
def test_on_step_returns_cache_unchanged(name, metadata):
    policy = getattr(kvp, name)()
    sentinel = {"kv": [1, 2, 3]}
    # Placeholder policies must not evict / replace the cache object.
    assert policy.on_step(sentinel, metadata) is sentinel


@pytest.mark.parametrize("name", REQUIRED_POLICIES)
def test_on_step_accepts_none_cache_and_metadata(name):
    policy = getattr(kvp, name)()
    assert policy.on_step(None) is None
    assert policy.on_step(None, None) is None


@pytest.mark.parametrize("name", REQUIRED_POLICIES)
def test_policy_name_appears_in_logs(name, metadata, caplog):
    policy = getattr(kvp, name)()
    with caplog.at_level(logging.DEBUG):
        policy.on_step({"kv": []}, metadata)
    assert policy.name in caplog.text


def test_get_policy_selects_by_config_name():
    mapping = {
        "default": kvp.DefaultPolicy,
        "baseline": kvp.DefaultPolicy,
        "noop_logging": kvp.NoOpLoggingPolicy,
        "sliding_window": kvp.SlidingWindowPolicy,
        "rotating_kv": kvp.RotatingKVPolicy,
    }
    for config_name, cls in mapping.items():
        policy = kvp.get_policy(config_name)
        assert isinstance(policy, cls)
        assert isinstance(policy.name, str)


def test_get_policy_is_case_insensitive():
    assert isinstance(kvp.get_policy("Sliding_Window"), kvp.SlidingWindowPolicy)


def test_get_policy_unknown_name_raises():
    with pytest.raises((KeyError, ValueError)):
        kvp.get_policy("does_not_exist")


def test_get_policy_forwards_kwargs_to_config():
    policy = kvp.get_policy("sliding_window", window_size=128)
    assert policy.config.get("window_size") == 128


def test_describe_includes_policy_name():
    policy = kvp.get_policy("rotating_kv", capacity=2048)
    described = policy.describe()
    assert described["policy"] == policy.name
    assert described.get("capacity") == 2048
