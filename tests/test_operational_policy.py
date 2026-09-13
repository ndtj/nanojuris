from __future__ import annotations

from nanojuris import DEFAULT_OPERATIONAL_POLICY, NanoJurisConfig, OperationalPolicy
from nanojuris.transport import TransportPolicy


def test_fixed_operational_policy_is_conservative_and_serializable() -> None:
    policy = DEFAULT_OPERATIONAL_POLICY
    assert isinstance(policy, OperationalPolicy)
    assert policy.live_cache_ttl_seconds == 600
    assert policy.telemetry_retention_days == 30
    assert policy.min_provider_request_interval_seconds == 2
    assert policy.max_bounded_pages == 3
    assert policy.same_host_parallelism == 1
    assert policy.persist_searchable_corpus is False
    assert policy.persist_raw_full_text is False
    assert policy.to_dict()["curated_default_rollout"] == "opt_in"


def test_config_and_transport_inherit_fixed_live_defaults() -> None:
    config = NanoJurisConfig()
    transport = TransportPolicy(allowed_hosts=("example.test",))
    assert config.rate_limit_interval == 2
    assert config.live_cache_ttl_seconds == 600
    assert config.telemetry_retention_days == 30
    assert config.bounded_probe_max_pages == 3
    assert transport.rate_limit_interval == 2
    assert transport.cache_ttl_seconds == 600
