#!/usr/bin/env python3
"""
小红书内容改写器 (Xiaohongshu Rewriter)
将任意内容（文字稿、视频字幕、文章）改写为小红书风格帖子。

功能：
- 核心改写 pipeline
- 多角度生成（同一主题多篇不同调性）
- 标题生成（A/B 测试）
- 合规检查
"""

import re
from typing import List


# ── 小红书风格配置 ───────────────────────────────

EMOJI_MAP = {
    "hot": "🔥", "star": "✨", "tip": "💡", "warn": "⚠️",
    "yes": "✅", "no": "❌", "pin": "📌", "target": "🎯",
    "muscle": "💪", "eyes": "👀",
}

SENSITIVE_WORDS = {
    "医疗断言": ["治疗", "治愈", "根治", "保证有效", "药到病除", "一针见效"],
    "极限词": ["最", "第一", "绝对", "100%", "全网", "独家", "唯一", "无副作用"],
    "投资承诺": ["稳赚", "月入", "年入", "保证收益", "零风险"],
    "虚假营销": ["用了就瘦", "三天见效", "一周改变", "一夜暴富"],
    "歧视性": ["脑残", "智商税"],
}


class XHSContent:
    """小红书内容单元"""

    def __init__(self, title: str, body_parts: List[str],
                 hashtags: List[str], interaction: str):
        self.title = title
        self.body_parts = body_parts
        self.hashtags = hashtags
        self.interaction = interaction

    def render(self) -> str:
        lines = [f"## {self.title}", ""]
        for part in self.body_parts:
            lines.append(part)
            lines.append("")
        lines.append("---")
        lines.append(self.interaction)
        lines.append("")
        lines.append(" ".join(f"#{t}" for t in self.hashtags))
        return "\n".join(lines).strip()


class XHSRewriter:
    """小红书改写器：文字稿 → 帖子。纯文本处理，无需外部 API。"""

    ACADEMIC_STOP = {"本研究", "一种", "本文", "提出", "基于", "利用", "通过"}

    def __init__(self, source_text: str):
        self.source = source_text
        self._core_points: List[str] = []
        self._keywords: List[str] = []
        self._domain = "通用"

    # ── 核心入口 ──────────────────────────────────

    def rewrite(self, angle: str = "干货", tone: str = "口语") -> XHSContent:
        """改写入口。angle: 干货/踩坑/推荐/经验"""
        self._analyze()
        title = self._generate_title(angle)
        body = self._build_body(angle, tone)
        tags = self._generate_tags()
        return XHSContent(title, body, tags, self._interaction(angle))

    def multi_angle(self, n: int = 3) -> List[XHSContent]:
        """生成多个角度的帖子"""
        angles = ["干货", "踩坑", "推荐", "经验"]
        return [self.rewrite(a) for a in angles[:n]]

    def generate_titles(self, n: int = 3) -> List[str]:
        """生成多个备选标题"""
        self._analyze()
        kw_main = self._keyword_str()
        results = []
        templates = [
            f"3步搞定{kw_main}，效果惊艳了！",
            f"都说{kw_main}很难，但我试了试居然...",
            f"终于有人把{kw_main}讲清楚了！",
            f"{self._detect_identity()}必看！{kw_main}其实很简单",
            f"不会{kw_main}和会{kw_main}的差距，只差这一篇",
        ]
        return templates[:n]

    # ── 内部分析 ──────────────────────────────────

    def _keyword_str(self) -> str:
        """生成标题可用的关键词"""
        if self._keywords and self._keywords[0] not in self.ACADEMIC_STOP:
            return self._keywords[0]
        return self._domain

    def _analyze(self):
        text = self.source
        sentences = re.split(r'[。！？；\n]', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 3]

        sorted_sents = sorted([s for s in sentences if len(s) > 6],
                              key=len, reverse=True)
        self._core_points = sorted_sents[:5] if sorted_sents else [text[:80]]

        stop_words = {"这个", "一个", "可以", "进行", "我们", "他们", "以及",
                      "通过", "基于", "利用", "采用", "提出", "相关", "不同",
                      "一定", "主要"}
        words = re.findall(r'[\u4e00-\u9fff]{2,5}', text)
        freq = {}
        for w in words:
            if w not in stop_words and len(w) >= 2:
                freq[w] = freq.get(w, 0) + 1
        self._keywords = [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:5]]

        domain_map = {
            "科研": ["研究", "实验", "数据", "算法", "模型", "论文", "方法"],
            "编程": ["代码", "编程", "Python", "框架", "开发"],
            "职场": ["工作", "团队", "项目", "管理", "面试"],
            "学习": ["学习", "课程", "知识", "技能", "考试"],
        }
        for domain, indicators in domain_map.items():
            if any(ind in text for ind in indicators):
                self._domain = domain
                break

    def _generate_title(self, angle: str) -> str:
        kw = self._keyword_str()
        num = {"干货": "3", "踩坑": "5", "推荐": "4", "经验": "6"}.get(angle, "3")
        if angle == "干货":
            return f"{num}步搞定{kw}，同事以为我偷偷报了班！"
        elif angle == "踩坑":
            return f"含泪总结{num}个{kw}的坑，别再踩了😭"
        elif angle == "推荐":
            return f"后悔没早点知道！{kw}必备推荐"
        else:
            return f"我的{kw}经验：第{num}点真的绝了🔥"

    def _build_body(self, angle: str, tone: str) -> List[str]:
        parts = []
        points = self._core_points[:4]
        if not points:
            return [f"{EMOJI_MAP['hot']} 先说说重点～"]

        # 开场
        if angle == "踩坑":
            parts.append(f"{EMOJI_MAP['eyes']} 谁懂啊！{points[0][:40]}😭")
        elif angle == "推荐":
            parts.append(f"{EMOJI_MAP['star']} 发现了一个宝藏！")
        else:
            parts.append(f"{EMOJI_MAP['hot']} 直奔主题👇")

        # 要点
        for i, point in enumerate(points):
            text = point[:60] + "..." if len(point) > 60 else point
            parts.append(f"{EMOJI_MAP['pin']} {text}")

        # 总结
        if angle == "踩坑":
            parts.append(f"{EMOJI_MAP['warn']} 以上都是亲身经历，信我！")
        else:
            parts.append(f"{EMOJI_MAP['target']} 核心就是这些，试试就知道了～")

        return parts

    def _detect_identity(self) -> str:
        text = self.source
        if any(w in text for w in ["研究生", "博士", "科研", "论文"]):
            return "研究生"
        if any(w in text for w in ["实习", "求职", "面试"]):
            return "求职党"
        if any(w in text for w in ["编程", "代码", "Python"]):
            return "程序员"
        if any(w in text for w in ["考研", "高考"]):
            return "备考党"
        return "打工人"

    def _generate_tags(self) -> List[str]:
        flow_map = {
            "科研": ["科研干货", "论文写作", "研究生日常"],
            "编程": ["编程干货", "程序员", "学习日常"],
            "职场": ["职场干货", "打工人", "升职加薪"],
            "学习": ["学习日常", "干货分享", "知识分享"],
        }
        flow = flow_map.get(self._domain, ["干货分享", "实用技巧"])
        precise = [f"{self._domain}{k}" for k in self._keywords[:2]]
        tags = [t for t in precise if len(t) < 8] + flow
        return tags[:6]

    def _interaction(self, angle: str) -> str:
        if angle == "踩坑":
            return "你们踩过什么坑？评论区互相避雷👇"
        elif angle == "推荐":
            return "你们还有什么好用的？评论区安利给我👇"
        else:
            return "觉得有用的话🌟收藏起来，下次直接用！"

    # ── 合规检查 ──────────────────────────────────

    def compliance_check(self, text: str) -> List[str]:
        violations = []
        for category, words in SENSITIVE_WORDS.items():
            for word in words:
                if word in text:
                    violations.append(f"{category}: 含敏感词「{word}」")
        return violations


# ── 视频稿处理 ──────────────────────────────────

class TranscriptToXHS:
    """视频字幕文稿 → 小红书帖子"""

    @staticmethod
    def process(transcript: str, **kwargs) -> XHSContent:
        cleaned = re.sub(r'\[\d{1,2}:\d{2}(?::\d{2})?\]', '', transcript)
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned).strip()
        return XHSRewriter(cleaned).rewrite(**kwargs)


# ── 演示 ─────────────────────────────────────────

def demo():
    source = """本研究提出一种基于改进ResNet-50的图像分类方法，通过在网络的每个残差块后引入通道注意力机制，有效提升了模型对关键特征的提取能力。实验在CIFAR-10和ImageNet数据集上进行评估。结果表明，该方法在保持低计算开销的同时，Top-1准确率提升3.2%，参数量仅增加5%。该方法可广泛应用于自动驾驶视觉系统、医疗影像分析和工业质检等领域。"""

    rw = XHSRewriter(source)

    print("=" * 60)
    print("📄 角度1：入门干货")
    print("=" * 60)
    print(rw.rewrite("干货", "口语").render())

    print("\n" + "=" * 60)
    print("📄 角度2：踩坑经验")
    print("=" * 60)
    print(rw.rewrite("踩坑", "口语").render())

    print("\n" + "=" * 60)
    print("🎯 备选标题")
    print("=" * 60)
    for i, t in enumerate(rw.generate_titles(3), 1):
        print(f"  {i}. {t}")

    print("\n" + "=" * 60)
    print("✅ 合规检查")
    print("=" * 60)
    result = rw.compliance_check(source + "治愈良方")
    if result:
        for v in result:
            print(f"  ❌ {v}")
    else:
        print("  通过 ✓")


if __name__ == "__main__":
    demo()