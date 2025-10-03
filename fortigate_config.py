#!/usr/bin/env python3
import os
import sys
import json
import argparse
import requests
from urllib.parse import urljoin

# 自己署名向け（HTTPS時のみ効く。HTTP時は無視される）
requests.packages.urllib3.disable_warnings()  # type: ignore

def api_request(scheme: str, host: str, port: int, token: str,
                method: str, path: str, **kwargs):
    """
    FortiGate REST API ラッパー
    scheme: "http" or "https"
    """
    base = f"{scheme}://{host}:{port}/"
    url = urljoin(base, path)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    resp = requests.request(
        method, url, headers=headers,
        verify=False, timeout=30, **kwargs
    )

    # FortiGateは成功時 200 かつ JSON "status":"success" を返すのが一般的
    try:
        data = resp.json()
    except Exception:
        resp.raise_for_status()
        return resp

    if not resp.ok or data.get("status") not in ("success", 200):
        raise RuntimeError(
            f"API error: HTTP {resp.status_code}, body={json.dumps(data, ensure_ascii=False)}"
        )
    return data

def set_hostname(scheme: str, host: str, port: int, token: str, hostname: str):
    payload = {"hostname": hostname}
    return api_request(scheme, host, port, token, "PUT",
                       "api/v2/cmdb/system/global", json=payload)

def get_hostname(scheme: str, host: str, port: int, token: str) -> str:
    data = api_request(scheme, host, port, token, "GET",
                       "api/v2/cmdb/system/global")
    return (data.get("results") or {}).get("hostname", "")

def main():
    p = argparse.ArgumentParser(description="FortiGate config via REST API")
    p.add_argument("--host", default=os.getenv("FGT_HOST"))
    p.add_argument("--token", default=os.getenv("FGT_API_TOKEN"))
    p.add_argument("--hostname", required=True)
    p.add_argument("--scheme", choices=["http", "https"],
                   default=os.getenv("FGT_SCHEME", "https"))
    p.add_argument("--port", type=int, default=int(os.getenv("FGT_PORT", "443")))
    args = p.parse_args()

    if not args.host or not args.token:
        print("FGT_HOST と FGT_API_TOKEN を指定してください（引数 or 環境変数）", file=sys.stderr)
        sys.exit(2)

    print(f"[INFO] target={args.scheme}://{args.host}:{args.port}/api/v2 ...")
    set_hostname(args.scheme, args.host, args.port, args.token, args.hostname)
    new_name = get_hostname(args.scheme, args.host, args.port, args.token)
    print(f"Hostname updated: {args.host} -> {new_name}")

if __name__ == "__main__":
    main()
