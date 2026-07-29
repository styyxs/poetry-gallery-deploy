#!/usr/bin/env python3
"""
validate.py · 部署前/上线后校验器（卡门·P0 焊死）

这是 v2 poetry-gallery-deploy 的卡门。任何诗的部署上线必须过此脚本。

用法：
    # 部署前本地校验
    python3 validate.py poems.json --local-dir /Users/sengao/WorkBuddy/2026-05-27-13-53-13/poetry-site

    # 上线后在线校验
    python3 validate.py poems.json --remote https://styyxs.github.io/poetry-gallery

    # 本地 + 远程同时校验
    python3 validate.py poems.json --local-dir <DIR> --remote <URL>

退出码：0=全过，1=有失败项（不允许上线）
"""
import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DEFAULT_REMOTE = "https://styyxs.github.io/poetry-gallery"


def fail(msg: str) -> bool:
    print(f"  ❌ {msg}")
    return False


def ok(msg: str) -> bool:
    print(f"  ✅ {msg}")
    return True


def head_url(url: str, timeout: int = 10) -> tuple[int, int]:
    """返回 (status_code, content_length)。URL 必须 ASCII-safe，中文路径要先 quote。"""
    # 编码非 ASCII 字符
    parts = urllib.parse.urlsplit(url)
    safe_path = urllib.parse.quote(parts.path, safe="/-_.~")
    safe_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, safe_path, parts.query, parts.fragment))
    try:
        req = urllib.request.Request(safe_url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, int(resp.headers.get("Content-Length", 0))
    except urllib.error.HTTPError as e:
        return e.code, 0
    except Exception as e:
        return 0, 0


def validate(poems_json_path: Path, local_dir: Path = None, remote_base: str = None) -> bool:
    if not poems_json_path.exists():
        print(f"❌ 文件不存在: {poems_json_path}")
        return False

    try:
        data = json.loads(poems_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        return False

    if not isinstance(data, list):
        print("❌ poems.json 必须是数组（每首一首）")
        return False

    print(f"\n📋 poems.json 校验: {poems_json_path.name} ({len(data)} 首)")
    print("─" * 60)
    all_pass = True

    for poem in data:
        title = poem.get("title", "<未知>")
        print(f"\n《{title}》")

        # 检查 1: 必填字段
        for required in ["title", "author", "file", "summary", "tags"]:
            if required not in poem:
                fail(f"缺少必填字段: {required}")
                all_pass = False
        if not all(required in poem for required in ["title", "author", "file", "summary", "tags"]):
            continue

        # 检查 2: tags 必须是数组
        if not isinstance(poem["tags"], list):
            fail(f"tags 必须是数组（当前类型: {type(poem['tags']).__name__}）")
            all_pass = False
        else:
            ok(f"tags = {poem['tags']}")

        # 检查 3: ⭐ illus 字段必须存在（v2 P0 焊死·森哥 2026-07-29 教训）
        if "illus" not in poem:
            fail("缺少 illus 字段（前端会 fallback 到 SVG，违反 P0 规则）")
            all_pass = False
            continue
        illus = poem["illus"]
        ok(f"illus = {illus}")

        # 检查 4: illus 路径必须以 poems/<title>_img/card_cover.webp 结尾
        expected_suffix = f"poems/{title}_img/card_cover.webp"
        if not illus.endswith(expected_suffix):
            fail(f"illus 路径格式不正确，应以 {expected_suffix} 结尾，实际 {illus}")
            all_pass = False
        else:
            ok("illus 路径符合规范")

        # 检查 5: 本地文件存在 + 大小 < 100KB
        if local_dir:
            local_path = local_dir / illus
            if not local_path.exists():
                fail(f"本地文件不存在: {local_path}")
                all_pass = False
            else:
                size_kb = local_path.stat().st_size / 1024
                if size_kb > 100:
                    fail(f"文件过大: {size_kb:.1f}KB（要求 < 100KB）")
                    all_pass = False
                else:
                    ok(f"本地文件存在 ({size_kb:.1f}KB)")

        # 检查 6: 远程 HTTP 200（在线验真）
        if remote_base:
            url = f"{remote_base.rstrip('/')}/{illus}"
            status, size = head_url(url)
            if status != 200:
                fail(f"远程 HTTP {status}: {url}")
                all_pass = False
            else:
                ok(f"远程 HTTP 200 ({size//1024}KB)")

            # 顺便检查主页 HTML + 内页 4 张图 + 6 段音频
            base_url = f"{remote_base.rstrip('/')}/poems/{title}"
            for asset in [f"{base_url}.html",
                          f"{base_url}_img/img_1.webp",
                          f"{base_url}_img/img_2.webp",
                          f"{base_url}_img/img_3.webp",
                          f"{base_url}_img/img_4.webp",
                          f"{base_url}_img/bg_audio_1.mp3",
                          f"{base_url}_img/bg_audio_2.mp3",
                          f"{base_url}_img/bg_audio_3.mp3",
                          f"{base_url}_img/bg_audio_4.mp3",
                          f"{base_url}_img/bg_audio_5.mp3",
                          f"{base_url}_img/bg_audio_6.mp3"]:
                s, _ = head_url(asset)
                if s != 200:
                    fail(f"  资源缺失: HTTP {s} {asset}")
                    all_pass = False
            if all(head_url(f"{remote_base.rstrip('/')}/poems/{title}{suffix}")[0] == 200
                   for suffix in [".html", "_img/img_1.webp", "_img/bg_audio_1.mp3"]):
                ok(f"  HTML + 4 张图 + 6 段音频全部在线")

    print("─" * 60)
    if all_pass:
        print("🎯 总体: ✅ 全部通过（可部署 / 已正确上线）")
    else:
        print("🎯 总体: ❌ 有失败项（必须修复后重跑）")
    print()
    return all_pass


def main():
    parser = argparse.ArgumentParser(description="poems.json 部署前/上线后校验")
    parser.add_argument("poems_json", help="poems.json 文件路径")
    parser.add_argument("--local-dir", help="poetry-site 根目录（启用本地文件检查）")
    parser.add_argument("--remote", default=None, help=f"远程基础 URL（默认 {DEFAULT_REMOTE}）")

    args = parser.parse_args()

    remote = args.remote if args.remote else None
    local_dir = Path(args.local_dir) if args.local_dir else None

    ok = validate(Path(args.poems_json), local_dir, remote)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()