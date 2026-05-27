# 小红书内容改写师 (xiaohongshu-rewriter) v2.0

Hermes Agent Skill：将任意内容（文章、视频稿、博客）改写为小红书风格帖子。

> **[English → README.md](README.md)**

## 功能特性

- 🔄 **文本改写** — 文章/字幕/笔记 → 小红书风
- 🎯 **6种标题模板** — 数字冲击/悬念/痛点/身份/对比/清单
- 🔀 **多角度生成** — 干货 / 踩坑 / 推荐 / 经验
- 📝 **结构化排版** — emoji 分段，一句一分行，正文 ≤1000 字
- 🏷️ **智能标签** — jieba 分词提取关键词 + 精准/流量标签组合
- ✅ **合规检查 v2** — 上下文感知，区分严格违规和语境警告
- 🤖 **去 AI 味检测** — 自动识别"首先其次最后"、翻译腔、废话连词等 AI 痕迹
- 📏 **标题字数校验** — 硬性 ≤20 字检查，确保信息流有效展示
- 🎬 **视频稿支持** — 自动清洗时间戳，支持 `TranscriptToXHS` 预处理

## 快速开始

### Hermes Agent 用法

加载 skill 后直接告诉 LLM 要改写：

```markdown
加载 skill: xiaohongshu-rewriter
任务：把以下内容改成小红书风格
输入：[你的文章或视频字幕]
角度：干货（可选：踩坑/推荐/经验）
```

### 脚本用法 v2.0

```bash
python templates/xhs_rewriter.py    # 运行完整演示
```

### 程序化使用

```python
from templates.xhs_rewriter import (
    XHSRewriter, compliance_check_v2, detect_ai_flavor, validate_title
)

source = "你的源文本..."
rw = XHSRewriter(source)

# 单篇改写
post = rw.rewrite(angle="干货")
print(post.render())

# 标题字数校验
ok, msg = validate_title(post.title)   # (True, "✓ 15 字")

# 多角度批量
posts = rw.multi_angle(n=3)

# 备选标题
titles = rw.generate_titles(5)

# 合规检查 v2（上下文感知）
cr = compliance_check_v2(post.render())
# cr.violations  → 必须修改
# cr.warnings    → 建议复查（如"治愈拖延症"只触发警告，不违规）

# 去 AI 味检测
ai = detect_ai_flavor(text)   # ["[总分总句式] 命中「首先.*其次.*最后」", ...]
```

## 工具函数一览

| 函数 | 作用 |
|------|------|
| `XHSRewriter(source).rewrite(angle)` | 核心改写（4 种角度） |
| `XHSRewriter(source).multi_angle(n)` | 多角度批量生成 |
| `XHSRewriter(source).generate_titles(n)` | 备选标题生成 |
| `validate_title(title)` | 标题字数校验（≤20 字） |
| `compliance_check_v2(text)` | 合规检查（区分违规/警告） |
| `detect_ai_flavor(text)` | AI 味检测 |
| `extract_keywords(text)` | jieba 分词提取关键词 |
| `detect_domain(text)` | 领域检测（6 类） |
| `TranscriptToXHS.process(transcript)` | 视频字幕预处理 → 帖子 |

> ⚠️ Python 脚本提供**辅助性**的关键词提取和模板生成（用于快速草稿和批量场景），核心改写质量靠 LLM。SKILL.md 中的改写原则和模板才是主角。

## 改写原则速览

### 标题公式

| 类型 | 公式 | 示例 |
|------|------|------|
| 数字冲击 | [数字] + [结果/效果] | 3步搞定Python基础，同事以为我偷偷报了班！ |
| 悬念反常识 | [常见观点] + "但是" + [反转] | 都说早起好，但我坚持晚起一年后... |
| 痛点共鸣 | "终于有人" + [痛点] | 终于有人把SCI论文写作讲清楚了！ |
| 身份标签 | [身份] + "必看" | 研一新生必看！5个生存法则 |
| 对比冲击 | A vs B, 只差一个 | 发C刊和普刊的差距，只差这一个方法 |
| 清单型 | [N] 个 + [领域] | 博士答辩被夸的10个PPT技巧 |

### 正文结构

```
🔥 一句话戳痛点

📌 核心观点 1
📌 核心观点 2
📌 核心观点 3

💡 小tips / 避坑提醒

--- 互动引导 ---
#标签1 #标签2 #标签3
```

### v2.0 新增：改写前置步骤

改写前先确认：
1. **目标受众** — 给谁看？想达到什么效果？
2. **对标搜索** — 同主题下什么帖子火了？标题用什么公式？
3. **可复用元素** — 从对标帖中提取 3-5 个可复用的表达方式

## 文件结构

```
xiaohongshu-rewriter/
├── SKILL.md                    # Skill 定义 (v2.0)
├── README.md                   # 英文说明
├── README.zh.md                # 中文说明（本文件）
├── LICENSE                     # MIT + AI 声明
├── templates/
│   └── xhs_rewriter.py         # 核心改写脚本 (v2.0)
└── references/
    └── examples.md             # 改写示例 (v2.0)
```

## 许可证

MIT — 详见 [LICENSE](LICENSE)