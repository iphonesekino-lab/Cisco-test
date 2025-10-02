#!/usr/bin/env python3
import os
import sys
import json
import argparse
import requests
from urllib.parse import urljoin

requests.packages.urllib3.disable_warnings()  # 自己署名証明書向け

def api_request(host: str, token: str, method: str, path: str, **kwargs):
    base = f"https://{host}/"  # ← HTTPS を使う
    url = urljoin(base, path)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    resp = requests.request(method, url, headers=headers, verify=False, timeout=30, **kwargs)
    try:
        data = resp.json()
    except Exception:
        resp.raise_for_status()
        return resp
    if not resp.ok or data.get("status") not in ("success", 200):
        raise RuntimeError(f"API error: HTTP {resp.status_code}, body={json.dumps(data, ensure_ascii=False)}")
    return data

def set_hostname(host: str, token: str, hostname: str):
    payload = {"hostname": hostname}
    return api_request(host, token, "PUT", "api/v2/cmdb/system/global", json=payload)

def get_hostname(host: str, token: str) -> str:
    data = api_request(host, token, "GET", "api/v2/cmdb/system/global")
    return (data.get("results") or {}).get("hostname", "")

def main():
    p = argparse.ArgumentParser(description="FortiGate config via REST API")
    p.add_argument("--host", default=os.getenv("FGT_HOST"))
    p.add_argument("--token", default=os.getenv("FGT_API_TOKEN"))
    p.add_argument("--hostname", required=True)
    args = p.parse_args()
    if not args.host or not args.token:
        print("FGT_HOST と FGT_API_TOKEN を指定してください（引数 or 環境変数）", file=sys.stderr)
        sys.exit(2)
    set_hostname(args.host, args.token, args.hostname)
    print(f"Hostname updated: {args.host} -> {get_hostname(args.host, args.token)}")

if __name__ == "__main__":
    main()
