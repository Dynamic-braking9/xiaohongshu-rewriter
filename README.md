# Xiaohongshu Content Rewriter (xiaohongshu-rewriter) v2.0

Hermes Agent Skill for rewriting text or video transcripts into Xiaohongshu (RED) style social media posts.

> **[中文版 → README.zh.md](README.zh.md)**

## Features

- 🔄 **Rewrite any text** — articles, transcripts, blogs, notes → Xiaohongshu style
- 🎯 **6 title templates** — Number punch / Suspense / Pain point / Identity / Contrast / Checklist
- 🔀 **Multi-angle generation** — 干货 (knowledge) / 踩坑 (pitfalls) / 推荐 (recommendations) / 经验 (experience)
- 📝 **Structured formatting** — emoji segments, one-sentence-per-line, ≤1000 chars body
- 🏷️ **Smart hashtags** — jieba-based keyword extraction + precise/trending tag combos
- ✅ **Compliance check v2** — context-aware: distinguishes strict violations from contextual warnings
- 🤖 **AI flavor detection** — catch robotic writing patterns (总-分-总, translationese, filler words)
- 📏 **Title validation** — hard ≤20 char check for feed visibility
- 🎬 **Video transcript support** — auto-clean timestamps, extract core message via `TranscriptToXHS`

## Quick Start

### Via Hermes Agent

Load the skill and provide your text — the LLM follows the rewriting rules:

```markdown
Load skill: xiaohongshu-rewriter
Task: rewrite this into Xiaohongshu style
Input: [your text or video transcript]
Angle: 干货 (or: 踩坑/推荐/经验)
```

### Python Script (v2.0)

```bash
python templates/xhs_rewriter.py    # runs full demo
```

### Programmatic

```python
from templates.xhs_rewriter import (
    XHSRewriter, compliance_check_v2, detect_ai_flavor, validate_title
)

source = "Your article text here..."
rw = XHSRewriter(source)

# Single post
post = rw.rewrite(angle="干货")
print(post.render())

# Title validation
ok, msg = validate_title(post.title)   # (True, "✓ 15 字")

# Multiple angles
posts = rw.multi_angle(n=3)

# Title A/B test
titles = rw.generate_titles(5)

# Context-aware compliance
cr = compliance_check_v2(post.render())
# cr.violations  → must fix
# cr.warnings    → review (e.g., "治愈拖延症" is a warning, "治愈癌症" is a violation)

# AI flavor detection
ai = detect_ai_flavor(text)   # ["[总分总句式] 命中「首先.*其次.*最后」", ...]
```

## Tool Functions

| Function | Purpose |
|----------|---------|
| `XHSRewriter(source).rewrite(angle)` | Core rewrite (4 angles) |
| `XHSRewriter(source).multi_angle(n)` | Batch multi-angle generation |
| `XHSRewriter(source).generate_titles(n)` | Generate title candidates |
| `validate_title(title)` | Title length check (≤20 chars) |
| `compliance_check_v2(text)` | Context-aware compliance (violations vs warnings) |
| `detect_ai_flavor(text)` | AI writing pattern detection |
| `extract_keywords(text)` | Jieba-based keyword extraction |
| `detect_domain(text)` | Domain detection (6 categories) |
| `TranscriptToXHS.process(transcript)` | Video transcript → post |

> ⚠️ The Python script provides **auxiliary** keyword extraction and template generation for batch/draft scenarios. Core rewriting quality depends on the LLM — SKILL.md rules are the authoritative source.

## Writing Style Guide

### Title Formulas

| Type | Pattern | Example |
|------|---------|---------|
| Number punch | [N] steps + [result] | 3步搞定Python基础，同事以为我偷偷报了班！ |
| Suspense | [common] + but + [twist] | 都说早起好，但我坚持晚起一年后... |
| Pain point | Finally someone explains... | 终于有人把SCI论文写作讲清楚了！ |
| Identity | [role] must see | 研一新生必看！5个生存法则 |
| Contrast | A vs B, just one trick away | 发C刊和普刊的差距，只差这一个方法 |
| Checklist | [N] things about [topic] | 博士答辩被夸的10个PPT技巧 |

### Body Structure

```
🔥 Hook line (pain point / curiosity)

📌 Key point 1
📌 Key point 2
📌 Key point 3

💡 Tips / Warnings

--- interactive prompt ---
#hashtag1 #hashtag2 #hashtag3
```

### Pre-rewrite Research (new in v2.0)

Before rewriting, confirm:
1. **Target audience** — who will read this?
2. **Benchmark posts** — search trending XHS posts on the same topic, analyze what works
3. **Reusable elements** — extract 3-5 patterns from benchmarks to incorporate

## File Structure

```
xiaohongshu-rewriter/
├── SKILL.md                    # Skill definition (v2.0)
├── README.md                   # English docs (this file)
├── README.zh.md                # Chinese docs
├── LICENSE                     # MIT + AI notice
├── templates/
│   └── xhs_rewriter.py         # Core rewriting script (v2.0)
└── references/
    └── examples.md             # Rewriting examples (v2.0)
```

## License

MIT — see [LICENSE](LICENSE)