# Poetry Gallery Deploy · 古诗绘本馆一条龙部署

> **v2.0.0 · 重构自 ancient-poem-kids-picturebook + kids-illustration-html**
> 一句话：把一首古诗的 JSON → 上线到 [styyxs.github.io/poetry-gallery](https://styyxs.github.io/poetry-gallery/) 主页，全程一条命令。

## 能力

- ✅ **5 张 AI 图**：4 张 1:1 内页插画（水彩日系绘本风）+ 1 张 16:9 主页卡片封面（国风动漫·电影级光影）
- ✅ **6 段 TTS 朗读**：4 句讲解 + 故事 + 末尾完整诗篇（温柔女老师音色）
- ✅ **离线 HTML 拼装**：base64 内嵌，双击即开
- ✅ **GitHub Pages 部署**：拆 base64 → 相对路径 → 加 illus 字段 → gh CLI 上传
- ✅ **卡门校验器**：部署前本地 + 上线后在线两阶段，缺一不放过

## 安装

```bash
git clone https://github.com/styyxs/poetry-gallery-deploy.git
cd poetry-gallery-deploy
pip install Pillow  # WebP 转码依赖
# mmx-cli 需已安装并登录
```

## 使用

### 1. 准备诗的 JSON 配置

参照 `examples/望洞庭.json` 或 `templates/poem.json.template`：

```json
{
  "title": "望洞庭",
  "author": "刘禹锡",
  "dynasty": "唐",
  "palette": "静谧月夜",
  "tags": ["山水", "月", "秋", "湖"],
  "card_cover_prompt": "国风动漫风格，电影级光影。洞庭湖秋夜全景图：...",
  "lines": [
    {
      "original": "湖光秋月两相和",
      "translation": "秋天晚上，洞庭湖的水光和天上月光相互融合，好温柔呀。",
      "tts_explanation": "这句话的意思是：在秋天的晚上...",
      "image_prompt": "A serene wide Chinese lake at autumn night..."
    },
    /* ... 4 句 */
  ],
  "story": "很久很久以前...\\n\\n有一天...",
  "story_tts": "很久很久以前...(去掉 \\n)",
  "facts": [
    {"emoji": "🏞️", "title": "...", "body": "..."},
    /* ... 3 个 */
  ]
}
```

**字段约束（详细见 templates/poem.json.template）**：
- `lines` 必须 4 句绝句
- `tts_explanation` 和 `story_tts` 不能带 `\n`（会被读出停顿）
- `card_cover_prompt` 用**中文**（描述国风动漫场景），内部加 "国风动漫风格，电影级光影。" 前缀
- `image_prompt` 用**英文**（mmx 在英文 prompt 上表现更好）

### 2. 一条龙部署

```bash
python3 scripts/deploy.py your_poem.json --deploy
```

这会跑：
1. 校验 JSON 字段完整性
2. 生 4 张内页插画（base64 → WebP, 800px, q=75）
3. 生 1 张主页卡片封面（16:9 2K → 1200×675 WebP, q=82）
4. 生 6 段 TTS（64kbps+16kHz mp3）
5. 拼装离线 HTML（base64 内嵌，~1-2MB）
6. 拆 base64 → 相对路径（GitHub Pages 部署用）
7. 更新 `poems.json`（**必含 `illus` 字段**）
8. **卡门 1**：本地校验 poems.json
9. gh CLI 上传到 styyxs/poetry-gallery
10. 等 80 秒 + **卡门 2**：在线校验所有资源

### 3. 跳过某步（节省 token）

```bash
# 跳过生图（复用已有 line*.webp）
python3 scripts/deploy.py your_poem.json --deploy --skip-images

# 跳过 TTS（复用已有 bg_audio_*.mp3）
python3 scripts/deploy.py your_poem.json --deploy --skip-audio

# 跳过 card_cover（复用已有 card_cover.webp）
python3 scripts/deploy.py your_poem.json --deploy --skip-cover

# 不部署到 GitHub（只生成本地素材，方便预览）
python3 scripts/deploy.py your_poem.json --no-upload
```

## 关键设计（必读·避坑）

### ⛔ P0 规则：主页卡片不要 SVG

GitHub Pages 主页（styyxs.github.io/poetry-gallery）的每张卡片**必须用真实生成的古风漫画图**（`card_cover.webp`），**绝对不允许** fallback 到 SVG 占位插画。

**为什么**：2026-07-29 我（agent）部署《望洞庭》时漏掉了 `illus` 字段，导致主页 4 张卡片 fallback 到 SVG，森哥痛骂。详见 `references/mistakes-2026-07-29.md`。

### 卡门设计：validate.py 不可绕过

```bash
# 部署前本地校验（卡门 1）
python3 scripts/validate.py /path/to/poetry-site/poems.json --local-dir /path/to/poetry-site

# 上线后在线校验（卡门 2）
python3 scripts/validate.py /path/to/poetry-site/poems.json --remote https://styyxs.github.io/poetry-gallery
```

任何一项 ❌ → 返回非零退出码，deploy.py 自动终止。

### 文件结构

```
styyxs/poetry-gallery-deploy/
├── SKILL.md                          # skill 入口（Hermes agent 调）
├── README.md                         # 本文档（人读）
├── LICENSE                           # MIT
├── examples/望洞庭.json              # 完整示例
├── templates/poem.json.template      # JSON 模板
├── scripts/
│   ├── deploy.py                     # ★ 一条龙主入口
│   ├── validate.py                   # ★ 卡门校验器
│   ├── build_html.py                 # 拼装离线 HTML
│   └── upload_github.py              # gh CLI 上传封装
└── references/
    ├── mistakes-2026-07-29.md        # ★ 必读：3 层根因错误复盘
    ├── poem-prompt-guide.md          # 4 张内页 prompt + card_cover prompt 模板
    ├── color-palettes.md             # 5 套色系锚 + 自动选色
    ├── deployment-workflow.md        # GitHub Pages 部署 8 步 SOP
    └── github-pages-quirks.md        # P10-P20 坑位（mmx --out vs --out-prefix 等）
```

## 已部署诗目

| 诗 | 作者 | 色系 | 文件大小 | 部署状态 |
|---|---|---|---|---|
| 静夜思 | 李白·唐 | 静谧月夜 | 1.2 MB | ✅ 已上线 |
| 望天门山 | 李白·唐 | 春日花朵 | 1.8 MB | ✅ 已上线 |
| 登鹳雀楼 | 王之涣·唐 | 秋日暖阳 | 1.7 MB | ✅ 已上线 |
| 望洞庭 | 刘禹锡·唐 | 静谧月夜 | 2.5 MB | ✅ 已上线 |

未来每跑通一首新诗，请追加此表。

## 依赖

- **mmx-cli**（图像生成 + TTS）：`mmx image generate`、`mmx speech synthesize`、`mmx vision describe`
- **Python 3.8+** + **Pillow**（WebP 转码）
- **gh CLI**（已登录 styyxs 账户）

## 常见问题

### Q: 主页 index.html 改过吗？
**A**: 不改。index.html 已有 `p.illus ? <img> : pickIllus(tags)` fallback 逻辑（GitHub 已部署版本）。fallback 仅作为系统挂了时的兜底，**不允许触发**——validate.py 卡门。

### Q: 4 张图 vs 5 张图？
**A**: 4 张是内页插画（绘本页里），1 张是主页卡片封面。两者**风格完全不同**：
- 内页：水彩日系绘本风（Satoshi Kitamura）
- 主页卡片：国风动漫·电影级光影

### Q: 单 HTML 文件多大？
**A**: v7 性能优化后约 1.2-2.5 MB（取决于音频长度）。GitHub Pages 部署首屏 < 1 秒。

### Q: deploy.py 跑过的诗 idempotent 吗？
**A**: ✅ 是。重复跑同一首诗：① 不会重复添加 poems.json 条目（update 而非 append）；② 不会重复上传资源（gh CLI 自动检测 sha）。

## License

MIT