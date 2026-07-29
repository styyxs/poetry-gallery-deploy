# 4 张内页插画 + 1 张主页卡片封面 的 Prompt 模板

## 一、4 张内页插画（绘本页内嵌·1:1 比例）

每首诗的 4 句诗，每句生成 1 张 1:1 插画。**必须共享同一画风锚前缀**，否则 4 张图风格会漂移。

### 模板 A：4 句绝句

```python
STYLE_ANCHOR = "Children's watercolor picture book illustration, soft pastel mint blue and moonlight silver color palette, macaron tones, rounded shapes, simple and warm, similar to Japanese picture book style by Satoshi Kitamura, no text, white background."

# 每句生图：line1 / line2 / line3 / line4
prompt = f"{STYLE_ANCHOR} {scene_en}"
```

**自检 3 问**：
1. 每张 prompt 都包含同一 `STYLE_ANCHOR` 前缀？（漏了就漂风格）
2. 每张 prompt 末尾都有 `, no text, white background`？（没禁字/禁花背景）
3. 英文场景描述够具体？（至少 3 个名词：人物 + 动作 + 场景细节）

### 示例：《望洞庭》4 张内页 prompt（已实测可用）

```python
# Line 1: 湖光秋月两相和
prompt_1 = f"{STYLE_ANCHOR} A serene wide Chinese lake (Dongting Lake) at autumn night, soft golden moonlight shimmering on the calm water surface, the lake and the sky blending into one silver-blue horizon, a few tiny lotus leaves floating, distant misty mountains in the background, watercolor soft glow"

# Line 2: 潭面无风镜未磨
prompt_2 = f"{STYLE_ANCHOR} A perfectly still unrippled Chinese lake surface at night, acting as a natural mirror that softly reflects the bright full moon and the mountain silhouette, the reflection slightly hazy and dreamy like an unpolished bronze mirror, tiny lotus leaves on the water"

# Line 3: 遥望洞庭山水翠
prompt_3 = f"{STYLE_ANCHOR} A small chubby 5-year-old Chinese boy standing on a wooden boat dock in traditional Hanfu clothes, looking out across a vast jade-green Chinese lake (Dongting Lake), surrounded by lush emerald mountains and dark green pine forests, an old Chinese fisherman silhouette on a tiny wooden boat in the distance, bright full moon rising"

# Line 4: 白银盘里一青螺
prompt_4 = f"{STYLE_ANCHOR} A magical bird's eye view of a round bright full moon reflected as a silver plate on the lake surface, a tiny green cone-shaped island (like an emerald snail) sitting perfectly in the center of the moon's reflection, surrounded by soft silver ripples, dreamy and whimsical scene"
```

### 风格参考作者（可叠加）

| 风格关键词 | 参考作者 | 视觉效果 |
|---|---|---|
| Japanese picture book | Satoshi Kitamura | 水彩 + 圆润 + 童趣 |
| Eric Carle style | Eric Carle | 拼贴 + 鲜艳色块 |
| Kanahei style | Kanahei | Q 萌 + 粉色系 + 治愈 |
| Beatrix Potter style | Beatrix Potter | 暖色 + 写实小动物 |
| Jon Klassen style | Jon Klassen | 极简 + 高级感 + 冷幽默 |
| 中式水墨 | 齐白石 / 吴冠中 | 写意 + 留白 |

---

## 二、1 张主页卡片封面（GitHub Pages 主页·16:9 2K 国风动漫）

**与内页插画风格完全不同**——主页卡片是"国潮 3D 山月风 / 电影级光影"，内页是"水彩日系绘本风"。**不要混用风格**。

### 模板：主页卡片封面（16:9 2K）

```bash
mmx image generate \
  --prompt "国风动漫风格，电影级光影。<诗境描述>。cinematic lighting, traditional Chinese ink painting style merged with modern anime aesthetics, dramatic <诗关键词> scene" \
  --aspect-ratio "16:9" \
  --resolution "2K" \
  --out /path/to/card_cover.jpg
```

### 关键参数（森哥焊死·2026-07-22）

| 参数 | 值 | 原因 |
|---|---|---|
| `--prompt` | 开头必须 "国风动漫风格，电影级光影。" | 国风动漫 + 电影质感 |
| `--aspect-ratio` | `16:9` | 主页卡片宽屏比例 |
| `--resolution` | `2K` | 高清但不过大（4K 太慢且没必要）|
| `--out` | **必须**用 `--out` 不是 `--out-prefix` | 见 github-pages-quirks.md P10 |

### 示例：《望洞庭》card_cover prompt（已实测可用）

```
"国风动漫风格，电影级光影。洞庭湖秋夜的全景图：月亮高悬天空，湖面如未磨的银镜，平静如镜，远处的君山像一颗青绿色的小螺丝静静坐在银盘一样的月亮倒影里。画面要开阔、梦幻、深蓝色调为主，配暖黄色的月光点缀。cinematic lighting, traditional Chinese ink painting style merged with modern anime aesthetics, dramatic moonlit lake scene"
```

### 压缩（deploy.py 自动做）

```python
from PIL import Image
im = Image.open(jpg_path)
w, h = im.size
new_h = int(h * 1200 / w)
im.resize((1200, new_h), Image.LANCZOS).save(
    webp_path, 'WEBP', quality=82, method=6)
```

**目标**：单图 18-65 KB，**绝不超过 100KB**。

---

## 三、TTS 文本（deploy.py 自动从 JSON 拼）

每首诗生成 6 段 TTS：

| 段 | 文本 | 速度 |
|---|---|---|
| line1.mp3 | "{original_1}。{tts_explanation_1}" | 0.85 |
| line2.mp3 | "{original_2}。{tts_explanation_2}" | 0.85 |
| line3.mp3 | "{original_3}。{tts_explanation_3}" | 0.85 |
| line4.mp3 | "{original_4}。{tts_explanation_4}" | 0.85 |
| story.mp3 | "{story_tts}" | 0.85 |
| full_poem.mp3 | "{title}，{dynasty}，{author}。{line1}，{line2}，{line3}，{line4}。" | **0.75** |

**关键约束（P8 坑）**：
- `tts_explanation` 不能带 `\n`（会被读成停顿）
- `story_tts` 不能带 `\n`（同上）
- 完整诗篇保留 `\n` 让节奏感出来
- 音色必须是 `female-shaonv-jingpin`（mmx 系统音色库）

---

## 四、vision 验真（每张图必跑）

```python
# 单图风格验真
mmx vision describe --image line1_001.jpg --prompt "一句话：是不是儿童水彩绘本风？风格统一吗？"

# card_cover 验真
mmx vision describe --image card_cover.jpg --prompt "一句话：是否看到 <诗关键词> 意境？"
```

**vision 反馈 vs 森哥偏好冲突时，听森哥的**（v1 pitfall）。vision 说"偏成人化"不采纳——以森哥参考图为准。