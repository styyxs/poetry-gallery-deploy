#!/usr/bin/env python3
"""upload_github.py · gh CLI 上传封装（deploy.py 内部调用，也可独立用）

用法：
    python3 upload_github.py <local_path> <remote_path> "[commit message]"

环境：
- gh CLI 已登录 styyxs 账户（`gh auth status` 检查）
- 上传文件自动检测 sha（覆盖已存在文件）
"""
import base64
import json
import subprocess
import sys
import urllib.parse
from pathlib import Path

GH_CLI = "/opt/homebrew/bin/gh"
GITHUB_REPO = "styyxs/poetry-gallery"


def upload(local_path: Path, remote_path: str, msg: str) -> bool:
    """上传单个文件，自动处理 sha（覆盖已存在文件）"""
    local_path = Path(local_path)
    if not local_path.exists():
        print(f"  ❌ 本地文件不存在: {local_path}")
        return False

    with open(local_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    encoded = urllib.parse.quote(remote_path, safe="")

    # GET sha（已存在文件需要，覆盖上传）
    sha_result = subprocess.run(
        [GH_CLI, "api", f"repos/{GITHUB_REPO}/contents/{encoded}", "--jq", ".sha"],
        capture_output=True, text=True, timeout=20,
    )
    sha = sha_result.stdout.strip()

    payload = {"message": msg, "content": b64}
    if sha:
        payload["sha"] = sha

    r = subprocess.run(
        [GH_CLI, "api", f"repos/{GITHUB_REPO}/contents/{encoded}", "-X", "PUT", "--input", "-"],
        input=json.dumps(payload), capture_output=True, text=True, timeout=60,
    )

    if r.returncode == 0:
        size_kb = local_path.stat().st_size / 1024
        print(f"  ✅ {remote_path} ({size_kb:.1f}KB)")
        return True
    else:
        print(f"  ❌ {remote_path}: {r.stderr[:300]}")
        return False


def main():
    if len(sys.argv) < 4:
        print('用法: python3 upload_github.py <local_path> <remote_path> "[commit message]"')
        print('示例: python3 upload_github.py ./poems/望洞庭.html poems/望洞庭.html "Add 望洞庭"')
        sys.exit(1)

    local = Path(sys.argv[1])
    remote = sys.argv[2]
    msg = sys.argv[3]

    ok = upload(local, remote, msg)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()