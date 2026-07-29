#!/usr/bin/env python3
"""
Poetry Gallery Deploy · 端到端主入口（v2 一条龙）

输入：诗的 JSON 配置（参考 templates/poem.json.template）
输出：5 张 AI 图 + 6 段 TTS + 离线 HTML + GitHub Pages 上线

用法：
    python3 deploy.py examples/望洞庭.json
    python3 deploy.py examples/望洞庭.json --deploy   # 部署到 GitHub
    python3 deploy.py examples/望洞庭.json --skip-images  --skip-audio  # 复用已有素材
    python3 deploy.py examples/望洞庭.json --no-upload  # 只生成本地素材

设计哲学（v2）：
- 一条龙跑通：JSON → 生图 → TTS → HTML → 部署
- 不允许漏任何步骤：缺一就返回非零退出码
- 自动调 validate.py：部署前必过卡门
- 不允许 fallback：homepage 卡片必须有 illus

依赖：
- mmx-cli（图像 + TTS）
- Python 3.8+
- gh CLI（已登录 styyxs 账户）

环境变量（可选）：
- POETRY_SITE_DIR: poetry-site 本地路径（默认 /Users/sengao/WorkBuddy/2026-05-27-13-53-13/poetry-site）
- POETRY_REMOTE: GitHub Pages URL（默认 https://styyxs.github.io/poetry-gallery）
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# ===== 配置常量（焊死）=====
TTS_VOICE = "female-shaonv-jingpin"
TTS_SPEED_NORMAL = "0.85"
TTS_SPEED_POEM = "0.75"
TTS_BITRATE = "64000"
TTS_SAMPLE_RATE = "16000"
WEBP_QUALITY_INNER = 75     # 内页插画（4 张）
WEBP_QUALITY_COVER = 82     # 主页卡片封面
WEBP_METHOD = 6
MAX_INNER_WIDTH = 800       # 内页插画最长边
COVER_WIDTH = 1200          # 主页卡片宽度

GH_CLI = "/opt/homebrew/bin/gh"
GITHUB_REPO = "styyxs/poetry-gallery"

DEFAULT_POETRY_SITE = "/Users/sengao/WorkBuddy/2026-05-27-13-53-13/poetry-site"
DEFAULT_REMOTE_BASE = "https://styyxs.github.io/poetry-gallery"

# ===== 色系 =====
COLOR_PALETTES = {
    "静谧月夜": {
        "style_words": "soft pastel mint blue and moonlight silver color palette, macaron tones",
        "page_bg": "linear-gradient(135deg, #b8e0ff 0%, #fff3a0 50%, #ffd6e8 100%)",
    },
    "春日花朵": {
        "style_words": "soft pastel cherry pink and cream yellow color palette, macaron tones, spring blossom mood",
        "page_bg": "linear-gradient(135deg, #ffd6e8 0%, #fff3a0 50%, #c8a8ff 100%)",
    },
    "夏日明媚": {
        "style_words": "soft pastel sky blue and sunshine yellow color palette, macaron tones, bright summer mood",
        "page_bg": "linear-gradient(135deg, #b8e0ff 0%, #ffe066 50%, #6bdbb8 100%)",
    },
    "秋日暖阳": {
        "style_words": "soft pastel warm orange and golden cream color palette, macaron tones, autumn warmth",
        "page_bg": "linear-gradient(135deg, #ffe066 0%, #ff9eb5 50%, #c8a8ff 100%)",
    },
    "冬日白雪": {
        "style_words": "soft pastel snow white and icy lavender color palette, macaron tones, gentle winter mood",
        "page_bg": "linear-gradient(135deg, #e0eaff 0%, #f0e6ff 50%, #d6f0ff 100%)",
    },
}
DEFAULT_PALETTE = "静谧月夜"


def pick_palette(poem: dict) -> str:
    """自动选色系（不准问用户）"""
    explicit = poem.get("palette")
    if explicit and explicit in COLOR_PALETTES:
        return explicit

    title = poem.get("title", "")
    text = (title + " " + " ".join(l.get("original", "") for l in poem.get("lines", []))).lower()

    if any(k in text for k in ["月", "夜", "思", "霜", "静"]):
        return "静谧月夜"
    if any(k in text for k in ["春", "花", "柳", "桃", "莺"]):
        return "春日花朵"
    if any(k in text for k in ["夏", "荷", "蝉", "暑"]):
        return "夏日明媚"
    if any(k in text for k in ["秋", "枫", "黄", "登", "白日", "夕"]):
        return "秋日暖阳"
    if any(k in text for k in ["冬", "雪", "寒", "梅"]):
        return "冬日白雪"
    return DEFAULT_PALETTE


def run_cmd(cmd: list, timeout: int = 120, cwd: Path = None) -> str:
    """run subprocess, raise if non-zero"""
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
    if r.returncode != 0:
        raise RuntimeError(f"命令失败: {' '.join(cmd)}\nstdout: {r.stdout[:500]}\nstderr: {r.stderr[:500]}")
    return r.stdout.strip()


def generate_inner_image(prompt: str, out_webp: Path, palette_name: str) -> Path:
    """Step 2: 生 1 张内页插画（1:1 jpg → WebP 800px q=75）"""
    style = COLOR_PALETTES.get(palette_name, COLOR_PALETTES[DEFAULT_PALETTE])
    full_prompt = (
        f"Children's watercolor picture book illustration, {style['style_words']}, "
        f"rounded shapes, simple and warm, dreamy atmosphere, no text, white background. "
        f"{prompt}"
    )
    # 用 --out-prefix + base64 模式（自动落盘到当前目录）
    # cwd 必须是当前目录，否则 mmx 把 cwd 加进文件名
    prefix = out_webp.stem  # 如 line1
    cmd = [
        "mmx", "image", "generate",
        "--prompt", full_prompt,
        "--aspect-ratio", "1:1",
        "--response-format", "base64",
        "--quiet",
        "--out-prefix", prefix,
    ]
    run_cmd(cmd, timeout=180)
    generated = Path(f"{prefix}_001.jpg")
    if not generated.exists():
        raise RuntimeError(f"内页图未生成: {generated}")

    # jpg → WebP（缩放到 ≤800px, q=75）
    from PIL import Image
    img = Image.open(generated).convert("RGB")
    if max(img.size) > MAX_INNER_WIDTH:
        ratio = MAX_INNER_WIDTH / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    img.save(out_webp, "WEBP", quality=WEBP_QUALITY_INNER, method=WEBP_METHOD)
    generated.unlink()
    return out_webp


def generate_card_cover(prompt: str, out_webp: Path) -> Path:
    """Step 3: 生 1 张主页卡片封面（16:9 2K 国风动漫 → WebP 1200px q=82）"""
    # 用 --out 直接落盘（不要 --out-prefix）
    full_prompt = f"国风动漫风格，电影级光影。{prompt}"
    tmp_jpg = out_webp.with_suffix(".jpg")
    cmd = [
        "mmx", "image", "generate",
        "--prompt", full_prompt,
        "--aspect-ratio", "16:9",
        "--resolution", "2K",
        "--out", str(tmp_jpg),
    ]
    run_cmd(cmd, timeout=180)
    if not tmp_jpg.exists():
        raise RuntimeError(f"card_cover 未生成: {tmp_jpg}")

    # jpg → WebP（1200×675, q=82）
    from PIL import Image
    img = Image.open(tmp_jpg).convert("RGB")
    w, h = img.size
    new_h = int(h * COVER_WIDTH / w)
    img = img.resize((COVER_WIDTH, new_h), Image.LANCZOS)
    img.save(out_webp, "WEBP", quality=WEBP_QUALITY_COVER, method=WEBP_METHOD)
    tmp_jpg.unlink()
    return out_webp


def generate_audio(text: str, out_path: Path, speed: str) -> Path:
    """生成 TTS mp3"""
    cmd = [
        "mmx", "speech", "synthesize",
        "--text", text,
        "--voice", TTS_VOICE,
        "--speed", speed,
        "--bitrate", TTS_BITRATE,
        "--sample-rate", TTS_SAMPLE_RATE,
        "--out", str(out_path),
        "--quiet",
    ]
    run_cmd(cmd, timeout=60)
    if not out_path.exists():
        raise RuntimeError(f"TTS 未生成: {out_path}")
    return out_path


def build_offline_html(poem: dict, workdir: Path, palette_name: str) -> Path:
    """Step 5: 拼装离线 HTML（base64 内嵌）"""
    # 这里直接调用 build_html.py 即可（同包内）
    from build_html import build_html
    html = build_html(poem, workdir, palette_name, COLOR_PALETTES)
    out_path = workdir / f"{poem['title']}_儿童绘本.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


def extract_media_for_github(html_path: Path, img_dir: Path) -> None:
    """Step 6: 把 base64 内嵌的 media 拆成相对路径文件（GitHub Pages 部署用）"""
    # 同 v1 extract_media.py 逻辑（焊死）
    import re
    html = html_path.read_text(encoding="utf-8")
    img_dir.mkdir(parents=True, exist_ok=True)
    img_dir_name = img_dir.name

    # 音频
    audio_idx = 0
    def repl_audio(m):
        nonlocal audio_idx
        audio_idx += 1
        b64 = m.group(2)
        fname = f"bg_audio_{audio_idx}.mp3"
        (img_dir / fname).write_bytes(base64.b64decode(b64))
        return f"{img_dir_name}/{fname}"
    html = re.sub(r'data:audio/(\w+);base64,([A-Za-z0-9+/=]+)', repl_audio, html)

    # 图片
    img_idx = 0
    def repl_img(m):
        nonlocal img_idx
        img_idx += 1
        b64 = m.group(2)
        fname = f"img_{img_idx}.webp"
        (img_dir / fname).write_bytes(base64.b64decode(b64))
        return f"{img_dir_name}/{fname}"
    html = re.sub(r'data:image/(\w+);base64,([A-Za-z0-9+/=]+)', repl_img, html)

    # 优化：第 1 张图 eager + fetchpriority，其他 lazy + async
    html = re.sub(r'<img ', '<img loading="lazy" decoding="async" ', html)
    html = html.replace('loading="lazy" decoding="async" ', 'loading="eager" fetchpriority="high" decoding="sync" ', 1)
    # 音频 preload=none
    html = re.sub(r'<audio ', '<audio preload="none" ', html)
    html = re.sub(r'preload="auto"', 'preload="none"', html)
    # 注入智能预载 JS（图片加载完后才预载音频）
    if "</body>" in html and "preloadAudios" not in html:
        preload_script = '''<script>
(function(){var i=document.querySelectorAll("img[loading=lazy]");if(!i.length)i=document.querySelectorAll("img");var l=0,a=document.querySelectorAll("audio");function p(){a.forEach(function(e){e.preload="auto"})}i.forEach(function(e){if(e.complete){l++;if(l===1)p()}else e.addEventListener("load",function(){l++;if(l===1)p()},{once:!0})})})();
</script>'''
        html = html.replace("</body>", preload_script + "\n</body>")

    html_path.write_text(html, encoding="utf-8")


def update_poems_json(poem: dict, illus_path: str, site_dir: Path) -> None:
    """Step 7: poems.json 加/更新条目（含 illus 字段）"""
    json_path = site_dir / "poems.json"
    data = json.loads(json_path.read_text(encoding="utf-8"))

    # tags 决策：JSON 里如果指定了 tags 就用 JSON 的（来自诗的意境分析），否则 fallback
    json_tags = poem.get("tags")
    if json_tags and isinstance(json_tags, list) and len(json_tags) > 0:
        tags = json_tags
    else:
        # 自动从 palette + title 推 tags
        tags = _infer_tags(poem)

    # 找已有或追加
    found = False
    for i, p in enumerate(data):
        if p.get("title") == poem["title"]:
            data[i] = {
                "title": poem["title"],
                "author": f"{poem['dynasty']}·{poem['author']}",
                "file": f"poems/{poem['title']}.html",
                "summary": "，".join(l["original"] for l in poem["lines"]) + "。",
                "tags": tags,
                "illus": illus_path,
            }
            found = True
            break
    if not found:
        data.append({
            "title": poem["title"],
            "author": f"{poem['dynasty']}·{poem['author']}",
            "file": f"poems/{poem['title']}.html",
            "summary": "，".join(l["original"] for l in poem["lines"]) + "。",
            "tags": tags,
            "illus": illus_path,
        })

    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _infer_tags(poem: dict) -> list:
    """自动从诗意境推断 tags（兜底）"""
    title = poem.get("title", "")
    text = (title + " " + " ".join(l.get("original", "") for l in poem.get("lines", []))).lower()
    tags = []
    if any(k in text for k in ["月", "夜", "思", "霜", "静"]):
        tags.extend(["月", "思乡"])
    if any(k in text for k in ["山", "水", "江", "湖", "河", "海"]):
        tags.append("山水")
    if any(k in text for k in ["秋", "黄", "枫", "夕"]):
        tags.append("秋")
    if any(k in text for k in ["登", "高", "楼", "远"]):
        tags.append("登高")
    if not tags:
        tags = ["古诗", poem.get("dynasty", "唐")]
    return list(dict.fromkeys(tags))  # 去重保序


def upload_to_github(local_path: Path, remote_path: str, msg: str) -> bool:
    """Step 8: gh CLI 上传单个文件（自动处理 sha）"""
    with open(local_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    encoded = urllib_parse_quote(remote_path)

    sha = subprocess.run(
        [GH_CLI, "api", f"repos/{GITHUB_REPO}/contents/{encoded}", "--jq", ".sha"],
        capture_output=True, text=True, timeout=20,
    ).stdout.strip()

    payload = json.dumps({"message": msg, "content": b64, **({"sha": sha} if sha else {})})
    r = subprocess.run(
        [GH_CLI, "api", f"repos/{GITHUB_REPO}/contents/{encoded}", "-X", "PUT", "--input", "-"],
        input=payload, capture_output=True, text=True, timeout=60,
    )
    return r.returncode == 0


def urllib_parse_quote(s: str) -> str:
    import urllib.parse
    return urllib.parse.quote(s, safe="")


def validate_before_deploy(site_dir: Path) -> bool:
    """Step 7.5: 部署前本地校验（卡门 1）"""
    script = Path(__file__).parent / "validate.py"
    r = subprocess.run(
        [sys.executable, str(script), str(site_dir / "poems.json"), "--local-dir", str(site_dir)],
        capture_output=True, text=True,
    )
    print(r.stdout)
    if r.returncode != 0:
        print("❌ 部署前校验失败！不允许 commit")
        return False
    return True


def validate_after_deploy() -> bool:
    """Step 9: 部署后在线校验（卡门 2）"""
    script = Path(__file__).parent / "validate.py"
    r = subprocess.run(
        [sys.executable, str(script), str(DEFAULT_POETRY_SITE / "poems.json"), "--remote", DEFAULT_REMOTE_BASE],
        capture_output=True, text=True,
    )
    print(r.stdout)
    if r.returncode != 0:
        print("❌ 上线后校验失败！")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Poetry Gallery Deploy · 古诗绘本馆一条龙部署")
    parser.add_argument("config", help="诗的 JSON 配置路径")
    parser.add_argument("--deploy", action="store_true", help="部署到 GitHub Pages（默认只生成本地素材）")
    parser.add_argument("--skip-images", action="store_true", help="跳过生图（复用已有 img_*.webp）")
    parser.add_argument("--skip-audio", action="store_true", help="跳过 TTS（复用已有 bg_audio_*.mp3）")
    parser.add_argument("--skip-cover", action="store_true", help="跳过生 card_cover（复用已有 card_cover.webp）")
    parser.add_argument("--no-upload", action="store_true", help="不部署到 GitHub（即使 --deploy）")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    poem = json.loads(config_path.read_text(encoding="utf-8"))
    title = poem["title"]
    palette = pick_palette(poem)
    print(f"\n📖 《{title}》开始部署")
    print(f"🎨 色系：{palette}")

    site_dir = Path(os.environ.get("POETRY_SITE_DIR", DEFAULT_POETRY_SITE))
    workdir = Path(tempfile.mkdtemp(prefix=f"poem_{title}_"))
    img_workdir = workdir / "assets"
    img_workdir.mkdir()
    img_dir = site_dir / "poems" / f"{title}_img"
    img_dir.mkdir(parents=True, exist_ok=True)

    # ===== Step 1: 校验 JSON（最基础）=====
    required = ["title", "author", "dynasty", "card_cover_prompt", "lines", "story", "story_tts", "facts"]
    for k in required:
        if k not in poem:
            raise RuntimeError(f"JSON 缺少字段: {k}")
    if len(poem["lines"]) != 4:
        raise RuntimeError(f"必须 4 句绝句（当前 {len(poem['lines'])} 句）")
    for i, line in enumerate(poem["lines"], 1):
        for k in ["original", "translation", "tts_explanation", "image_prompt"]:
            if k not in line:
                raise RuntimeError(f"第 {i} 句缺少字段: {k}")

    # ===== Step 2: 生 4 张内页插画 =====
    if not args.skip_images:
        print("\n🎨 Step 2/9：生 4 张内页插画（base64 → WebP 800px q=75）...")
        for i, line in enumerate(poem["lines"], 1):
            out = img_workdir / f"line{i}.webp"
            print(f"  → 第 {i} 句: {line['original'][:10]}...")
            generate_inner_image(line["image_prompt"], out, palette)
            print(f"    ✅ line{i}.webp ({out.stat().st_size//1024} KB)")
    else:
        print("⏭️  跳过生图，复用已有 line*.webp")
        for i in range(1, 5):
            src = img_dir / f"img_{i}.webp"
            if not src.exists():
                raise RuntimeError(f"--skip-images 但 img_{i}.webp 不存在: {src}")
            (img_workdir / f"line{i}.webp").write_bytes(src.read_bytes())
    if not args.skip_cover:
        print("\n🖼️  Step 3/9：生 card_cover.webp（16:9 2K 国风动漫 → 1200px q=82）...")
        cover_jpg = img_workdir / "card_cover.jpg"
        cover_webp = img_dir / "card_cover.webp"
        print(f"  → card_cover: {poem['card_cover_prompt'][:50]}...")
        generate_card_cover(poem["card_cover_prompt"], cover_webp)
        print(f"    ✅ card_cover.webp ({cover_webp.stat().st_size//1024} KB)")
    else:
        print("⏭️  跳过 card_cover，复用已有")
        cover_webp = img_dir / "card_cover.webp"
        if not cover_webp.exists():
            raise RuntimeError(f"--skip-cover 但 card_cover.webp 不存在: {cover_webp}")

    # ===== Step 4: 生 6 段 TTS =====
    if not args.skip_audio:
        print("\n🎙️ Step 4/9：生 6 段 TTS...")
        for i, line in enumerate(poem["lines"], 1):
            out = img_workdir / f"line{i}.mp3"
            tts_text = f"{line['original']}。{line['tts_explanation']}"
            print(f"  → 第 {i} 句朗读...")
            generate_audio(tts_text, out, TTS_SPEED_NORMAL)
            print(f"    ✅ line{i}.mp3 ({out.stat().st_size//1024} KB)")
        print("  → 故事朗读...")
        generate_audio(poem["story_tts"], img_workdir / "story.mp3", TTS_SPEED_NORMAL)
        print(f"    ✅ story.mp3 ({(img_workdir / 'story.mp3').stat().st_size//1024} KB)")
        full_text = f"{title}，{poem['dynasty']}，{poem['author']}。" + "，".join(
            l["original"] for l in poem["lines"]
        ) + "。"
        print("  → 完整诗篇朗读...")
        generate_audio(full_text, img_workdir / "full_poem.mp3", TTS_SPEED_POEM)
        print(f"    ✅ full_poem.mp3 ({(img_workdir / 'full_poem.mp3').stat().st_size//1024} KB)")
    else:
        print("⏭️  跳过 TTS，复用已有音频")
        for i in range(1, 7):
            # 第5=story，第6=full_poem
            if i == 5:
                base_name = "bg_audio_5"
                dst = img_workdir / "story.mp3"
            elif i == 6:
                base_name = "bg_audio_6"
                dst = img_workdir / "full_poem.mp3"
            else:
                base_name = f"bg_audio_{i}"
                dst = img_workdir / f"line{i}.mp3"
            # 兼容 mp3 和 m4a（v2 已统一用 mp3，但可能历史用 m4a）
            src = None
            for ext in [".mp3", ".m4a"]:
                candidate = img_dir / f"{base_name}{ext}"
                if candidate.exists():
                    src = candidate
                    break
            if not src:
                raise RuntimeError(f"--skip-audio 但 {base_name}.{{mp3,m4a}} 不存在: {img_dir}")
            dst.write_bytes(src.read_bytes())

    # ===== Step 5: 拼装离线 HTML =====
    print("\n🔨 Step 5/9：拼装离线 HTML（base64 内嵌）...")
    html_path = build_offline_html(poem, img_workdir, palette)
    print(f"    ✅ {html_path} ({html_path.stat().st_size//1024} KB)")

    # ===== Step 6: extract_media 拆 base64 → 相对路径 =====
    print("\n📦 Step 6/9：拆 base64 → 相对路径（GitHub Pages 部署用）...")
    # 先把 webp 复制到 workdir 的 _img（extract_media 内部用 img_N.webp 命名）
    import shutil
    for i in range(1, 5):
        shutil.copy(img_workdir / f"line{i}.webp", img_workdir / f"img_{i}.webp")
    extract_media_for_github(html_path, img_dir)
    # 把瘦身后的 HTML 复制到 site_dir
    site_html = site_dir / "poems" / f"{title}.html"
    shutil.copy(html_path, site_html)
    print(f"    ✅ 瘦身后 HTML: {site_html} ({site_html.stat().st_size//1024} KB)")
    print(f"    ✅ 媒体文件: {img_dir}/")

    # ===== Step 7: 更新 poems.json =====
    print("\n📋 Step 7/9：更新 poems.json（含 illus 字段）...")
    illus_path = f"poems/{title}_img/card_cover.webp"
    update_poems_json(poem, illus_path, site_dir)
    print(f"    ✅ {site_dir / 'poems.json'} 已更新（含 {title} illus={illus_path}）")

    # ===== Step 7.5: 部署前校验（卡门 1）=====
    if args.deploy:
        print("\n🛡️  Step 7.5/9：部署前本地校验（卡门 1）...")
        if not validate_before_deploy(site_dir):
            sys.exit(1)

        # ===== Step 8: gh CLI 上传 =====
        print("\n📤 Step 8/9：gh CLI 上传到 styyxs/poetry-gallery...")
        # 1) HTML
        upload_to_github(site_html, f"poems/{title}.html", f"📜 Add {title} children picture book")
        # 2) card_cover
        upload_to_github(cover_webp, f"poems/{title}_img/card_cover.webp", f"🎨 Add {title} card cover")
        # 3) poems.json
        upload_to_github(site_dir / "poems.json", "poems.json", f"📋 Update poems index with {title}")
        # 4) 媒体（webp + mp3）
        for f in sorted(img_dir.iterdir()):
            if f.suffix in (".webp", ".mp3"):
                upload_to_github(f, f"poems/{title}_img/{f.name}", f"🖼️ {f.name}")

        # ===== Step 9: 上线后在线校验（卡门 2）=====
        print("\n🛡️  Step 9/9：上线后在线校验（卡门 2）...")
        # 等 1-2 分钟 GitHub Pages rebuild
        print("⏳ 等待 GitHub Pages rebuild（80秒）...")
        import time
        time.sleep(80)
        if not validate_after_deploy():
            sys.exit(1)

        print(f"\n🎉 完成！浏览器访问：{DEFAULT_REMOTE_BASE}/")
    else:
        print(f"\n✅ 本地素材生成完毕（未部署）。")
        print(f"   HTML: {site_html}")
        print(f"   card_cover.webp: {cover_webp}")
        print(f"   媒体: {img_dir}/")
        print(f"\n下一步：deploy.py <poem.json> --deploy")


if __name__ == "__main__":
    main()