---
name: poetry-gallery-deploy
description: "把任意一首古诗做成「GitHub Pages 古诗绘本馆」上线的一条龙 skill。端到端：JSON 配置 → 5 张 AI 插画（4 张内页 + 1 张主页卡片封面）→ 6 段 TTS 朗读 → 离线 HTML 拼装 → 拆资源部署 → 上传 styyxs/poetry-gallery → 主页卡片自动出现。触发词：「把这首诗做成绘本」「加一首新诗到网页」「GitHub Pages 古诗绘本」「更新古诗绘本馆」「主页卡片换图」。**森哥专属**（奥莉 5 岁半 + 茉莉 1 岁 9 个月的亲子古诗启蒙项目，styyxs/poetry-gallery）。"
version: 2.0.0
author: 小爱 (Hermes Agent)
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [古诗, 儿童绘本, HTML, TTS, GitHub Pages, 国风动漫, deploy]
    related_skills: [mmx-cli, installing-shared-tools]
---

# Poetry Gallery Deploy · 古诗绘本馆端到端部署

> **v2.0.0 · 重构自 ancient-poem-kids-picturebook + kids-illustration-html**
> 
> v1 两个 skill 严重重叠（绘本 HTML 内嵌 vs GitHub Pages 部署），导致 2026-07-29《望洞庭》部署事故（主页 4 张卡片 fallback 到 SVG，森哥痛骂）。
> v2 合并为单 skill、单一入口、单一端到端脚本——以后不会再犯。

## ⚠️ 触发后立即读 `references/mistakes-2026-07-29.md`

**这个 skill 历史上犯过 3 层连环错误**（写在 references 里），不读会重犯。

## 一句话能力

**输入一首古诗的 JSON 配置** → **`deploy.py` 一条龙** → **GitHub Pages 上线，新诗自动出现在 styyxs/poetry-gallery 主页**。

## 标准工作流（5 步·焊死）

```
1. 准备诗 JSON
2. python3 deploy.py <poem.json> --deploy
3. python3 validate.py --online   # 上线后自动校验
4. 等 1-2 分钟 GitHub Pages rebuild
5. 浏览器访问 https://styyxs.github.io/poetry-gallery/ 确认
```

## 仓库信息（硬编码·不查文档）

| 项 | 值 |
|---|---|
| 站点 | https://styyxs.github.io/poetry-gallery/ |
| GitHub 仓库 | styyxs/poetry-gallery |
| gh CLI 路径 | /opt/homebrew/bin/gh |
| 工作目录（生图） | /Users/sengao/AI共享空间/古诗绘本/cards/v2/ |
| poetry-site 本地 | /Users/sengao/WorkBuddy/2026-05-27-13-53-13/poetry-site/ |
| 主页 index.html | /Users/sengao/WorkBuddy/2026-05-27-13-53-13/poetry-site/index.html |

## 触发关键词

- "把这首诗做成绘本"
- "加一首新诗到网页"/"更新古诗绘本馆"
- "GitHub Pages 古诗绘本"
- "主页卡片换图"
- "把 X 这首诗部署到 styyxs"

## 部署脚本清单

| 脚本 | 作用 |
|---|---|
| `scripts/deploy.py` | **主入口**：一条龙（5 张图 + 6 TTS + HTML + WebP + 部署） |
| `scripts/validate.py` | **卡门**：部署前 + 上线后两阶段校验，缺一不放过 |
| `scripts/build_html.py` | 离线 HTML 拼装（deploy.py 内部调用） |
| `scripts/upload_github.py` | gh CLI 上传（deploy.py 内部调用） |

## 完整文件结构

```
poetry-gallery-deploy/
├── SKILL.md                           # 本文件
├── README.md                          # 完整使用文档（老板/agent 都能照着跑）
├── LICENSE                            # MIT
├── examples/
│   ├── 望洞庭.json                    # 完整示例（含 prompt + story + facts）
│   └── 望洞庭_config.json             # 最小配置示例
├── templates/
│   └── poem.json.template             # JSON 模板（字段说明 + 校验规则）
├── scripts/
│   ├── deploy.py                      # ★ 主入口端到端脚本
│   ├── validate.py                    # ★ 卡门校验器
│   ├── build_html.py                  # 拼装离线 HTML（v7 性能优化）
│   ├── upload_github.py               # gh CLI 上传封装
│   └── mmx_helpers.py                 # mmx-cli 调用封装（生图 + TTS + vision 验真）
└── references/
    ├── mistakes-2026-07-29.md         # ★ 必读：3 层根因错误复盘
    ├── poem-prompt-guide.md           # 4 张内页 prompt 模板 + 1 张 card_cover prompt
    ├── color-palettes.md              # 5 套色系锚 + palette 自动选择
    ├── deployment-workflow.md         # GitHub Pages 部署 8 步详细 SOP
    ├── github-pages-quirks.md         # P10-P16 坑位（mmx --out vs --out-prefix / tags 数组 / m4a 等）
    └── cover-card-design.md          # 主页卡片设计标准（虽然是 WebP 不再是 PIL，但骨架仍适用）
```

## 端到端 SOP（deploy.py 一条龙做了什么）

| Step | 动作 | 工具 | 输出 |
|---|---|---|---|
| 1 | 校验 JSON | validate.py | 错误立即退出 |
| 2 | 生 4 张内页插画 | mmx image generate ×4 | img_1-4.webp（800px, q=75）|
| 3 | 生 1 张主页卡片封面 | mmx image generate ×1 | card_cover.webp（1200×675, q=82）|
| 4 | 生 6 段 TTS | mmx speech ×6 | 4 line + 1 story + 1 full_poem |
| 5 | 拼装离线 HTML | build_html.py | 望洞庭_儿童绘本.html（base64 内嵌）|
| 6 | extract_media 拆 base64 | 内联 | 望洞庭_img/*.webp + *.mp3 |
| 7 | 加 illus 字段 | poems.json | 部署前必须 |
| 8 | gh CLI 上传 | upload_github.py | 4 文件 + json + 所有媒体 |
| 9 | 上线后在线校验 | validate.py --online | HTTP 200 全过 |

## 验收硬指标（任何一首诗部署上线后必须全过）

```
[ ] 主页 fetch poems.json → 含 illus 字段
[ ] https://styyxs.github.io/poetry-gallery/poems/<title>.html → 200
[ ] https://styyxs.github.io/poetry-gallery/poems/<title>_img/card_cover.webp → 200
[ ] https://styyxs.github.io/poetry-gallery/poems/<title>_img/img_1-4.webp → 200
[ ] https://styyxs.github.io/poetry-gallery/poems/<title>_img/bg_audio_1-6.mp3 → 200
[ ] 主页渲染该卡片时是 <img src="...card_cover.webp"> 而不是 <svg>
```

任何一项 ❌ → 上线失败，必须修复后重跑。

## 已知已验证诗目

| 诗 | 作者 | 色系 | 文件大小 | 部署状态 |
|---|---|---|---|---|
| 静夜思 | 李白·唐 | 静谧月夜 | 1.2 MB | ✅ 已上线 |
| 望天门山 | 李白·唐 | 春日花朵 | 1.8 MB | ✅ 已上线 |
| 登鹳雀楼 | 王之涣·唐 | 秋日暖阳 | 1.7 MB | ✅ 已上线 |
| 望洞庭 | 刘禹锡·唐 | 静谧月夜 | 2.5 MB | ✅ 已上线 |

未来每跑通一首新诗，请追加此表。

## 反面教材（2026-07-29 事故）

详见 `references/mistakes-2026-07-29.md`。3 层根因：
1. **技能依赖图错过**：误以为 2 个 skill 是同一件事
2. **字段契约没强制**：illus 字段没在 validate.py 里卡死
3. **existing data drift**：之前 illus 字段在某个时间点被清掉过

**修复（v2 已永久焊死）**：
- ✅ 2 个 skill 合并为 1 个
- ✅ validate.py 强制每条 poem 记录必有 illus
- ✅ validate.py 强制 card_cover.webp 在线 HTTP 200

## 不做的事

- ❌ 不要在主页 index.html 用 SVG fallback 渲染卡片
- ❌ 不要在 poems.json 漏 illus 字段
- ❌ 不要没生成 card_cover.webp 就 commit poems.json
- ❌ 不要把 v1 的 2 个 skill（ancient-poem-kids-picturebook / kids-illustration-html）当主 skill 用——它们已废弃