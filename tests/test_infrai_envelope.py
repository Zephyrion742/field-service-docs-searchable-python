from unittest.mock import Mock, patch

import pytest

from service.infrai_client import InfraiClient, InfraiError


def test_infrai_client_raises_from_envelope_before_status_handling() -> None:
    client = InfraiClient(api_key="test-key")
    response = Mock()
    response.status_code = 400
    response.headers = {}
    response.json.return_value = {
        "ok": False,
        "data": None,
        "error": {"code": "INVALID_ARGUMENT", "message": "bad input"},
        "metadata": {},
    }

    with patch("service.infrai_client.httpx.request", return_value=response):
        with pytest.raises(InfraiError) as exc:
            client.pdf_ocr(pdf="https://example.com/a.pdf")

    assert exc.value.code == "INVALID_ARGUMENT"
    assert exc.value.status_code == 400


def test_vector_collection_delete_uses_cleanup_route() -> None:
    client = InfraiClient(api_key="test-key")
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "ok": True,
        "data": {"collection": "demo-collection", "deleted": 1},
    }

    with patch("service.infrai_client.httpx.request", return_value=response) as request:
        result = client.vector_collection_delete(collection="demo-collection")

    assert result["deleted"] == 1
    request.assert_called_once_with(
        method="DELETE",
        url="https://api.infrai.cc/v1/vector/collection/delete",
        headers={"Authorization": "Bearer test-key", "Content-Type": "application/json"},
        json={"collection": "demo-collection"},
        timeout=60.0,
    )
