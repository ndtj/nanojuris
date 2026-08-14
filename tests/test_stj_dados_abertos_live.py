from __future__ import annotations

import os

import pytest

from nanojuris import NanoJurisClient

pytestmark = pytest.mark.skipif(
    os.getenv("NANOJURIS_RUN_LIVE") != "1",
    reason="Set NANOJURIS_RUN_LIVE=1 to query live public sources",
)


@pytest.mark.live
def test_live_stj_open_data_catalog_and_sync_plan_are_metadata_only():
    client = NanoJurisClient()
    source = "stj_dados_abertos_jurisprudencia"

    datasets = client.list_source_datasets(source=source, query="jurisprudencia", rows=20)

    assert datasets
    dataset_id = datasets[0]["name"]
    description = client.describe_source_dataset(source=source, dataset_id=dataset_id)
    plan = client.plan_source_sync(source=source, dataset_id=dataset_id, format="JSON")

    assert description["source"] == source
    assert description["resources"]
    assert plan["download"] is False
    assert plan["source"] == source
