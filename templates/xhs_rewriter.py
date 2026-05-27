#!/usr/bin/env python3
"""
小红书内容改写器 v2.0 (Xiaohongshu Rewriter)

将任意文字内容改写为小红书风格帖子。v2.0 使用 jieba 分词实现
可靠的关键词提取和领域检测。

功能：
- 核心改写 pipeline（干货/踩坑/推荐/经验 四种角度）
- 多角度生成（同一主题多篇不同调性）
- 标题生成（A/B 测试，硬性 ≤20 字校验）
- 合规检查（带上下文判断，减少误报）
- 去 AI 味反检
- 视频字幕预处理
"""

import re
from typing import List, Tuple, Optional
from collections import Counter

import jieba


# ── 小红书平台约束 ───────────────────────────────

TITLE_MAX_CHARS = 20       # 小红书信息流只显示前 20 字
BODY_MAX_CHARS = 1000      # 正文上限
HASHTAG_MAX = 7            # 标签总数上限
HASHTAG_MIN = 3            # 标签数量下限


# ── Emoji 映射 ────────────────────────────────────

EMOJI = {
    "hot": "🔥", "star": "✨", "tip": "💡", "warn": "⚠️",
    "yes": "✅", "no": "❌", "pin": "📌", "target": "🎯",
    "muscle": "💪", "eyes": "👀", "cry": "😭", "clap": "👏",
    "heart": "❤️", "rocket": "🚀", "sparkles": "✨",
    "book": "📚", "laptop": "💻", "bulb": "💡",
}

# ── 领域配置 ──────────────────────────────────────

DOMAIN_KEYWORDS = {
    "科研": ["研究", "实验", "数据", "算法", "模型", "论文", "方法",
             "神经网络", "深度学习", "机器学习", "训练", "准确率",
             "ImageNet", "CIFAR", "ResNet", "Transformer"],
    "编程": ["代码", "编程", "Python", "框架", "开发", "库", "开源",
             "API", "前端", "后端", "架构", "调试", "Git", "GitHub",
             "React", "Vue", "JavaScript", "TypeScript", "Java", "Go"],
    "职场": ["工作", "团队", "项目", "管理", "面试", "简历", "跳槽",
             "升职", "薪资", "实习", "领导", "同事", "效率", "汇报"],
    "学习": ["学习", "课程", "知识", "技能", "考试", "考研", "高考",
             "备考", "笔记", "复习", "记忆", "阅读", "读书"],
    "设计": ["设计", "UI", "UX", "配色", "排版", "字体", "图标",
             "Figma", "Sketch", "Photoshop", "海报"],
    "自媒体": ["自媒体", "账号", "运营", "涨粉", "选题", "脚本",
               "剪辑", "拍摄", "流量", "变现", "小红书", "抖音"],
}

DOMAIN_TAGS = {
    "科研": ["科研干货", "论文写作", "研究生日常"],
    "编程": ["编程干货", "程序员", "学习日常"],
    "职场": ["职场干货", "打工人", "升职加薪"],
    "学习": ["学习日常", "干货分享", "知识分享"],
    "设计": ["设计灵感", "设计师日常", "干货分享"],
    "自媒体": ["自媒体运营", "新人博主", "运营干货"],
}

# ── 合规词库 ─────────────────────────────────────

SENSITIVE_WORDS = {
    "医疗断言": {
        "strict": ["根治", "药到病除", "一针见效", "保证有效", "包治百病"],
        "contextual": {  # 需要上下文判断（非医疗语境不算违规）
            "治疗": ["疾病", "癌症", "肿瘤", "抑郁", "感染","处方","手术"],
            "治愈": ["疾病", "癌症", "肿瘤", "抑郁", "感染", "处方"],
        },
    },
    "极限词": {
        "strict": ["全网第一", "独家唯一", "100%有效", "绝对安全"],
        "contextual": {
            "最": ["最好", "最便宜", "最有效", "最先进", "最强",
                   "第一品牌", "第一名", "全网第一", "全国第一"],
            "第一": ["第一品牌", "第一名", "第一选择"],
        },
    },
    "投资承诺": {
        "strict": ["稳赚", "保证收益", "零风险投资"],
        "contextual": {
            "月入": ["月入过万", "月入十万", "月入百万"],
            "年入": ["年入百万", "年入千万"],
        },
    },
    "虚假营销": {
        "strict": ["用了就瘦", "一夜暴富", "躺着赚钱", "不用学就能"],
        "contextual": {
            "三天": ["三天见效", "三天学会", "三天改变"],
            "一周": ["一周见效", "一周改变", "一周速成"],
        },
    },
    "歧视性": {
        "strict": ["脑残", "傻逼", "智障", "废物"],
        "contextual": {},
    },
}

# ── AI 味检测词 ─────────────────────────────────

AI_PATTERNS = {
    "总分总句式": [r'首先.*其次.*最后', r'综上所述', r'总而言之',
                   r'值得注意的是', r'不可忽视的是', r'需要指出的是'],
    "翻译腔": [r'研究结果显示', r'研究表明', r'数据表明', r'结果表明',
               r'根据.*调查', r'在.*方面', r'对.*进行.*分析'],
    "假客观": [r'从某种意义上说', r'在一定程度上', r'相对而言',
               r'不可否认', r'毋庸置疑', r'显而易见'],
    "废话连词": [r'不仅如此', r'此外', r'另外', r'与此同时',
                 r'更重要的是', r'进一步来说'],
    "说教感": [r'我们应该', r'大家要', r'一定要', r'必须要',
               r'建议大家', r'希望大家都'],
}


# ═══════════════════════════════════════════════════
# 分词 & 领域检测工具
# ═══════════════════════════════════════════════════

STOP_WORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些",
    "所", "为", "以", "及", "与", "或", "但", "而", "且", "因", "然",
    "这个", "那个", "可以", "进行", "我们", "他们", "以及",
    "通过", "基于", "利用", "采用", "提出", "相关", "不同",
    "一定", "主要", "本文", "本研究", "该", "其", "某",
    "比如", "例如", "等等", "什么", "怎么", "为什么", "如何",
    "一种", "方法", "结果", "分析", "使用", "比较", "非常",
    "真的", "觉得", "感觉", "知道", "应该", "还是", "之后",
    "已经", "可能", "需要", "现在", "很多", "一点", "一些",
    "给大家", "今天", "分享", "关注", "点赞", "收藏", "评论",
    "大家", "超好", "一键", "生成", "用了", "好用", "推荐",
    "三个", "月", "效率", "直接", "翻倍", "试试", "就是",
    "一下", "起来", "过来", "出来", "下来", "上去", "进去",
    "不到", "不能", "不用", "不会", "不够", "不只",
    "我用", "你", "你们", "他们", "她们",
    "时候", "几点", "注意", "一定", "一些", "什么", "怎么",
    "研究", "提出", "改进", "一种", "基于", "利用", "采用",
    "方法", "结果", "分析", "使用", "比较", "相关", "不同",
    "进行", "通过", "实验", "表明", "验证", "评估", "测试",
    "结合", "引入", "融合", "设计", "实现",
}


def segment(text: str) -> List[str]:
    """用 jieba 分词，过滤停用词和单字"""
    words = jieba.lcut(text)
    return [
        w.strip() for w in words
        if len(w.strip()) >= 2 and w.strip() not in STOP_WORDS
    ]


def extract_keywords(text: str, topn: int = 5) -> List[str]:
    """提取关键词：jieba 分词 + TF 排序，合并常见 2-gram"""
    words = segment(text)
    if not words:
        return []

    # TF 统计
    counter = Counter(words)

    # 尝试合并 2-gram（如「数据」「可视化」→「数据可视化」）
    merged = []
    raw_words = [w for w in jieba.lcut(text) if len(w.strip()) >= 2 and w.strip() not in STOP_WORDS]
    i = 0
    while i < len(raw_words) - 1:
        bigram = raw_words[i] + raw_words[i + 1]
        # 如果 bigram 出现在原文本中，且有意义（非纯数字组合）
        if bigram in text and not bigram.isdigit() and len(bigram) >= 4:
            merged.append(bigram)
            i += 2
        else:
            merged.append(raw_words[i])
            i += 1
    if i < len(raw_words):
        merged.append(raw_words[-1])

    # 用合并后的词重新统计
    counter2 = Counter(merged)
    seen = set()
    result = []
    for word, _ in counter2.most_common(30):
        if word not in seen and word not in STOP_WORDS and len(word) >= 2:
            seen.add(word)
            result.append(word)
        if len(result) >= topn:
            break
    return result


def detect_domain(text: str) -> Tuple[str, float]:
    """
    领域检测。返回 (domain_name, confidence)。
    confidence 基于匹配 indicator 数量占比。
    """
    scores = {}
    for domain, indicators in DOMAIN_KEYWORDS.items():
        count = sum(1 for ind in indicators if ind in text)
        if count:
            scores[domain] = count

    if not scores:
        return "通用", 0.0

    best = max(scores, key=scores.get)
    confidence = scores[best] / len(DOMAIN_KEYWORDS[best])
    return best, min(confidence, 1.0)


# ═══════════════════════════════════════════════════
# 合规检查 v2（上下文感知）
# ═══════════════════════════════════════════════════

class ComplianceResult:
    def __init__(self):
        self.violations: List[str] = []    # 明确违规（必须改）
        self.warnings: List[str] = []      # 上下文存疑（建议检查）


def compliance_check_v2(text: str) -> ComplianceResult:
    """
    合规检查 v2：区分 strict（明确违规）和 contextual（上下文存疑）。
    - strict: 命中即违规
    - contextual: 只在医疗/金融等语境下才算违规
    """
    result = ComplianceResult()

    for category, rules in SENSITIVE_WORDS.items():
        # Strict 词：命中即违规
        for word in rules["strict"]:
            if word in text:
                result.violations.append(f"[{category}] 含敏感词「{word}」")

        # Contextual 词：需要上下文触发词同时出现
        for keyword, triggers in rules["contextual"].items():
            if keyword in text:
                # 检查是否有医疗/金融等敏感上下文
                context_hit = any(t in text for t in triggers)
                if context_hit:
                    result.violations.append(
                        f"[{category}] 含敏感词「{keyword}」（上下文: {', '.join(t for t in triggers if t in text)}）")
                else:
                    result.warnings.append(
                        f"[{category}] 含词「{keyword}」，当前上下文未触发违规，建议复查")

    return result


# ═══════════════════════════════════════════════════
# 去 AI 味检测
# ═══════════════════════════════════════════════════

def detect_ai_flavor(text: str) -> List[str]:
    """
    检测文本中的 AI 写作痕迹。
    返回命中的模式列表（空列表 = 通过）。
    """
    issues = []
    for category, patterns in AI_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text):
                issues.append(f"[{category}] 命中「{pat}」")
    return issues


# ═══════════════════════════════════════════════════
# 标题硬性校验
# ═══════════════════════════════════════════════════

def validate_title(title: str) -> Tuple[bool, str]:
    """
    检查标题是否符合小红书平台约束。
    返回 (pass, reason)。
    """
    # 去 emoji 后算字数
    clean = re.sub(r'[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE00-\uFE0F]', '', title)
    clean = re.sub(r'[【】《》「」『』""'']', '', clean)

    char_count = len(clean)
    if char_count > TITLE_MAX_CHARS:
        return False, f"标题 {char_count} 字（超 {char_count - TITLE_MAX_CHARS} 字），信息流只显示前 {TITLE_MAX_CHARS} 字"
    if char_count < 5:
        return False, f"标题仅 {char_count} 字，太短无信息量"
    return True, f"✓ {char_count} 字"


# ═══════════════════════════════════════════════════
# 标题模板库（带权重）
# ═══════════════════════════════════════════════════

TITLE_TEMPLATES = {
    "干货": [
        "{kw}入门指南，看这一篇就够了",
        "{n}个{kw}技巧，效率翻倍",
        "零基础学{kw}，{n}天从入门到上手",
        "终于有人把{kw}讲清楚了！",
        "{kw}全攻略：从原理到实战",
    ],
    "踩坑": [
        "含泪总结：{kw}路上的{n}个大坑",
        "做{kw}千万别做的{n}件事😭",
        "血泪教训！{kw}新手最容易犯的{n}个错",
        "后悔没早知道！{kw}避坑指南",
        "{kw}踩坑实录：第{n}个太真实了",
    ],
    "推荐": [
        "{kw}必备！这{n}个工具/方法绝了🔥",
        "挖到宝了！{kw}的神器推荐",
        "用了{n}年的{kw}好物，真心推荐✨",
        "提升{kw}效率的{n}个秘密武器",
        "宝藏{kw}资源，建议收藏🌟",
    ],
    "经验": [
        "我的{kw}经验：第{n}点真的很重要",
        "{n}年{kw}经验，浓缩成{n}条建议",
        "关于{kw}，我想说的{n}句话",
        "{kw}真实体�：从入门到放弃再到真香",
        "{n}条{kw}心得，每条都是花钱买来的",
    ],
}


# ═══════════════════════════════════════════════════
# 核心类
# ═══════════════════════════════════════════════════

class XHSContent:
    """小红书内容单元"""

    def __init__(self, title: str, body_parts: List[str],
                 hashtags: List[str], interaction: str,
                 angle: str = "干货"):
        self.title = title
        self.body_parts = body_parts
        self.hashtags = hashtags[:HASHTAG_MAX]
        self.interaction = interaction
        self.angle = angle

    def render(self) -> str:
        """渲染为完整帖子文本"""
        lines = [self.title, ""]
        for part in self.body_parts:
            lines.append(part)
            lines.append("")
        lines.append("---")
        lines.append(self.interaction)
        lines.append("")
        lines.append("  ".join(f"#{t}" for t in self.hashtags))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "body": self.body_parts,
            "hashtags": self.hashtags,
            "interaction": self.interaction,
            "angle": self.angle,
        }


class XHSRewriter:
    """
    小红书改写器 v2.0

    使用 jieba 分词实现关键词提取和领域检测。
    核心改写逻辑是模板驱动的（LLM 模式下由 AI 完成实际改写，
    脚本用于快速生成草稿、批量处理和合规校验）。
    """

    def __init__(self, source_text: str):
        self.source = source_text
        self._keywords: List[str] = []
        self._domain: str = "通用"
        self._domain_conf: float = 0.0
        self._core_sentences: List[str] = []
        self._analyzed = False

    # ── 分析 ──────────────────────────────────────

    def _analyze(self):
        """提取关键词、领域、核心句子"""
        if self._analyzed:
            return
        text = self.source

        # 关键词提取 (jieba)
        self._keywords = extract_keywords(text)
        if not self._keywords:
            self._keywords = ["干货"]

        # 领域检测
        self._domain, self._domain_conf = detect_domain(text)

        # 核心句子提取（取最长的实义句）
        sentences = re.split(r'[。！？；\n]', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 8]
        sorted_sents = sorted(sentences, key=len, reverse=True)
        self._core_sentences = sorted_sents[:5] if sorted_sents else [text[:80]]

        self._analyzed = True

    # ── 核心入口 ──────────────────────────────────

    def rewrite(self, angle: str = "干货", tone: str = "口语") -> XHSContent:
        """改写入口"""
        self._analyze()
        title = self._generate_title(angle)
        body = self._build_body(angle, tone)
        tags = self._generate_tags()
        return XHSContent(title, body, tags, self._interaction(angle), angle)

    def multi_angle(self, n: int = 3) -> List[XHSContent]:
        """生成多个角度的帖子"""
        angles = ["干货", "踩坑", "推荐", "经验"]
        return [self.rewrite(a) for a in angles[:n]]

    def generate_titles(self, n: int = 5) -> List[str]:
        """生成多个备选标题，附带字数校验结果"""
        self._analyze()
        kw = self._keywords[0] if self._keywords else "干货"
        num = len(self._core_sentences) if self._core_sentences else 3
        num = min(num, 5)

        results = []
        # 从各角度各取模板
        import random
        rng = random.Random(42)  # 固定种子保证可复现

        all_candidates = []
        for angle, templates in TITLE_TEMPLATES.items():
            for tmpl in templates:
                title = tmpl.format(kw=kw, n=num)
                all_candidates.append(title)

        # 按字数筛选：优先 ≤20 字的
        good = [t for t in all_candidates if len(re.sub(r'[\U0001F300-\U0001FAFF]', '', t)) <= TITLE_MAX_CHARS]
        ok = [t for t in all_candidates if t not in good]

        candidates = good + ok
        rng.shuffle(good)
        rng.shuffle(ok)

        return (good + ok)[:n]

    # ── 内部方法 ──────────────────────────────────

    def _generate_title(self, angle: str) -> str:
        """生成标题（LLM 模式下由 AI 生成，这里提供模板兜底）"""
        kw = self._keywords[0] if self._keywords else self._domain
        n = len(self._core_sentences)
        n = min(n, 5) if n > 1 else 3

        templates = TITLE_TEMPLATES.get(angle, TITLE_TEMPLATES["干货"])
        # 选字数最小的模板
        candidates = [t.format(kw=kw, n=n) for t in templates]
        candidates.sort(key=lambda t: len(re.sub(r'[\U0001F300-\U0001FAFF]', '', t)))
        return candidates[0]

    def _build_body(self, angle: str, tone: str) -> List[str]:
        """构建正文"""
        parts = []
        points = self._core_sentences[:4]
        if not points:
            parts.append(f"{EMOJI['hot']} 先说说重点～")
            return parts

        # 开场
        openers = {
            "踩坑": f"{EMOJI['eyes']} 谁懂啊！说多了都是泪😭",
            "推荐": f"{EMOJI['star']} 挖到宝了！分享几个心头好👇",
            "经验": f"{EMOJI['bulb']} 做这行这么久，这些经验最值钱",
            "干货": f"{EMOJI['hot']} 直奔主题👇",
        }
        parts.append(openers.get(angle, openers["干货"]))

        # 要点
        for i, point in enumerate(points):
            p = point[:72].rsplit("，", 1)[0] if len(point) > 72 else point
            parts.append(f"{EMOJI['pin']} {p}")

        # 总结
        closers = {
            "踩坑": f"{EMOJI['warn']} 以上都是亲身踩过的坑，信我！",
            "推荐": f"{EMOJI['heart']} 都是自用很久的，真心推荐！",
            "经验": f"{EMOJI['target']} 能消化一条就值了～",
            "干货": f"{EMOJI['target']} 核心就是这些，试试就知道了～",
        }
        parts.append(closers.get(angle, closers["干货"]))

        return parts

    def _generate_tags(self) -> List[str]:
        """生成话题标签"""
        # 领域标签
        domain_tags = DOMAIN_TAGS.get(self._domain, ["干货分享", "实用技巧"])

        # 关键词标签（过滤太长的）
        kw_tags = []
        for kw in self._keywords[:3]:
            kw = kw.replace(" ", "")
            if 3 <= len(kw) <= 8:
                kw_tags.append(kw)

        # 组合：精准 + 流量
        tags = kw_tags + domain_tags
        # 去重保序
        seen = set()
        result = []
        for t in tags:
            if t not in seen and len(t) <= 12:
                seen.add(t)
                result.append(t)

        return result[:HASHTAG_MAX]

    def _interaction(self, angle: str) -> str:
        """生成互动引导"""
        guides = {
            "踩坑": "你们踩过什么坑？评论区互相避雷👇",
            "推荐": "你们还有什么好用的？评论区安利给我👇",
            "经验": "你们有什么经验？一起来聊聊～",
            "干货": "觉得有用的话🌟收藏起来，下次直接用！",
        }
        return guides.get(angle, guides["干货"])


# ═══════════════════════════════════════════════════
# 视频稿处理
# ═══════════════════════════════════════════════════

class TranscriptToXHS:
    """视频字幕文稿 → 小红书帖子"""

    @staticmethod
    def process(transcript: str, **kwargs) -> XHSContent:
        """预处理字幕文本后改写"""
        # 删除时间戳
        cleaned = re.sub(r'\[\d{1,2}:\d{2}(?::\d{2})?\]', '', transcript)
        cleaned = re.sub(r'\d{2}:\d{2}(?::\d{2})?\s*', '', cleaned)
        # 合并连续空行
        cleaned = re.sub(r'\n\s*\n+', '\n', cleaned).strip()
        # 删除纯标点行
        cleaned = re.sub(r'^[^\w\u4e00-\u9fff]+$', '', cleaned, flags=re.MULTILINE)
        return XHSRewriter(cleaned).rewrite(**kwargs)


# ═══════════════════════════════════════════════════
# 演示 & 测试
# ═══════════════════════════════════════════════════

def demo():
    """运行完整演示"""
    source = (
        "今天给大家分享一个超好用的Python库，可以一键生成数据可视化图表。"
        "我用了三个月，写报告效率直接翻倍。不需要写一行前端代码，"
        "只要几行Python就能出漂亮的图表。支持折线图、柱状图、散点图、"
        "热力图等几十种图表类型，导出格式支持PNG、SVG、HTML。"
    )

    rw = XHSRewriter(source)
    rw._analyze()  # 手动触发分析，以便显示诊断信息

    print("=" * 60)
    print("📊 分析结果")
    print("=" * 60)
    print(f"  关键词: {rw._keywords}")
    print(f"  领域: {rw._domain} (置信度: {rw._domain_conf:.0%})")
    print(f"  核心句: {len(rw._core_sentences)} 句")
    print()

    for angle in ["干货", "踩坑", "推荐", "经验"]:
        post = rw.rewrite(angle)
        print("=" * 60)
        print(f"📄 角度: {angle}")
        print("=" * 60)
        valid, msg = validate_title(post.title)
        print(f"  标题校验: {msg}")
        ai_issues = detect_ai_flavor(post.render())
        if ai_issues:
            print(f"  ⚠️ AI味检测: {ai_issues[0]}")
        else:
            print("  ✅ AI味检测: 通过")
        print("─" * 40)
        print(post.render())
        print()

    print("=" * 60)
    print("🎯 备选标题（带字数校验）")
    print("=" * 60)
    for i, t in enumerate(rw.generate_titles(5), 1):
        ok, msg = validate_title(t)
        mark = "✅" if ok else "❌"
        print(f"  {mark} {i}. {t}")
        if not ok:
            print(f"      ↳ {msg}")

    print()
    print("=" * 60)
    print("🛡️ 合规检查 v2（上下文感知）")
    print("=" * 60)

    tests = [
        ("正常文本", source),
        ("极限词", "这是最好的Python库，100%好用"),
        ("医疗误报", "这个插件可以治愈你的拖延症"),   # 不应违规
        ("真实违规", "这个方法能治愈癌症，保证有效"),  # 应违规
        ("投资承诺", "用这个工具月入过万不是梦"),       # 应违规
    ]
    for label, text in tests:
        r = compliance_check_v2(text)
        print(f"\n  [{label}]")
        for v in r.violations:
            print(f"    ❌ {v}")
        for w in r.warnings:
            print(f"    ⚠️ {w}")
        if not r.violations and not r.warnings:
            print("    ✅ 通过")

    print()
    print("=" * 60)
    print("🤖 去 AI 味测试")
    print("=" * 60)

    ai_text = (
        "首先，我们需要了解数据可视化的基本概念。其次，选择合适的图表类型"
        "至关重要。最后，值得注意的是，配色方案也会影响可读性。"
        "综上所述，数据可视化是一门综合性的技能。"
    )
    issues = detect_ai_flavor(ai_text)
    if issues:
        for x in issues:
            print(f"  ❌ {x}")
    else:
        print("  ✅ 通过")


if __name__ == "__main__":
    demo()