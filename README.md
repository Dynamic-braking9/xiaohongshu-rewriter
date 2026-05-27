# 小红书内容改写师 (xiaohongshu-rewriter)

Hermes Agent Skill for rewriting text or video transcripts into Xiaohongshu (RED) style social media posts.

> **[中文版 → README.zh.md](README.zh.md)**

## Features

- 🔄 **Rewrite any text** — articles, transcripts, blogs, notes → Xiaohongshu style
- 🎯 **6 title templates** — 数字冲击/悬念/痛点/身份标签/对比/清单
- 🔀 **Multi-angle generation** — 干货 / 踩坑 / 推荐 / 经验
- 📝 **Structured formatting** — emoji segments, one-sentence-per-line
- 🏷️ **Smart hashtags** — precise + trending tag combinations
- ✅ **Compliance check** — flag sensitive words and regulated claims
- 🎬 **Video transcript support** — clean timestamp markers, extract core message

## Quick Start

### Via Hermes Agent

Load the skill and provide your text:

```markdown
Load skill: xiaohongshu-rewriter
Task: rewrite this into Xiaohongshu style
Input: [your text or video transcript]
Angle: 干货 (or: 踩坑/推荐/经验)
```

### Python Script

```bash
python templates/xhs_rewriter.py
```

### Programmatic

```python
from templates.xhs_rewriter import XHSRewriter

source = "Your article text here..."
rw = XHSRewriter(source)

# Single post
post = rw.rewrite(angle="干货")
print(post.render())

# Multiple angles
posts = rw.multi_angle(n=3)

# Title A/B test
titles = rw.generate_titles(3)

# Compliance
violations = rw.compliance_check(source)
```

## Writing Style Guide

### Title Formulas

| Type | Pattern | Example |
|------|---------|---------|
| Number punch | [N] steps + [result] | 3步搞定Python基础，同事以为我偷偷报了班！ |
| Suspense | [common] + but + [twist] | 都说早起好，但我坚持晚起一年后... |
| Pain point | Finally someone explains... | 终于有人把SCI论文写作讲清楚了！ |
| Identity | [role] must see | 研一新生必看！5个生存法则 |

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

### Emoji Rules

- Each section starts with 1 emoji (no stacking)
- Title: minimal emoji; Body: 1 emoji per segment
- Domain mapping:
  - 📚 📖 ✍️ 🎓 for academic
  - 💼 📈 🏢 for workplace
  - 🏠 🛒 🌿 for lifestyle

### Compliance Checklist

- ❌ No medical claims (治疗/治愈/根治)
- ❌ No superlatives (最/第一/绝对/100%)
- ❌ No investment promises (稳赚/月入X万)
- ❌ No political sensitivity
- ✅ Interactive call-to-action at the end

## File Structure

```
xiaohongshu-rewriter/
├── SKILL.md                    # Skill definition
├── README.md                   # English docs
├── README.zh.md                # Chinese docs
├── LICENSE                     # MIT + AI notice
├── templates/
│   └── xhs_rewriter.py         # Core rewriting script
└── references/
    └── examples.md             # Before/after examples
```

## License

MIT
