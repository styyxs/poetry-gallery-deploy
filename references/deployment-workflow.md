# GitHub Pages 部署 8 步详细 SOP

## 仓库结构（deploy.py 默认假设）

```
styyxs/poetry-gallery/
├── index.html                  # 主页（含 fetch poems.json JS）
├── poems.json                  # 诗的索引（每条记录必有 illus 字段）
└── poems/
    ├── <title>.html            # 单首绘本 HTML（瘦身后版）
    └── <title>_img/
        ├── img_1.webp          # 第 1 句插画
        ├── img_2.webp          # 第 2 句插画
        ├── img_3.webp
        ├── img_4.webp
        ├── bg_audio_1.mp3      # 第 1 句 TTS
        ├── bg_audio_2.mp3
        ├── bg_audio_3.mp3
        ├── bg_audio_4.mp3
        ├── bg_audio_5.mp3      # 故事
        ├── bg_audio_6.mp3      # 完整诗篇
        └── card_cover.webp     # 主页卡片封面（必须）
```

## 8 步部署流程

### Step 1: 校验 poems.json（卡门 1）

```bash
python3 scripts/validate.py poems.json --local-dir /Users/sengao/WorkBuddy/2026-05-27-13-53-13/poetry-site
```

校验项：
- 每条 poem 记录必有 `illus` 字段
- `illus` 路径以 `poems/<title>_img/card_cover.webp` 结尾
- 对应本地文件存在 + < 100KB

任何一项 ❌ → 不允许 commit。

### Step 2: 上传 poem HTML（瘦身后）

```bash
python3 scripts/upload_github.py \
  /Users/sengao/WorkBuddy/2026-05-27-13-53-13/poetry-site/poems/<title>.html \
  poems/<title>.html \
  "📜 Add <title> children picture book"
```

### Step 3: 上传 card_cover.webp

```bash
python3 scripts/upload_github.py \
  /Users/sengao/WorkBuddy/2026-05-27-13-53-13/poetry-site/poems/<title>_img/card_cover.webp \
  poems/<title>_img/card_cover.webp \
  "🎨 Add <title> card cover"
```

### Step 4: 上传 poems.json

```bash
python3 scripts/upload_github.py \
  /Users/sengao/WorkBuddy/2026-05-27-13-53-13/poetry-site/poems.json \
  poems.json \
  "📋 Update poems index with <title>"
```

### Step 5: 上传媒体文件（批量）

```bash
for f in /Users/sengao/WorkBuddy/2026-05-27-13-53-13/poetry-site/poems/<title>_img/*.{webp,mp3}; do
  python3 scripts/upload_github.py "$f" "poems/<title>_img/$(basename $f)" "🖼️ $(basename $f)"
done
```

### Step 6: 等待 GitHub Pages rebuild（1-2 分钟）

GitHub Pages 自动部署，无须手动操作。

### Step 7: 上线后在线校验（卡门 2）

```bash
python3 scripts/validate.py poems.json --remote https://styyxs.github.io/poetry-gallery
```

校验项：
- poems.json 在线版每条记录有 illus 字段
- card_cover.webp HTTP 200
- <title>.html HTTP 200
- 所有 img_*.webp HTTP 200
- 所有 bg_audio_*.mp3 HTTP 200

### Step 8: 浏览器验真（人工）

打开 https://styyxs.github.io/poetry-gallery/ 确认：
- 主页新卡片出现
- 卡片渲染的是真实插图（不是 SVG）
- 点击新卡片能进绘本页，4 张图 + 6 段音频按钮都正常

## 主页 index.html 的关键 JS（千万别动）

```javascript
fetch('poems.json?'+Date.now())
.then(function(r){return r.json()})
.then(function(poems){
  var g=document.getElementById('gallery');
  poems.forEach(function(p){
    var a=document.createElement('a');a.className='card';a.href=p.file;a.target='_blank';
    // 关键：优先用 illus（真实插图），缺了才 fallback SVG
    var illusHtml=p.illus
      ? '<img loading="lazy" decoding="async" src="'+p.illus+'" alt="'+p.title+'" style="width:100%;height:100%;object-fit:cover;display:block">'
      : pickIllus(p.tags);
    a.innerHTML='<div class="card-illus">'+illusHtml+'</div>'+
      '<div class="card-body">'+
        '<div class="card-title">'+p.title+'</div>'+
        '<div class="card-author">'+p.author+'</div>'+
        '<div class="card-excerpt">'+p.summary+'</div>'+
        '<div class="card-tags">'+p.tags.map(function(t){return'<span class="card-tag">#'+t+'</span>'}).join('')+'</div>'+
      '</div>';
    g.appendChild(a);
  });
})
```

**不要从 index.html 删除 `pickIllus` fallback 逻辑**——保留作系统兜底，但**不允许触发**（validate.py 卡门）。