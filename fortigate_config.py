python: fortigate_config.py

#!/usr/bin/env python3
import os
import sys
import json
import argparse
import requests
from urllib.parse import urljoin

# 証明書検証を無効化（社内機器の自己署名証明書向け）
# 可能なら verify=<社内CAのパス> に置き換えてください
requests.packages.urllib3.disable_warnings()  # type: ignore

def api_request(host: str, token: str, method: str, path: str, **kwargs):
    """
    FortiGate REST API を叩く薄いラッパー。
    method: "GET" | "POST" | "PUT" | "DELETE"
    path  : 先頭にスラッシュ無し e.g. "api/v2/cmdb/system/global"
    """
    base = f"http://{host}/"
    url = urljoin(base, path)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    resp = requests.request(method, url, headers=headers, verify=False, timeout=30, **kwargs)
    # FortiGateの成功コード: HTTP 200 かつ JSONの "status": "success"
    try:
        data = resp.json()
    except Exception:
        resp.raise_for_status()
        # JSONでなければそのまま返す
        return resp

    if not resp.ok or data.get("status") not in ("success", 200):
        # 失敗時は詳細を出す
        raise RuntimeError(f"API error: HTTP {resp.status_code}, body={json.dumps(data, ensure_ascii=False)}")
    return data

def set_hostname(host: str, token: str, hostname: str):
    # ホスト名変更: PUT /api/v2/cmdb/system/global
    payload = {"hostname": hostname}
    return api_request(host, token, "PUT", "api/v2/cmdb/system/global", json=payload)

def get_hostname(host: str, token: str) -> str:
    data = api_request(host, token, "GET", "api/v2/cmdb/system/global")
    # 取り出し方はバージョンにより若干異なることがあります
    # 一般的には results/hostname
    return (data.get("results") or {}).get("hostname", "")

def main():
    p = argparse.ArgumentParser(description="FortiGate config via REST API")
    p.add_argument("--host", default=os.getenv("FGT_HOST"), help="FortiGate host/IP")
    p.add_argument("--token", default=os.getenv("FGT_API_TOKEN"), help="API token (REST API Admin)")
    p.add_argument("--hostname", required=True, help="New hostname (e.g., GP-FortiGate)")
    args = p.parse_args()

    if not args.host or not args.token:
        print("FGT_HOST と FGT_API_TOKEN を指定してください（引数 or 環境変数）", file=sys.stderr)
        sys.exit(2)

    # 変更
    set_hostname(args.host, args.token, args.hostname)
    # 確認
    new_name = get_hostname(args.host, args.token)
    print(f"Hostname updated: {args.host} -> {new_name}")

if __name__ == "__main__":
    main()
