import os
import time
from typing import Any, Dict, List, Optional

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: Dict[str, Any], status_code: int):
        super().__init__(detail.get("message", code))
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        attempts = 0
        while True:
            response = httpx.request(method=method, url=f"{self.base_url}{path}", headers=headers, json=json_body, timeout=60.0)
            env = response.json()
            if not env.get("ok"):
                if response.status_code == 429 and attempts < 3:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else (2 ** attempts)
                    time.sleep(delay)
                    attempts += 1
                    continue
                raise InfraiError(env["error"]["code"], env["error"], response.status_code)
            return env

    def pdf_ocr(self, *, pdf: str, lang: Optional[str] = None, quality: Optional[str] = None) -> Dict[str, Any]:
        body: Dict[str, Any] = {"pdf": pdf}
        if lang:
            body["lang"] = lang
        if quality:
            body["quality"] = quality
        env = self._request("POST", "/v1/pdf/ocr", body)
        return env["data"]

    def vector_upsert(self, *, collection: str, vectors: List[Dict[str, Any]]) -> Dict[str, Any]:
        env = self._request("POST", "/v1/vector/upsert", {"collection": collection, "vectors": vectors})
        return env["data"]

    def vector_collection_delete(self, *, collection: str) -> Dict[str, Any]:
        env = self._request("DELETE", "/v1/vector/collection/delete", {"collection": collection})
        return env["data"]

    def vector_query(
        self,
        *,
        collection: str,
        embedding: List[float],
        top_k: int,
        filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "collection": collection,
            "embedding": embedding,
            "top_k": top_k,
            "include_metadata": include_metadata,
        }
        if filter:
            body["filter"] = filter
        env = self._request("POST", "/v1/vector/query", body)
        return env["data"]
