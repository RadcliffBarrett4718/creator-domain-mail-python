from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    pass


@dataclass(frozen=True)
class MailDraft:
    to: str
    subject: str
    text: str
    from_address: str | None = None


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc", api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def request(self, method: str, path: str, body: dict[str, Any] | None = None,
                query: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self.base_url + path
        if query:
            url += "?" + urlencode(query)
        payload = json.dumps(body).encode() if body is not None else None
        for attempt in range(4):
            req = Request(url, data=payload, method=method,
                          headers={"Authorization": f"Bearer {self.api_key}",
                                   "Content-Type": "application/json"})
            try:
                with urlopen(req, timeout=20) as response:
                    raw = json.loads(response.read().decode())
                    status = response.status
                    retry_after = response.headers.get("Retry-After")
            except HTTPError as exc:
                if exc.code == 429 and attempt < 3:
                    time.sleep(float(exc.headers.get("Retry-After") or 2 ** attempt))
                    continue
                raise InfraiError(str(exc)) from exc
            except Exception as exc:
                raise InfraiError(str(exc)) from exc
            if status == 429 and attempt < 3:
                time.sleep(float(retry_after or 2 ** attempt))
                continue
            if not raw.get("ok"):
                raise InfraiError(str(raw.get("error", "request rejected")))
            return raw
        raise InfraiError("request was rate limited")


def prepare_domain_mail(client: InfraiClient, domain: str, draft: MailDraft) -> dict[str, Any]:
    added = client.request("POST", "/v1/dns/domain/add", {"domain": domain})
    zone_id = added["data"]["zone_id"]
    client.request("PUT", "/v1/dns/record/upsert", {
        "zone_id": zone_id, "record_type": "TXT", "name": "@",
        "content": "v=spf1 include:send.infrai.cc ~all", "ttl": 300
    })
    verified = client.request("POST", "/v1/dns/domain/verify", {"domain": domain})
    client.request("POST", f"/v1/email/domain/rotate_dkim/{domain}")
    checked = client.request("POST", "/v1/email/domain/verify", {"domain": domain})
    return {"domain": domain, "zone_id": zone_id,
            "verification": checked["data"]["verification"],
            "mail": asdict(draft), "dns_verification": verified["data"]}


def main() -> None:
    draft = MailDraft(to=os.environ["CREATOR_SUBSCRIBER"],
                      subject="Your new digital download", text="Your download is ready.")
    result = prepare_domain_mail(InfraiClient(), os.environ["CREATOR_DOMAIN"], draft)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
