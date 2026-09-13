from __future__ import annotations

import os

import pytest

from nanojuris import NanoJurisClient, NanoJurisConfig
from nanojuris.errors import SourceUnavailableError

pytestmark = pytest.mark.skipif(
    os.getenv("NANOJURIS_RUN_LIVE") != "1",
    reason="Set NANOJURIS_RUN_LIVE=1 to query live public sources",
)


@pytest.mark.live
def test_live_stj_open_data_catalog_and_sync_plan_are_metadata_only():
    # The public CKAN catalog can take longer than the generic request
    # timeout under normal load. Keep this live check bounded, but avoid
    # classifying a slow upstream response as an adapter regression.
    client = NanoJurisClient(config=NanoJurisConfig(timeout=45, rate_limit_interval=0.5))
    source = "stj_dados_abertos_jurisprudencia"

    try:
        datasets = client.list_source_datasets(source=source, query="jurisprudencia", rows=20)
    except SourceUnavailableError as exc:
        # A public CKAN timeout is an explicit external-unavailability result,
        # not an empty catalog and not an adapter regression. Keep the live
        # suite honest while allowing the remaining provider checks to run.
        pytest.skip(f"STJ public CKAN unavailable: {exc}")

    assert datasets
    dataset_id = datasets[0]["name"]
    description = client.describe_source_dataset(source=source, dataset_id=dataset_id)
    plan = client.plan_source_sync(source=source, dataset_id=dataset_id, format="JSON")

    assert description["source"] == source
    assert description["resources"]
    assert plan["download"] is False
    assert plan["source"] == source
