#!/usr/bin/env python3
"""
Family Daily Reader — Daily Article Generator
每天自動為四位家人生成不同程度的英文閱讀文章，並產生網頁。
"""

import os
import json
import urllib.request
import urllib.error
import datetime
import re
import sys
import time

# ── Config ────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "docs")
TODAY = datetime.date.today().isoformat()

# ── Member Profiles ────────────────────────────────────────────────────────────
MEMBERS = [
    {
        "id": "tony",
        "name": "Tony",
        "icon": "📰",
        "color": "#c0392b",
        "badge": "B2–C1 · FLPT",
        "storage_key": "daily_tony",
        "prompt": f"""You are an expert FLPT tutor. Generate a B2-C1 level English reading article for a Taiwanese military officer targeting FLPT 220-240+ score.

REQUIREMENTS:
- Length: 350–420 words, analytical essay style
- Topics: rotate among geopolitics, military technology, US-China-Taiwan relations, cybersecurity, international security, global economics
- Style: The Economist / Foreign Affairs — analytical, precise, sophisticated
- Grammar: naturally include inversion, subjunctive mood, nominalization, participial constructions
- Vocabulary: B2-C1 CEFR, 8 vocabulary items

OUTPUT FORMAT (exact markers required):
===TITLE===
[Headline in Standard Title Case]
===ARTICLE===
[350-420 word essay, paragraphs only]
===TRANSLATION===
[Full Traditional Chinese translation, professional quality]
===VOCAB===
[8 items, one per line: WORD|/IPA/|English definition|中文意思|Example sentence]
===QUIZ===
Q1: [Inference question]
A) B) C) D)
ANSWER: [letter]
EXPLANATION_EN: [2-3 sentences]
EXPLANATION_ZH: [2-3 sentences in Traditional Chinese]
Q2: [Author's purpose or implication question]
A) B) C) D)
ANSWER: [letter]
EXPLANATION_EN: [2-3 sentences]
EXPLANATION_ZH: [2-3 sentences in Traditional Chinese]

Today's date: {TODAY}. All Chinese must be Traditional Chinese (正體中文)."""
    },
    {
        "id": "angel",
        "name": "Angel",
        "icon": "🌸",
        "color": "#7d3c98",
        "badge": "B2–C1",
        "storage_key": "daily_angel",
        "prompt": f"""You are a thoughtful English teacher. Generate a B2-C1 level English reading article for an adult female reader who enjoys a wide variety of topics.

REQUIREMENTS:
- Length: 280–350 words, engaging magazine style
- Topics: rotate broadly — lifestyle, health & wellness, travel & culture, food, parenting & family, design & arts, psychology, social trends, technology in daily life, environmental issues, human interest stories
- Style: Intelligent general-interest magazine (The Atlantic, BBC Culture, Vogue International feature)
- Tone: warm, thoughtful, intellectually engaging — not stiff academic, not superficial
- Vocabulary: B2-C1, natural and expressive, 6 vocabulary items

OUTPUT FORMAT (exact markers required):
===TITLE===
[Engaging headline in Standard Title Case]
===ARTICLE===
[280-350 word article, flowing paragraphs]
===TRANSLATION===
[Full Traditional Chinese translation, natural and expressive]
===VOCAB===
[6 items, one per line: WORD|/IPA/|English definition|中文意思|Example sentence]
===QUIZ===
Q1: [Comprehension or inference question]
A) B) C) D)
ANSWER: [letter]
EXPLANATION_EN: [2 sentences]
EXPLANATION_ZH: [2 sentences in Traditional Chinese]
Q2: [What does the author imply or suggest?]
A) B) C) D)
ANSWER: [letter]
EXPLANATION_EN: [2 sentences]
EXPLANATION_ZH: [2 sentences in Traditional Chinese]

Today's date: {TODAY}. All Chinese must be Traditional Chinese (正體中文). Never repeat the same topic area as yesterday."""
    },
    {
        "id": "jill",
        "name": "Jill",
        "icon": "📖",
        "color": "#16a085",
        "badge": "B2 · 國高中",
        "storage_key": "daily_jill",
        "prompt": f"""You are an engaging English teacher for Taiwanese junior/senior high school students. Generate a B2 level English reading article.

REQUIREMENTS:
- Length: 220–280 words
- Topics: rotate among environment & nature, technology & social media, cross-cultural understanding, youth issues, sports & achievement, science discoveries, current events (simplified)
- Style: Clear, engaging, educational — like a good school magazine article
- Vocabulary: B1-B2 CEFR, accessible but stretching, 6 vocabulary items
- Grammar: varied sentences, some complex structures, but readable

OUTPUT FORMAT (exact markers required):
===TITLE===
[Clear engaging headline]
===ARTICLE===
[220-280 words, clear paragraphs]
===TRANSLATION===
[Full Traditional Chinese translation, natural for a student]
===VOCAB===
[6 items, one per line: WORD|/IPA/|English definition|中文意思|Example sentence]
===QUIZ===
Q1: [Main idea or key detail question]
A) B) C) D)
ANSWER: [letter]
EXPLANATION_EN: [1-2 sentences]
EXPLANATION_ZH: [1-2 sentences in Traditional Chinese]
Q2: [Inference — what can we understand from the article?]
A) B) C) D)
ANSWER: [letter]
EXPLANATION_EN: [1-2 sentences]
EXPLANATION_ZH: [1-2 sentences in Traditional Chinese]

Today's date: {TODAY}. All Chinese must be Traditional Chinese (正體中文)."""
    },
    {
        "id": "guan",
        "name": "Guan",
        "icon": "🚀",
        "color": "#2980b9",
        "badge": "A2–B1 · 國小高年級—國中",
        "storage_key": "daily_guan",
        "prompt": f"""You are a fun and encouraging English teacher for Taiwanese upper elementary to junior high school students (ages 11-14, A2-B1 level). Generate an engaging English reading article.

REQUIREMENTS:
- Length: 150–200 words
- Topics: rotate among animals & nature, sports & games, food & cooking, science experiments & discoveries, adventures & travel, school life, technology kids use, interesting facts about the world
- Style: Fun, clear, encouraging — like a great children's magazine (National Geographic Kids level)
- Vocabulary: A2-B1 CEFR, simple and clear, 6 vocabulary items with simple definitions
- Sentences: mostly short to medium, active voice, concrete and vivid

OUTPUT FORMAT (exact markers required):
===TITLE===
[Fun, catchy headline]
===ARTICLE===
[150-200 words, short clear paragraphs]
===TRANSLATION===
[Full Traditional Chinese translation, friendly and natural for a student aged 11-14]
===VOCAB===
[6 items, one per line: WORD|/IPA/|Simple English definition|中文意思|Simple example sentence]
===QUIZ===
Q1: [Simple comprehension question about a key fact in the article]
A) B) C) D)
ANSWER: [letter]
EXPLANATION_EN: [1 sentence, simple language]
EXPLANATION_ZH: [1 sentence in Traditional Chinese]
Q2: [Fun inference question — what do you think?]
A) B) C) D)
ANSWER: [letter]
EXPLANATION_EN: [1 sentence]
EXPLANATION_ZH: [1 sentence in Traditional Chinese]

Today's date: {TODAY}. All Chinese must be Traditional Chinese (正體中文). Make it fun and encouraging!"""
    }
]

# ── Gemini API Call ────────────────────────────────────────────────────────────
def call_gemini(prompt: str, max_retries: int = 5) -> str:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set")

    payload = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "temperature": 0.85
    }).encode("utf-8")

    delay = 30  # initial backoff in seconds for 429 errors
    for attempt in range(max_retries):
        req = urllib.request.Request(
            GROQ_URL,
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                if attempt < max_retries - 1:
                    print(f"  ⏳ Rate limited (429). Waiting {delay}s before retry {attempt + 1}/{max_retries - 1}...", file=sys.stderr)
                    time.sleep(delay)
                    delay *= 2  # exponential backoff
                else:
                    raise
            else:
                raise

# ── Parse Response ─────────────────────────────────────────────────────────────
def parse_response(raw: str) -> dict:
    def extract(tag: str) -> str:
        pattern = rf"==={tag}===(.*?)(?====\w+===|$)"
        m = re.search(pattern, raw, re.DOTALL)
        return m.group(1).strip() if m else ""

    title       = extract("TITLE")
    article     = extract("ARTICLE")
    translation = extract("TRANSLATION")
    vocab_raw   = extract("VOCAB")
    quiz_raw    = extract("QUIZ")

    # Parse vocab
    vocab_items = []
    for line in vocab_raw.strip().split("\n"):
        parts = line.strip().split("|")
        if len(parts) >= 5:
            vocab_items.append({
                "word": parts[0].strip(),
                "ipa":  parts[1].strip(),
                "en":   parts[2].strip(),
                "zh":   parts[3].strip(),
                "ex":   parts[4].strip()
            })

    # Parse quiz
    quiz_items = []
    questions = re.split(r'Q\d+:', quiz_raw)[1:]
    for q_block in questions:
        lines = [l.strip() for l in q_block.strip().split("\n") if l.strip()]
        if not lines:
            continue
        q_text = lines[0]
        opts, answer, exp_en, exp_zh = {}, "", "", ""
        for line in lines[1:]:
            m = re.match(r'^([A-D])\)\s*(.*)', line)
            if m:
                opts[m.group(1)] = m.group(2)
            elif line.startswith("ANSWER:"):
                answer = line.replace("ANSWER:", "").strip()
            elif line.startswith("EXPLANATION_EN:"):
                exp_en = line.replace("EXPLANATION_EN:", "").strip()
            elif line.startswith("EXPLANATION_ZH:"):
                exp_zh = line.replace("EXPLANATION_ZH:", "").strip()
        quiz_items.append({"q": q_text, "opts": opts, "answer": answer,
                           "exp_en": exp_en, "exp_zh": exp_zh})

    return {"title": title, "article": article, "translation": translation,
            "vocab": vocab_items, "quiz": quiz_items}

# ── Generate Member HTML Page ──────────────────────────────────────────────────
def generate_member_html(member: dict, data: dict) -> str:
    color  = member["color"]
    name   = member["name"]
    icon   = member["icon"]
    badge  = member["badge"]
    skey   = member["storage_key"]

    # Build vocab HTML
    vocab_html = ""
    for v in data["vocab"]:
        vocab_html += f"""
        <div class="vocab-card">
          <div class="vocab-word">{v['word']} <span class="vocab-ipa">{v['ipa']}</span></div>
          <div class="vocab-def">{v['en']}</div>
          <div class="vocab-zh">{v['zh']}</div>
          <div class="vocab-ex">"{v['ex']}"</div>
        </div>"""

    # Build quiz HTML
    quiz_html = ""
    for i, q in enumerate(data["quiz"], 1):
        opts_html = ""
        for letter, text in q["opts"].items():
            opts_html += f"""
            <label class="opt-label" data-letter="{letter}">
              <input type="radio" name="q{i}" value="{letter}"> {letter}) {text}
            </label>"""
        quiz_html += f"""
        <div class="quiz-item" id="quiz-{i}" data-answer="{q['answer']}"
             data-exp-en="{q['exp_en'].replace('"','&quot;')}"
             data-exp-zh="{q['exp_zh'].replace('"','&quot;')}">
          <div class="quiz-q">Q{i}. {q['q']}</div>
          <div class="quiz-opts">{opts_html}</div>
          <div class="quiz-exp" id="exp-{i}" style="display:none"></div>
        </div>"""

    article_paragraphs = "".join(f"<p>{p}</p>" for p in data["article"].split("\n") if p.strip())
    translation_paragraphs = "".join(f"<p>{p}</p>" for p in data["translation"].split("\n") if p.strip())

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>{name} · {TODAY}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
<style>
  :root {{
    --accent: {color};
    --bg: #faf9f7;
    --card: #ffffff;
    --ink: #1a1a1a;
    --muted: #6b6b6b;
    --border: #e8e4de;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Source Serif 4', serif;
    background: var(--bg);
    color: var(--ink);
    line-height: 1.75;
    font-size: 17px;
  }}
  .top-bar {{
    background: var(--accent);
    color: #fff;
    padding: 14px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    position: sticky;
    top: 0;
    z-index: 100;
  }}
  .top-bar-left {{ display: flex; align-items: center; gap: 10px; }}
  .top-bar a {{ color: rgba(255,255,255,.8); text-decoration: none; font-size: 14px; }}
  .top-bar a:hover {{ color: #fff; }}
  .top-bar h1 {{ font-size: 17px; font-family: 'Playfair Display', serif; }}
  .badge {{
    background: rgba(255,255,255,.2);
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 12px;
    white-space: nowrap;
  }}
  .btn-zh {{
    background: rgba(255,255,255,.15);
    border: 1px solid rgba(255,255,255,.4);
    color: #fff;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13px;
    cursor: pointer;
    font-family: 'Source Serif 4', serif;
    transition: background .15s;
  }}
  .btn-zh:hover {{ background: rgba(255,255,255,.25); }}
  .wrap {{ max-width: 720px; margin: 0 auto; padding: 32px 20px 80px; }}
  .article-date {{ color: var(--muted); font-size: 13px; margin-bottom: 8px; text-transform: uppercase; letter-spacing: .5px; }}
  .article-title {{
    font-family: 'Playfair Display', serif;
    font-size: clamp(24px, 5vw, 36px);
    line-height: 1.25;
    margin-bottom: 28px;
    color: var(--ink);
  }}
  .divider {{ border: none; border-top: 2px solid var(--accent); margin: 28px 0; opacity: .25; }}
  .section-label {{
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--accent);
    font-weight: 600;
    margin-bottom: 14px;
  }}
  .article-body p {{ margin-bottom: 1.1em; }}
  .translation-wrap {{
    background: #f5f3ef;
    border-left: 3px solid var(--accent);
    padding: 20px;
    border-radius: 0 8px 8px 0;
    margin: 24px 0;
    display: none;
  }}
  .translation-wrap p {{ margin-bottom: .9em; color: #333; font-size: 15.5px; }}
  .vocab-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; margin-top: 4px; }}
  .vocab-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 16px;
    border-top: 3px solid var(--accent);
  }}
  .vocab-word {{ font-size: 18px; font-weight: 600; color: var(--ink); }}
  .vocab-ipa {{ font-size: 13px; color: var(--muted); font-weight: 400; }}
  .vocab-def {{ font-size: 13.5px; color: #444; margin-top: 4px; }}
  .vocab-zh {{ font-size: 13px; color: var(--accent); margin-top: 2px; font-weight: 600; }}
  .vocab-ex {{ font-size: 13px; color: var(--muted); margin-top: 6px; font-style: italic; }}
  .quiz-item {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 20px; margin-bottom: 16px; }}
  .quiz-q {{ font-weight: 600; margin-bottom: 14px; font-size: 15.5px; }}
  .quiz-opts {{ display: flex; flex-direction: column; gap: 10px; }}
  .opt-label {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    cursor: pointer;
    padding: 10px 14px;
    border-radius: 8px;
    border: 1px solid var(--border);
    font-size: 14.5px;
    transition: background .12s;
  }}
  .opt-label:hover {{ background: #f5f3ef; }}
  .opt-label.correct {{ background: #eafaf1; border-color: #a9dfbf; color: #1e8449; }}
  .opt-label.wrong   {{ background: #fdf2f2; border-color: #f5b7b1; color: #922b21; }}
  .quiz-exp {{
    margin-top: 14px;
    background: #f9f8f6;
    border-radius: 8px;
    padding: 14px 16px;
    font-size: 14px;
    line-height: 1.65;
    border-left: 3px solid var(--accent);
  }}
  .quiz-exp .exp-en {{ color: #333; margin-bottom: 8px; }}
  .quiz-exp .exp-zh {{ color: #555; }}
  .score-banner {{
    padding: 14px 20px;
    border-radius: 8px;
    text-align: center;
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 20px;
    display: none;
  }}
  .score-banner.great {{ background: #eafaf1; color: #1e8449; border: 1.5px solid #a9dfbf; }}
  .score-banner.ok    {{ background: #fef9e7; color: #9a7d0a; border: 1.5px solid #f9e79f; }}
  .score-banner.retry {{ background: #fdf2f2; color: #922b21; border: 1.5px solid #f5b7b1; }}
  .action-bar {{ margin-top: 20px; }}
  .btn-submit {{
    background: var(--accent);
    color: #fff;
    border: none;
    padding: 13px 32px;
    border-radius: 8px;
    font-size: 16px;
    font-family: 'Source Serif 4', serif;
    cursor: pointer;
    transition: opacity .15s;
  }}
  .btn-submit:disabled {{ opacity: .4; cursor: not-allowed; }}
  .next-bar {{
    display: none;
    text-align: center;
    margin-top: 40px;
    padding-bottom: 20px;
  }}
  .btn-next {{
    background: var(--accent);
    color: #fff;
    border: none;
    padding: 18px 48px;
    border-radius: 50px;
    font-size: 20px;
    font-family: 'Source Serif 4', serif;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 18px rgba(0,0,0,.15);
    transition: transform .15s;
    display: inline-block;
  }}
  .btn-next:hover {{ transform: scale(1.04); }}
  .stats-bar {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 18px;
    display: flex;
    gap: 24px;
    font-size: 13px;
    color: var(--muted);
    margin-bottom: 28px;
    flex-wrap: wrap;
  }}
  .stats-bar strong {{ color: var(--ink); }}
</style>
</head>
<body>

<div class="top-bar">
  <div class="top-bar-left">
    <a href="index.html">← 返回</a>
    <h1>{icon} {name}</h1>
    <span class="badge">{badge}</span>
  </div>
  <button class="btn-zh" onclick="toggleZh(this)">🈶 顯示中文</button>
</div>

<div class="wrap">

  <div class="stats-bar">
    <span>已讀 <strong id="s-count">0</strong> 篇</span>
    <span>答對率 <strong id="s-rate">—</strong></span>
  </div>

  <div class="article-date">{TODAY} · Daily Article</div>
  <h2 class="article-title">{data['title']}</h2>

  <div class="section-label">📰 English Article</div>
  <div class="article-body">{article_paragraphs}</div>

  <div class="translation-wrap" id="translation-wrap">
    <div class="section-label">🈶 中文翻譯</div>
    {translation_paragraphs}
  </div>

  <hr class="divider">

  <div class="section-label">📚 Key Vocabulary</div>
  <div class="vocab-grid">{vocab_html}</div>

  <hr class="divider">

  <div class="section-label">✏️ Reading Quiz</div>
  <div class="score-banner" id="score-banner"></div>
  {quiz_html}
  <div class="action-bar">
    <button class="btn-submit" id="btn-submit" onclick="submitQuiz()" disabled>提交答案</button>
  </div>
  <div class="next-bar" id="next-bar">
    <a href="index.html" class="btn-next">今日已完成 ✓</a>
  </div>

</div>

<script>
const STORAGE_KEY = '{skey}';
let state = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{"count":0,"totalQ":0,"correctQ":0}}');
let quizSubmitted = false;

// Update stats display
function updateStats() {{
  document.getElementById('s-count').textContent = state.count;
  const rate = state.totalQ > 0 ? Math.round(state.correctQ / state.totalQ * 100) + '%' : '—';
  document.getElementById('s-rate').textContent = rate;
}}
updateStats();

// Mark article as read
if (!localStorage.getItem(STORAGE_KEY + '_{TODAY}')) {{
  state.count++;
  localStorage.setItem(STORAGE_KEY + '_{TODAY}', '1');
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  updateStats();
}}

function toggleZh(btn) {{
  const wrap = document.getElementById('translation-wrap');
  const show = wrap.style.display === 'none' || wrap.style.display === '';
  wrap.style.display = show ? 'block' : 'none';
  btn.textContent = show ? '🈶 隱藏中文' : '🈶 顯示中文';
}}

// Quiz logic
document.querySelectorAll('input[type=radio]').forEach(radio => {{
  radio.addEventListener('change', () => {{
    const allAnswered = document.querySelectorAll('.quiz-item').length ===
      [...document.querySelectorAll('.quiz-item')].filter(qi =>
        qi.querySelector('input[type=radio]:checked')).length;
    document.getElementById('btn-submit').disabled = !allAnswered;
  }});
}});

function submitQuiz() {{
  if (quizSubmitted) return;
  quizSubmitted = true;
  let correct = 0, total = 0;

  document.querySelectorAll('.quiz-item').forEach(qi => {{
    total++;
    const answer = qi.dataset.answer;
    const expEn = qi.dataset.expEn;
    const expZh = qi.dataset.expZh;
    const selected = qi.querySelector('input[type=radio]:checked');
    const userAnswer = selected ? selected.value : '';

    qi.querySelectorAll('.opt-label').forEach(label => {{
      label.querySelector('input').disabled = true;
      if (label.dataset.letter === answer) label.classList.add('correct');
      else if (label.dataset.letter === userAnswer && userAnswer !== answer)
        label.classList.add('wrong');
    }});

    const expDiv = qi.querySelector('.quiz-exp');
    expDiv.style.display = 'block';
    expDiv.innerHTML = `<div class="exp-en">📌 ${{expEn}}</div><div class="exp-zh">📌 ${{expZh}}</div>`;

    if (userAnswer === answer) correct++;
  }});

  state.totalQ += total;
  state.correctQ += correct;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  updateStats();

  const banner = document.getElementById('score-banner');
  banner.style.display = 'block';
  if (correct === total) {{
    banner.className = 'score-banner great';
    banner.textContent = `🎉 全對！${{correct}} / ${{total}}`;
  }} else if (correct >= total / 2) {{
    banner.className = 'score-banner ok';
    banner.textContent = `👍 答對 ${{correct}} / ${{total}}`;
  }} else {{
    banner.className = 'score-banner retry';
    banner.textContent = `📖 答對 ${{correct}} / ${{total}}，再讀一遍吧！`;
  }}

  document.getElementById('btn-submit').style.display = 'none';
  document.getElementById('next-bar').style.display = 'block';
  document.getElementById('next-bar').scrollIntoView({{behavior:'smooth', block:'center'}});
}}
</script>
</body>
</html>"""

# ── Generate Index Page ────────────────────────────────────────────────────────
def generate_index_html(members: list, results: dict) -> str:
    cards_html = ""
    for m in members:
        mid = m["id"]
        success = results.get(mid, False)
        if success:
            link = f"{mid}_{TODAY}.html"
            status = "✅ 今日文章已就緒"
            clickable = f'href="{link}"'
            tag = "a"
        else:
            link = "#"
            status = "⚠️ 今日文章生成失敗"
            clickable = ""
            tag = "div"

        cards_html += f"""
  <{tag} class="card" {clickable} style="--c:{m['color']}">
    <div class="card-icon">{m['icon']}</div>
    <div class="card-badge">{m['badge']}</div>
    <h2>{m['name']}</h2>
    <div class="card-status">{status}</div>
    <div class="card-stats">
      <span>已讀 <strong id="c-{mid}">—</strong> 篇</span>
      <span>答對率 <strong id="r-{mid}">—</strong></span>
    </div>
  </{tag}>"""

    # Build archive list
    archive_items = ""
    existing = sorted([
        f for f in os.listdir(OUTPUT_DIR)
        if re.match(r'tony_\d{4}-\d{2}-\d{2}\.html', f)
    ], reverse=True)
    for fname in existing[:14]:
        date = re.search(r'(\d{4}-\d{2}-\d{2})', fname).group(1)
        is_today = "🔴 " if date == TODAY else ""
        archive_items += f'<li>{is_today}<a href="tony_{date}.html">{date}</a> · '
        for m in members:
            mid = m["id"]
            mfile = f"{mid}_{date}.html"
            if os.path.exists(os.path.join(OUTPUT_DIR, mfile)):
                archive_items += f'<a href="{mfile}">{m["icon"]}</a> '
        archive_items += "</li>\n"

    storage_keys = ", ".join([f"'{m['storage_key']}'" for m in members])
    ids = [(m["id"], m["storage_key"]) for m in members]
    stats_js = "\n".join([
        f"""  (()=>{{const s=JSON.parse(localStorage.getItem('{sk}')||'{{"count":0,"totalQ":0,"correctQ":0}}');
  const ce=document.getElementById('c-{mid}');
  const re=document.getElementById('r-{mid}');
  if(ce)ce.textContent=s.count+' 篇';
  if(re)re.textContent=s.totalQ>0?Math.round(s.correctQ/s.totalQ*100)+'%':'—';
}})();""" for mid, sk in ids
    ])

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>Family Daily Reader</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Source Serif 4',serif;background:#0f1117;color:#e8e6e0;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:48px 20px 80px}}
  .hero{{text-align:center;margin-bottom:40px}}
  .hero-label{{font-size:12px;text-transform:uppercase;letter-spacing:2px;color:#7a7890;margin-bottom:12px}}
  .hero h1{{font-family:'Playfair Display',serif;font-size:clamp(28px,6vw,42px);margin-bottom:10px}}
  .hero p{{color:#9a98b0;font-size:15px}}
  .today-badge{{display:inline-block;background:#1e2030;border:1px solid #2a2d3a;border-radius:20px;padding:4px 16px;font-size:13px;color:#9a98b0;margin-top:10px}}
  .cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:20px;width:100%;max-width:900px}}
  .card{{background:#1a1d27;border:1px solid #2a2d3a;border-radius:12px;padding:24px;text-decoration:none;color:#e8e6e0;transition:transform .15s,border-color .15s;position:relative;overflow:hidden;cursor:pointer}}
  .card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--c)}}
  .card:hover{{transform:translateY(-3px);border-color:#3a3d4a}}
  .card-icon{{font-size:32px;margin-bottom:10px}}
  .card-badge{{font-size:11px;text-transform:uppercase;letter-spacing:.8px;color:var(--c);margin-bottom:8px;font-weight:600}}
  .card h2{{font-family:'Playfair Display',serif;font-size:22px;margin-bottom:8px}}
  .card-status{{font-size:13px;color:#9a98b0;margin-bottom:12px}}
  .card-stats{{display:flex;gap:16px;font-size:13px;color:#7a7890}}
  .card-stats strong{{color:#e8e6e0}}
  .archive{{width:100%;max-width:900px;margin-top:40px;background:#1a1d27;border:1px solid #2a2d3a;border-radius:12px;padding:24px}}
  .archive h3{{font-family:'Playfair Display',serif;font-size:18px;margin-bottom:16px;color:#9a98b0}}
  .archive ul{{list-style:none;display:flex;flex-direction:column;gap:8px}}
  .archive li{{font-size:14px;color:#7a7890}}
  .archive a{{color:#9a98b0;text-decoration:none}}
  .archive a:hover{{color:#e8e6e0}}
  .footer{{margin-top:40px;color:#3a3a50;font-size:12px;text-align:center}}
</style>
</head>
<body>
<div class="hero">
  <div class="hero-label">Family Daily Reader</div>
  <h1>今天的英文文章</h1>
  <p>每天早上 6:00 自動生成，直接閱讀</p>
  <div class="today-badge">📅 {TODAY}</div>
</div>

<div class="cards">{cards_html}</div>

<div class="archive">
  <h3>📂 過去文章（Tony）</h3>
  <ul>{archive_items}</ul>
</div>

<div class="footer">由 Google Gemini 2.0 Flash 每日自動生成 · GitHub Actions</div>

<script>
{stats_js}
</script>
</body>
</html>"""

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = {}

    for i, member in enumerate(MEMBERS):
        mid = member["id"]
        print(f"\n{'='*50}")
        print(f"Generating article for {member['name']} ({member['badge']})...")

        # Brief pause between requests to avoid rate limiting (skip before first request)
        if i > 0:
            time.sleep(5)

        try:
            raw = call_gemini(member["prompt"])
            data = parse_response(raw)

            if not data["title"] or not data["article"]:
                raise ValueError("Incomplete response from Gemini")

            html = generate_member_html(member, data)
            out_path = os.path.join(OUTPUT_DIR, f"{mid}_{TODAY}.html")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html)

            print(f"  ✅ {member['name']}: '{data['title']}'")
            print(f"     Vocab: {len(data['vocab'])} items, Quiz: {len(data['quiz'])} questions")
            results[mid] = True

        except Exception as e:
            print(f"  ❌ {member['name']} failed: {e}", file=sys.stderr)
            results[mid] = False

    # Generate index
    print(f"\nGenerating index page...")
    index_html = generate_index_html(MEMBERS, results)
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
    print("  ✅ index.html updated")

    success_count = sum(results.values())
    print(f"\n{'='*50}")
    print(f"Done: {success_count}/{len(MEMBERS)} articles generated for {TODAY}")

    if success_count == 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
