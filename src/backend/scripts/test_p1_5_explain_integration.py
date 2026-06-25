"""P1-5 explain 联调 API 冒烟（integration/p1-5-explain · F015）"""
import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api"


def req(method: str, path: str, body=None, token: str | None = None, timeout: int = 120):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        BASE + path, data=data, headers=headers, method=method
    )
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        return json.loads(resp.read())


def pick_pending_orders(token: str, count: int = 2) -> list[str]:
    result = req("GET", "/orders?status=pending&page=1&page_size=50", token=token)
    items = result["data"]["items"]
    codes = [o["order_code"] for o in items[:count]]
    if len(codes) < count:
        raise RuntimeError(f"pending 订单不足 {count} 条")
    return codes


def create_global_schedule(token: str) -> str:
    order_codes = pick_pending_orders(token, 2)
    preview = req(
        "POST",
        "/schedule/global",
        {"algorithm": "traditional", "preview": True, "order_codes": order_codes},
        token=token,
    )
    assert preview["code"] == 0, preview
    schedule_code = preview["data"]["schedule_code"]
    confirm = req("POST", f"/schedule/confirm/{schedule_code}", None, token=token)
    assert confirm["code"] == 0, confirm
    return schedule_code


def main() -> int:
    try:
        health = req("GET", "/health")
        assert health.get("code") == 0 or health.get("status") == "ok", health
        print("health ok")

        login = req("POST", "/auth/login", {"username": "dispatcher", "password": "123456"})
        assert login["code"] == 0, login
        token = login["data"]["access_token"]
        print("login ok")

        schedule_code = create_global_schedule(token)
        print("schedule created", schedule_code)

        explain = req(
            "POST",
            "/ai/explain",
            {"schedule_code": schedule_code},
            token=token,
            timeout=90,
        )
        assert explain["code"] == 0, explain
        data = explain["data"]
        assert "explanation" in data, data
        assert isinstance(data.get("key_decisions"), list), data
        assert isinstance(data.get("potential_risks"), list), data
        assert isinstance(data.get("suggestions"), list), data
        meta = explain.get("meta") or {}
        print(
            "explain ok",
            "degraded=",
            meta.get("degraded"),
            "explanation_len=",
            len(data.get("explanation") or ""),
        )

        missing = req("POST", "/ai/explain", {}, token=token)
        assert missing["code"] == 40001, missing
        print("missing params ok", missing["code"])

        not_found = req(
            "POST",
            "/ai/explain",
            {"schedule_code": "GS_NONEXISTENT"},
            token=token,
        )
        assert not_found["code"] == 40401, not_found
        print("not found ok", not_found["code"])

        print("ALL_P1_5_EXPLAIN_API_CHECKS_PASS")
        return 0
    except urllib.error.HTTPError as e:
        print("HTTP error", e.code, e.read().decode())
        return 1
    except AssertionError as e:
        print("assert fail", e)
        return 1
    except Exception as e:
        print("error", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
