from unittest.mock import Mock, patch

import pytest

from service import demo_ingest


def test_demo_deletes_its_collection_when_ingest_fails() -> None:
    infrai = Mock()
    infrai.vector_collection_delete.side_effect = [
        {"collection": "demo-collection", "deleted": 1},
        {"collection": "demo-collection", "deleted": 0},
    ]
    pipeline = Mock()
    pipeline.ingest_work_order.side_effect = RuntimeError("ingest failed")

    with (
        patch.object(demo_ingest, "InfraiClient", return_value=infrai),
        patch.object(demo_ingest, "EmbeddingIndex"),
        patch.object(demo_ingest, "FieldServicePipeline", return_value=pipeline),
        pytest.raises(RuntimeError, match="ingest failed"),
    ):
        demo_ingest.main()

    collection = pipeline.ingest_work_order.call_args.args[0].collection
    assert collection.startswith("field-service-work-orders-demo-")
    assert infrai.vector_collection_delete.call_count == 2
    infrai.vector_collection_delete.assert_called_with(collection=collection)
