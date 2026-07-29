# GitHub Pages 部署坑位（实战验证·焊死）

## P10: mmx `--out` vs `--out-prefix`

### 内页 4 张图（base64 → 文件）

```bash
# ✅ 对：用 --out-prefix（base64 模式自动落盘到当前目录）
mmx image generate \
  --prompt "..." \
  --response-format base64 \
  --quiet \
  --out-prefix /path/to/line1
# → 输出 line1_001.jpg（自动编号）
```

**坑**：base64 模式下输出文件名 = `{out_prefix}_001.jpg`。**必须 rename** 到目标路径（mmx_helpers.py 已处理）。

### card_cover 图（直接落盘）

```bash
# ✅ 对：用 --out（直接指定输出路径）
mmx image generate \
  --prompt "国风动漫风格..." \
  --aspect-ratio "16:9" --resolution "2K" \
  --out /path/to/card_cover.jpg

# ❌ 错：用 --out-prefix
mmx image generate \
  --prompt "..." \
  --out-prefix card_cover
# → 输出 card_cover_001.jpg（带 _001 后缀，不是要的）
```

**为什么**：card_cover 图不需要 base64 模式（最终是 .webp 文件，不是 HTML 内嵌），用 `--out` 直接落盘到指定路径，省去 rename 步骤。

## P11: 主页 index.html 不要用 jsDelivr CDN

- ❌ 不要写 `<script src="https://cdn.jsdelivr.net/...">`
- ✅ 用 GitHub Pages 自带 Fastly CDN + 相对路径

**实测 jsDelivr 在中国无边缘节点，301 重定向到 raw.githubusercontent.com 反而更慢。**

## P12: 媒体子目录命名必须是 `<诗名>_img/`

- ✅ `poems/望天门山_img/img_1.webp`
- ❌ `poems/望天门山-img/...`（连字符不是下划线）
- ❌ `poems/望天门山_images/...`
- ❌ `poems/望天门山media/...`

**HTML 里的相对路径硬编码了 `<诗名>_img/` 格式**。

## P13: poems.json tags 必须是数组

```json
{
  "title": "望洞庭",
  "tags": ["山水", "月", "秋", "湖"]    ✅
}
```

```json
{
  "title": "望洞庭",
  "tags": "山水,月,秋,湖"    ❌ 字符串
}
```

**主页代码用 `poem.tags.map()` 渲染，字符串直接报错。**

## P14: subprocess.run + capture_output + input 的坑

```python
# ✅ 对
subprocess.run([...], input=data, capture_output=True, text=True, timeout=60)

# ❌ 错
subprocess.run([...], capture_output=True, input=data.encode(), text=True, timeout=60)
```

**`text=True` 模式下 `.encode()` 会报"decoded too early"**。

## P15: gh CLI 路径硬编码 `/opt/homebrew/bin/gh`

- ✅ 写死绝对路径（避免不同机器 which 路径不同）
- ❌ `subprocess.run(["gh", ...])`（依赖 PATH，可能找不到）

## P16: card_cover.webp 命名规范

- ✅ `poems/<title>_img/card_cover.webp`
- ❌ `poems/<title>_img/cover.webp`（少了 card_）
- ❌ `poems/<title>_img/card-cover.webp`（连字符不是下划线）
- ❌ `poems/<title>_img/cover.png`（PNG 不是 WebP）

**validate.py 强制检查路径**。

## P17: gh CLI 上传自动检测 sha

上传已存在的文件需要 sha（从 GET 拿）：

```python
sha = subprocess.run(
    [GH, 'api', f'repos/{REPO}/contents/{encoded_path}', '--jq', '.sha'],
    capture_output=True, text=True, timeout=20
).stdout.strip()

payload = {'message': msg, 'content': b64}
if sha:
    payload['sha'] = sha  # 已存在才加
```

**坑**：第一次上传时 sha 为空，第二次（更新）才有。代码要兼容两种情况。

## P18: 不要让用户在 poems.json 里"以后再加 illus 字段"

**绝不允许**。**每次提交 poems.json 之前必跑 validate.py**。任何一条记录没 illus → 不允许 commit。

## P19: mmx vision describe 看图用

```bash
# ✅ 对：用 mmx vision describe（实测好用）
mmx vision describe --image line1_001.jpg --prompt "一句话：是不是儿童绘本风？"

# ❌ 错：用 vision_analyze 工具（Hermes 内置 404 已废）
```

**森哥 2026-07-08 焊死规则**。

## P20: vision_analyze 后端持续 404（再次强调）

Hermes 内置 `vision_analyze` 工具后端持续 404 不可用。
**规则**：收到图片/截图/图像类需求，直接 `mmx vision describe --image <path> --prompt "<问题>"`，不试 vision_analyze。