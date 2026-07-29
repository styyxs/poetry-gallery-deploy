#!/usr/bin/env python3
"""build_html.py · 拼装离线 HTML（base64 内嵌）

deploy.py 内部调用
"""
import base64
from pathlib import Path


def to_data_uri(path: Path, mime: str) -> str:
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"


CSS = """
:root {
  --bg-1: #b8e0ff;
  --bg-2: #ffd6e8;
  --bg-3: #fff3a0;
  --card-bg: #ffffff;
  --card-shadow: 0 10px 30px rgba(255, 158, 181, 0.25);
  --ink-primary: #1e4d6b;
  --ink-secondary: #4a7892;
  --ink-soft: #8fb5c9;
  --accent-pink: #ff6b9d;
  --accent-cream: #ffd966;
  --accent-mint: #6bdbb8;
  --accent-yellow: #ffe066;
  --accent-purple: #c8a8ff;
  --accent-blue: #6bb6ff;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  font-weight: 700;
  background: {PAGE_BG};
  background-attachment: fixed;
  color: var(--ink-primary);
  line-height: 1.7;
  -webkit-font-smoothing: antialiased;
  letter-spacing: 1px;
}
.page-wrapper { max-width: 480px; margin: 0 auto; padding: 28px 16px 56px; }

.header-card {
  background: var(--card-bg); border-radius: 32px; padding: 36px 24px 32px;
  text-align: center; box-shadow: var(--card-shadow); margin-bottom: 28px;
  position: relative; overflow: hidden;
}
.header-card::before { content: "🌙"; position: absolute; top: 14px; right: 22px; font-size: 32px; opacity: 0.8; }
.header-card::after  { content: "⭐"; position: absolute; top: 38px; left: 26px; font-size: 18px; opacity: 0.6; }
.header-card .badge {
  display: inline-block; background: var(--accent-pink); color: #fff;
  font-size: 14px; font-weight: 800; padding: 8px 22px; border-radius: 999px;
  margin-bottom: 18px; letter-spacing: 3px;
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.4);
}
.header-card h1 {
  font-size: 52px; font-weight: 900; color: var(--accent-pink); margin-bottom: 14px;
  letter-spacing: 12px;
  text-shadow: 3px 3px 0 var(--accent-yellow), 6px 6px 0 var(--accent-mint);
  transform: rotate(-2deg); display: inline-block;
}
.header-card .author {
  font-size: 20px; font-weight: 800; color: var(--ink-primary); margin-bottom: 4px;
  background: var(--accent-cream); display: inline-block;
  padding: 4px 18px; border-radius: 999px;
}
.header-card .dynasty { font-size: 13px; font-weight: 600; color: var(--ink-soft); letter-spacing: 1px; }

.poem-card {
  background: var(--card-bg); border-radius: 28px; padding: 14px 14px 22px;
  margin-bottom: 22px; box-shadow: var(--card-shadow);
}
.poem-illustration {
  position: relative; width: 100%; aspect-ratio: 4/3;
  border-radius: 20px; overflow: hidden;
  background: linear-gradient(135deg, #f0f8ff, #fce7f3); margin-bottom: 16px;
}
.poem-illustration img { width: 100%; height: 100%; object-fit: cover; display: block; }
.line-badge {
  position: absolute; top: 12px; left: 12px;
  background: rgba(255, 255, 255, 0.92); color: var(--ink-primary);
  font-size: 13px; font-weight: 700; padding: 5px 14px; border-radius: 999px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08); letter-spacing: 1px;
}
.poem-text { padding: 0 8px; text-align: center; }
.line-original {
  font-size: 32px; font-weight: 900; color: var(--accent-pink);
  margin-bottom: 10px; letter-spacing: 6px;
  text-shadow: 2px 2px 0 var(--accent-yellow); display: inline-block;
}
.line-translation {
  font-size: 17px; font-weight: 600; color: var(--ink-secondary);
  line-height: 1.7; margin-bottom: 16px;
}

.play-btn {
  display: inline-flex; align-items: center; gap: 8px;
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
  color: #fff; font-size: 15px; font-weight: 800;
  padding: 10px 22px; border: none; border-radius: 999px; cursor: pointer;
  box-shadow: 0 4px 12px rgba(107, 182, 255, 0.4);
  transition: transform 0.2s, box-shadow 0.2s; letter-spacing: 1px;
}
.play-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(107, 182, 255, 0.5); }
.play-btn:active { transform: translateY(0); }
.play-btn.playing {
  background: linear-gradient(135deg, var(--accent-pink), var(--accent-yellow));
  animation: pulse 1s infinite;
}
.play-btn .play-icon { font-size: 18px; }
@keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }

.story-card {
  background: linear-gradient(135deg, #ffffff 0%, #fff8f3 100%);
  border-radius: 28px; padding: 28px 24px; margin-bottom: 24px;
  box-shadow: var(--card-shadow); position: relative;
}
.story-card::before {
  content: "📖"; position: absolute; top: -14px; left: 24px;
  font-size: 28px; background: var(--card-bg); padding: 0 6px; border-radius: 50%;
}
.story-card .story-head {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px; flex-wrap: wrap; gap: 10px;
}
.story-card h2 {
  font-size: 24px; font-weight: 900; color: var(--accent-pink);
  letter-spacing: 3px; text-shadow: 2px 2px 0 var(--accent-yellow);
}
.story-card p {
  font-size: 16px; font-weight: 600; color: var(--ink-secondary);
  white-space: pre-line; line-height: 2; text-indent: 2em;
}

.facts-section h2 {
  font-size: 24px; font-weight: 900; color: var(--accent-pink);
  margin-bottom: 18px; text-align: center; letter-spacing: 3px;
  text-shadow: 2px 2px 0 var(--accent-yellow);
}
.fact-card {
  background: var(--card-bg); border-radius: 24px; padding: 20px 22px;
  margin-bottom: 14px; box-shadow: var(--card-shadow);
  display: flex; gap: 16px; align-items: flex-start;
}
.fact-emoji {
  flex-shrink: 0; font-size: 36px; width: 60px; height: 60px;
  background: var(--accent-yellow); border-radius: 20px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 12px rgba(255, 158, 181, 0.3);
}
.fact-card:nth-child(2) .fact-emoji { background: var(--accent-mint); }
.fact-card:nth-child(3) .fact-emoji { background: var(--accent-pink); }
.fact-card:nth-child(4) .fact-emoji { background: var(--accent-purple); }
.fact-text { flex: 1; min-width: 0; }
.fact-title { font-size: 18px; font-weight: 800; color: var(--ink-primary); margin-bottom: 6px; letter-spacing: 1px; }
.fact-body { font-size: 14px; font-weight: 500; color: var(--ink-secondary); line-height: 1.7; }

.full-poem-card {
  background: linear-gradient(135deg, #fff8f3 0%, #fce7f3 100%);
  border-radius: 28px; padding: 32px 24px; margin-bottom: 24px;
  box-shadow: var(--card-shadow); text-align: center; position: relative;
}
.full-poem-card::before {
  content: "🌟"; position: absolute; top: -16px; left: 50%;
  transform: translateX(-50%); font-size: 32px;
  background: var(--card-bg); padding: 0 8px; border-radius: 50%;
}
.full-poem-card h2 {
  font-size: 24px; font-weight: 900; color: var(--accent-pink);
  margin-bottom: 16px; letter-spacing: 4px;
  text-shadow: 2px 2px 0 var(--accent-yellow);
}
.full-poem-meta {
  font-size: 16px; font-weight: 700; color: var(--ink-secondary);
  margin-bottom: 24px; letter-spacing: 2px;
  background: var(--accent-cream); display: inline-block;
  padding: 6px 18px; border-radius: 999px;
}
.full-poem-text {
  font-size: 28px; font-weight: 800; color: var(--ink-primary);
  line-height: 2.2; letter-spacing: 6px; margin-bottom: 24px;
}
.full-poem-text .line { display: block; padding: 6px 0; }
.play-btn-big {
  display: inline-flex; align-items: center; gap: 10px;
  background: linear-gradient(135deg, var(--accent-pink), var(--accent-yellow));
  color: #fff; font-size: 18px; font-weight: 900;
  padding: 14px 32px; border: none; border-radius: 999px; cursor: pointer;
  box-shadow: 0 6px 18px rgba(255, 107, 157, 0.5); letter-spacing: 2px;
  transition: transform 0.2s, box-shadow 0.2s;
}
.play-btn-big:hover { transform: translateY(-2px); box-shadow: 0 8px 22px rgba(255, 107, 157, 0.6); }
.play-btn-big .play-icon { font-size: 22px; }

.footer { text-align: center; margin-top: 36px; font-size: 13px; font-weight: 600; color: var(--ink-soft); }
.footer .badge-local {
  display: inline-block; background: rgba(255, 255, 255, 0.7);
  padding: 6px 16px; border-radius: 999px;
  border: 1.5px dashed var(--accent-pink); margin-top: 10px; color: var(--ink-secondary);
}

@media (max-width: 540px) {
  .page-wrapper { padding: 16px 12px 36px; }
  .header-card h1 { font-size: 40px; letter-spacing: 8px; }
  .header-card .author { font-size: 18px; }
}
"""

JS = """
(function() {
  let currentAudio = null, currentBtn = null;
  document.querySelectorAll('.play-btn, .play-btn-big').forEach(btn => {
    btn.addEventListener('click', function() {
      const audioId = this.getAttribute('data-audio');
      const audio = document.getElementById(audioId);
      if (!audio) return;
      if (currentAudio === audio && !audio.paused) {
        audio.pause();
        resetBtn();
        return;
      }
      if (currentAudio && currentAudio !== audio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        resetBtn();
      }
      audio.currentTime = 0;
      audio.play().then(() => {
        currentAudio = audio;
        currentBtn = this;
        this.classList.add('playing');
        const t = this.querySelector('.play-text');
        if (t) t.textContent = '播放中…';
      }).catch(err => console.error('播放失败:', err));
      audio.onended = () => resetBtn();
    });
  });
  function resetBtn() {
    if (currentBtn) {
      currentBtn.classList.remove('playing');
      const t = currentBtn.querySelector('.play-text');
      if (t) {
        if (currentBtn.classList.contains('play-btn-big')) t.textContent = '完整朗读一遍';
        else if (currentBtn.getAttribute('data-audio') === 'audioStory') t.textContent = '听故事';
        else t.textContent = '点我听讲解';
      }
      currentAudio = null;
      currentBtn = null;
    }
  }
})();
"""


def build_html(poem: dict, workdir: Path, palette_name: str, color_palettes: dict) -> str:
    """拼装完整 HTML"""
    title = poem["title"]
    author = poem["author"]
    dynasty = poem["dynasty"]
    page_bg = color_palettes.get(palette_name, color_palettes["静谧月夜"])["page_bg"]

    # 4 句诗
    lines_html_parts = []
    for i, line in enumerate(poem["lines"], 1):
        img_uri = to_data_uri(workdir / f"line{i}.webp", "image/webp")
        audio_uri = to_data_uri(workdir / f"line{i}.mp3", "audio/mpeg")
        audio_id = f"audio{i}"

        lines_html_parts.append(f"""
    <section class="poem-card">
      <div class="poem-illustration">
        <img src="{img_uri}" alt="第 {i} 句插画" loading="lazy" decoding="async">
        <span class="line-badge">第 {i} 句</span>
      </div>
      <div class="poem-text">
        <h2 class="line-original">{line['original']}</h2>
        <p class="line-translation">{line['translation']}</p>
        <button class="play-btn" data-audio="{audio_id}" aria-label="朗读第 {i} 句">
          <span class="play-icon">🔊</span>
          <span class="play-text">点我听讲解</span>
        </button>
        <audio id="{audio_id}" preload="none">
          <source src="{audio_uri}" type="audio/mpeg">
        </audio>
      </div>
    </section>
        """)
    lines_html = "".join(lines_html_parts)

    story = poem["story"]
    story_audio_uri = to_data_uri(workdir / "story.mp3", "audio/mpeg")

    facts_html_parts = []
    for f in poem["facts"]:
        facts_html_parts.append(f"""
    <div class="fact-card">
      <div class="fact-emoji">{f['emoji']}</div>
      <div class="fact-text">
        <h3 class="fact-title">{f['title']}</h3>
        <p class="fact-body">{f['body']}</p>
      </div>
    </div>
        """)
    facts_html = "".join(facts_html_parts)

    full_poem_meta = f"《{title}》 · {dynasty} · {author}"
    full_audio_uri = to_data_uri(workdir / "full_poem.mp3", "audio/mpeg")
    full_poem_lines_html = "\n      ".join(
        f'<span class="line">{line["original"]}</span>' for line in poem["lines"]
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · 儿童绘本</title>
<style>{CSS.replace("{PAGE_BG}", page_bg)}</style>
</head>
<body>
<div class="page-wrapper">

  <header class="header-card">
    <span class="badge">📖 儿童绘本</span>
    <h1>{title}</h1>
    <div class="author">{author}</div>
    <div class="dynasty">{dynasty}</div>
  </header>

  {lines_html}

  <section class="story-card">
    <div class="story-head">
      <h2>诗人小故事</h2>
      <button class="play-btn" data-audio="audioStory" aria-label="朗读诗人故事">
        <span class="play-icon">🎙️</span>
        <span class="play-text">听故事</span>
      </button>
    </div>
    <p>{story}</p>
    <audio id="audioStory" preload="none">
      <source src="{story_audio_uri}" type="audio/mpeg">
    </audio>
  </section>

  <section class="facts-section">
    <h2>✨ 古诗小知识</h2>
    {facts_html}
  </section>

  <section class="full-poem-card">
    <h2>🌙 完整诗篇 🌙</h2>
    <div class="full-poem-meta">{full_poem_meta}</div>
    <div class="full-poem-text">
      {full_poem_lines_html}
    </div>
    <button class="play-btn-big" data-audio="audioFull" aria-label="完整朗读这首诗">
      <span class="play-icon">📖</span>
      <span class="play-text">完整朗读一遍</span>
    </button>
    <audio id="audioFull" preload="none">
      <source src="{full_audio_uri}" type="audio/mpeg">
    </audio>
  </section>

  <footer class="footer">
    <div>为奥莉和茉莉精心制作 🌸</div>
    <div class="badge-local">💾 本地离线绘本 · 双击即可阅读</div>
  </footer>

</div>
<script>{JS}</script>
</body>
</html>
"""
    return html