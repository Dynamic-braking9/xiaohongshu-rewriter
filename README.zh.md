# 小红书内容改写师 (xiaohongshu-rewriter)

Hermes Agent Skill：将任意内容（文章、视频稿、博客）改写为小红书风格帖子。

> **[English → README.md](README.md)**

## 功能特性

- 🔄 **文本改写** — 文章/字幕/笔记 → 小红书风
- 🎯 **6种标题模板** — 数字冲击/悬念/痛点/身份/对比/清单
- 🔀 **多角度生成** — 干货 / 踩坑 / 推荐 / 经验
- 📝 **结构化排版** — emoji 分段，一句一分行
- 🏷️ **智能标签** — 精准长尾 + 大流量组合
- ✅ **合规检查** — 敏感词、极限词、医疗断言
- 🎬 **视频稿支持** — 自动清洗时间戳

## 快速开始

### Hermes Agent 用法

加载 skill 后直接告诉 LLM 要改写：

```markdown
加载 skill: xiaohongshu-rewriter
任务：把以下内容改成小红书风格
输入：[你的文章或视频字幕]
角度：干货（可选：踩坑/推荐/经验）
```

### 脚本用法

```bash
python templates/xhs_rewriter.py

# 程序化使用
from templates.xhs_rewriter import XHSRewriter
rw = XHSRewriter("源文本")
post = rw.rewrite(angle="干货")
print(post.render())
```

## 文件结构

```
xiaohongshu-rewriter/
├── SKILL.md                    # Skill 定义
├── README.md                   # 英文说明
├── README.zh.md                # 中文说明
├── LICENSE                     # MIT + AI 声明
├── templates/
│   └── xhs_rewriter.py         # 核心改写脚本
└── references/
    └── examples.md             # 改写前后示例
```

## 许可证

MIT
