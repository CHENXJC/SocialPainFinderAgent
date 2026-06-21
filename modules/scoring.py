"""Transparent local emotion and business-opportunity scoring rules."""

from __future__ import annotations

import math
import re

import pandas as pd


COMPLAINT_WORDS = ("bad", "terrible", "awful", "broken", "useless", "disappointed", "hate", "problem", "糟糕", "太差", "难用", "失望", "讨厌", "问题", "崩溃")
URGENCY_WORDS = ("urgent", "asap", "immediately", "now", "cannot wait", "紧急", "马上", "立刻", "赶快", "等不及")
NEGATIVE_WORDS = ("angry", "frustrated", "anxious", "worried", "overwhelmed", "stress", "annoying", "生气", "愤怒", "焦虑", "担心", "烦", "压力", "无语")
INTENSIFIERS = ("very", "extremely", "really", "totally", "always", "never", "非常", "特别", "太", "真的", "一直", "根本", "完全")

PAYMENT_KEYWORDS = (
    "pay", "paid", "expensive", "price", "cost", "refund", "subscription",
    "waste money", "lose money", "revenue", "sales", "client", "customer",
    "business", "urgent", "deadline", "hire", "outsource", "consultant",
    "service", "solution", "付费", "花钱", "太贵", "价格", "成本", "退款",
    "订阅", "浪费钱", "亏钱", "收入", "销售", "客户", "生意", "着急",
    "截止", "外包", "找人做", "顾问", "服务", "解决方案",
)
AUTOMATION_KEYWORDS = (
    "manual", "repetitive", "copy", "paste", "summarize", "extract", "classify",
    "monitor", "report", "reply", "translate", "schedule", "search", "organize",
    "workflow", "automate", "automation", "dashboard", "document", "email",
    "customer service", "手动", "重复", "复制", "粘贴", "总结", "提取", "分类",
    "监控", "报告", "回复", "翻译", "排程", "搜索", "整理", "流程", "自动化",
    "看板", "文档", "邮件", "客服",
)
CONTENT_KEYWORDS = (
    "tutorial", "guide", "how to", "tips", "mistakes", "review", "comparison",
    "beginner", "checklist", "case study", "workflow", "productivity", "learn",
    "explain", "template", "教程", "指南", "怎么做", "技巧", "避坑", "测评",
    "对比", "新手", "清单", "案例", "流程", "效率", "学习", "解释", "模板",
)
URGENCY_BUSINESS_KEYWORDS = (
    "urgent", "asap", "immediately", "deadline", "cannot wait", "delay", "hours",
    "waste time", "lose money", "revenue", "sales", "customer", "client", "business",
    "broken", "crash", "no response", "manual", "repetitive", "every day", "slow",
    "time-consuming", "productivity", "紧急", "马上", "立刻", "截止", "耽误", "耗时",
    "浪费时间", "亏钱", "收入", "销售", "客户", "生意", "崩溃", "不回复", "手动",
    "重复", "每天", "效率低", "太慢",
)

WHY_IT_MATTERS = {
    "Time cost pain": "这类反馈说明用户正在为低效率或等待付出时间成本，若问题高频出现，通常具有明确的效率改进价值。",
    "Money cost pain": "这类反馈直接涉及价格、订阅或资金损失，往往能反映用户对价值与付费结果的敏感度。",
    "Learning difficulty": "这类反馈说明用户难以理解、记忆或执行学习内容，适合转化为分步教学、学习助手或练习工具。",
    "Tool usability problem": "这类反馈会阻碍用户完成任务并增加流失风险，适合通过辅助工具、智能支持或更好的引导降低使用门槛。",
    "Information gap": "这类反馈说明用户缺少清晰信息、判断依据或整理后的知识，适合转化为研究助手、信息监控 Agent、内容选题或咨询服务。",
    "Trust issue": "这类反馈说明用户对真实性、隐私、安全或收费透明度存在疑虑，信任改善可能直接影响使用与购买决策。",
    "Service complaint": "这类反馈通常涉及响应速度、解决质量和客户体验，适合发展为客服分流、回复辅助或服务流程优化方案。",
    "Anxiety / uncertainty": "这类反馈表明用户在选择或行动前缺少信心，适合提供决策支持、结构化建议和清晰的下一步。",
    "Repeated manual work": "这类反馈说明用户正被重复流程和手动操作困扰，适合转化为自动整理、分类、汇总和报告工具。",
    "Need for automation": "这类反馈明确表达了对自动化的需求，适合转化为自动化工具、AI Agent 或工作流实施服务。",
}

BUSINESS_INTERPRETATIONS = {
    "Time cost pain": "可优先验证用户愿意为节省多少时间付费，并选择一个可量化的高频任务做小型 MVP。",
    "Money cost pain": "机会重点在于降低总成本、避免浪费或提供更透明的方案比较，需要验证实际节省金额。",
    "Learning difficulty": "可测试微课、个性化学习路径、知识拆解 Skill 或陪练服务，并用完成率验证价值。",
    "Tool usability problem": "可探索智能帮助台、错误诊断 Skill、上手辅导或特定软件的轻量辅助产品。",
    "Information gap": "可探索知识库问答、研究摘要、监控报告、教程内容或专业信息整理服务。",
    "Trust issue": "可探索评价分析、证据核验、风险提示或透明度审计，但必须避免替用户作出未经验证的结论。",
    "Service complaint": "可探索工单分类、优先级判断、回复草稿和升级提醒，商业价值可用响应时间衡量。",
    "Anxiety / uncertainty": "可探索决策模板、选项比较和行动计划；产品表达应提供支持，而不是制造焦虑。",
    "Repeated manual work": "自动化适配度通常较高，可从输入稳定、规则清晰、风险较低的重复任务开始。",
    "Need for automation": "可先绘制触发条件、处理步骤、人工审批和异常分支，再验证用户是否愿意购买实施服务。",
}

MONETIZATION_ANGLES = {
    "Time cost pain": "可以包装成效率诊断、流程优化、时间审计或按月维护的自动化服务。",
    "Money cost pain": "可以包装成成本比较工具、订阅审计、采购决策支持或降本咨询服务。",
    "Learning difficulty": "可以包装成学习辅助工具、课程拆解服务、复习资料生成器或知识付费内容。",
    "Tool usability problem": "可以包装成教程内容、工具替代方案推荐、SOP 模板或上手训练服务。",
    "Information gap": "可以包装成信息监控 Agent、行业趋势简报、选题库或咨询报告服务。",
    "Trust issue": "可以包装成测评内容、购买决策助手、评论分析工具或避坑指南。",
    "Service complaint": "可以包装成客服分流 Agent、回复模板库、工单自动化或服务流程优化。",
    "Anxiety / uncertainty": "可以包装成选择比较工具、决策模板、规划陪跑或结构化咨询服务。",
    "Repeated manual work": "可以包装成自动化工作流搭建服务、企业内部效率工具、周报/月报自动生成方案。",
    "Need for automation": "可以包装成 AI 工作流设计、实施、员工培训和持续优化服务。",
}

TARGET_SCENARIOS = {
    "Time cost pain": "内容创作者运营、小商家日常管理、中小企业流程优化",
    "Money cost pain": "SaaS 工具采购、创作者订阅管理、小企业降本",
    "Learning difficulty": "留学生学习、在线课程、课程卖课引流、企业培训",
    "Tool usability problem": "SaaS 工具评测、新用户上手、软件客服与知识库",
    "Information gap": "内容创作者选题、行业研究、竞品监控、社交媒体评论分析",
    "Trust issue": "产品测评、购买决策、课程与工具避坑、品牌口碑分析",
    "Service complaint": "客服与售后、电商运营、课程服务、SaaS 客户成功",
    "Anxiety / uncertainty": "学习规划、职业选择、内容定位、产品选择",
    "Repeated manual work": "小商家运营、内容创作者报表、中小企业流程自动化",
    "Need for automation": "中小企业流程自动化、客服工作流、营销运营与定期报告",
}

PORTFOLIO_VALUES = {
    "Time cost pain": "适合展示流程拆解、效率指标设计、自动化建议和节省时间的量化方法。",
    "Money cost pain": "适合展示商业价值判断、成本信号提取、方案比较和 ROI 假设设计。",
    "Learning difficulty": "适合展示文本拆解、个性化学习 Skill、内容产品设计和用户测试能力。",
    "Tool usability problem": "适合展示问题分类、知识库检索、诊断流程和人机协作设计。",
    "Information gap": "适合展示信息抽取、摘要、监控、知识组织和研究 Agent 的产品思路。",
    "Trust issue": "适合展示评论分析、风险信号识别、证据呈现和负责任的产品边界。",
    "Service complaint": "适合展示情绪识别、工单分类、回复辅助和客服 Dashboard 能力。",
    "Anxiety / uncertainty": "适合展示需求洞察、决策支持、结构化输出和安全表达能力。",
    "Repeated manual work": "适合展示文本分析、需求洞察、商业评分、自动化建议和 Dashboard 展示能力。",
    "Need for automation": "适合展示 Agent 工作流设计、触发与审批逻辑、异常处理和 MVP 验证能力。",
}

REAL_USER_PAINS = {
    "Time cost pain": "用户不是单纯嫌慢，而是希望减少等待和低价值劳动，把时间投入到更重要的任务。",
    "Money cost pain": "用户担心费用不透明、持续订阅或投入没有带来相应回报。",
    "Learning difficulty": "用户缺少可执行的学习步骤、适合自身基础的解释和及时反馈。",
    "Tool usability problem": "用户无法稳定完成目标任务，故障和复杂界面正在消耗耐心与生产力。",
    "Information gap": "用户拥有零散信息，却缺少可信、清晰、可用于决策的整理结果。",
    "Trust issue": "用户无法判断承诺、评价、收费和隐私风险是否可信，因此不敢行动或购买。",
    "Service complaint": "用户需要的是及时解决问题和明确下一步，而不是重复沟通或模板化敷衍。",
    "Anxiety / uncertainty": "用户缺少判断标准和下一步路径，选择成本正在阻碍行动。",
    "Repeated manual work": "用户希望减少复制、整理、分类和报告等低价值重复劳动。",
    "Need for automation": "用户已经意识到现有流程可以自动化，但缺少设计、实施和风险控制能力。",
}

AI_SOLUTION_DIRECTIONS = {
    "Time cost pain": "可做周报自动生成 Agent、任务瓶颈分析 Skill 或资料批量整理 Workflow。",
    "Money cost pain": "可做订阅成本监控 Agent、方案对比 Skill 或费用异常提醒 Workflow。",
    "Learning difficulty": "可做学习教练 Agent、课程拆解 Skill 或复习卡片生成 Workflow。",
    "Tool usability problem": "可做软件帮助 Agent、错误诊断 Skill 或知识库分流 Workflow。",
    "Information gap": "可做研究 Agent、信息摘要 Skill 或行业监控 Workflow。",
    "Trust issue": "可做评论分析 Agent、声明核验 Skill 或人工复核风险清单 Workflow。",
    "Service complaint": "可做客服分流 Agent、投诉摘要 Skill 或超时升级 Workflow。",
    "Anxiety / uncertainty": "可做决策支持 Agent、选项比较 Skill 或行动计划 Workflow。",
    "Repeated manual work": "可做周报自动生成 Agent、评论批量分析 Skill 或资料自动整理 Workflow。",
    "Need for automation": "可做流程设计 Agent、自动化规格生成 Skill 或带人工审批的 Workflow。",
}

CONTENT_DIRECTIONS = {
    "Time cost pain": "制作时间黑洞盘点、自动化前后对比和效率改造案例。",
    "Money cost pain": "制作隐性成本拆解、订阅避坑和工具性价比对比。",
    "Learning difficulty": "制作新手学习路径、错误方法复盘和知识拆解教程。",
    "Tool usability problem": "制作一分钟排错、工具上手 SOP 和替代方案测评。",
    "Information gap": "制作信息整理框架、行业简报和可收藏的研究清单。",
    "Trust issue": "制作购买避坑、评价可信度分析和风险检查清单。",
    "Service complaint": "制作客服回复对比、投诉处理 SOP 和服务体验案例。",
    "Anxiety / uncertainty": "制作决策模板、选择比较和低压力行动指南。",
    "Repeated manual work": "制作重复任务自动化演示、效率对比和小型案例研究。",
    "Need for automation": "制作自动化选题方法、流程搭建实录和实施避坑指南。",
}

VALIDATION_SUGGESTIONS = {
    "Time cost pain": "找 3–5 位真实用户记录一周耗时，用 MVP 自动处理一次并比较节省时间。",
    "Money cost pain": "收集 3–5 份真实费用场景，验证用户是否愿意为可量化的节省付费。",
    "Learning difficulty": "让 5 位新手试用一段拆解后的学习内容，对比理解率和完成率。",
    "Tool usability problem": "选一个高频可复现问题做引导原型，观察用户能否独立解决。",
    "Information gap": "向目标用户交付一份手工版简报，确认它是否真正改善决策效率。",
    "Trust issue": "测试风险清单能否帮助用户判断，同时请专业人士检查表述边界。",
    "Service complaint": "用历史合成工单测试分类与草稿质量，记录人工修改率和响应时间。",
    "Anxiety / uncertainty": "让 3–5 位用户使用决策模板，观察是否能形成明确下一步。",
    "Repeated manual work": "找 3–5 个真实用户，收集每周重复任务，用 MVP 完成一次自动化 demo。",
    "Need for automation": "选一个低风险流程做半自动原型，记录成功率、异常情况和人工介入点。",
}

OPPORTUNITY_ACTIONS = {
    "高机会（High Opportunity）": "建议优先做小型 MVP，并找真实用户验证。（Build a small MVP and test with real users.）",
    "中等机会（Medium Opportunity）": "建议先做内容选题，并继续收集更多案例。（Create content and collect more examples.）",
    "观察机会（Watchlist Opportunity）": "建议继续观察，等待更强的需求信号。（Keep monitoring and wait for stronger signals.）",
    "低优先级（Low Priority）": "当前阶段不建议优先投入。（Not a priority for the current stage.）",
}


def _count(text: str, words: tuple[str, ...]) -> int:
    lowered = text.casefold()
    return sum(lowered.count(word.casefold()) for word in words)


def score_emotion_intensity(text: str) -> int:
    """Calculate negative emotion intensity from 0 to 5."""
    score = min(2, _count(text, COMPLAINT_WORDS))
    score += min(2, _count(text, URGENCY_WORDS) * 2)
    score += min(2, _count(text, NEGATIVE_WORDS))
    score += min(1, _count(text, INTENSIFIERS))
    if re.search(r"[!?！？]{2,}", text) or re.search(r"\b[A-Z]{4,}\b", text):
        score += 1
    return min(5, score)


def _keyword_signal_score(texts: pd.Series, keywords: tuple[str, ...]) -> float:
    """Score a signal from keyword coverage (70%) and repeated evidence (30%)."""
    if texts.empty:
        return 0.0
    match_counts = texts.astype(str).map(lambda text: _count(text, keywords))
    coverage = float((match_counts > 0).mean())
    density = min(float(match_counts.mean()) / 2.0, 1.0)
    raw_score = coverage * 65.0 + density * 35.0
    # A single matching comment is a weaker business signal than repeated evidence.
    evidence_confidence = min(1.0, 0.55 + 0.15 * math.log2(len(texts) + 1))
    return min(100.0, raw_score * evidence_confidence)


def _market_signal_strength(frequency: float, emotion: float, total: float) -> str:
    signal = frequency * 0.40 + emotion * 0.25 + total * 0.35
    if signal >= 60:
        return "强"
    if signal >= 35:
        return "中"
    return "弱"


def _user_urgency(texts: pd.Series, emotion_score: float) -> str:
    keyword_score = _keyword_signal_score(texts, URGENCY_BUSINESS_KEYWORDS)
    urgency = emotion_score * 0.55 + keyword_score * 0.45
    if urgency >= 55:
        return "高"
    if urgency >= 25:
        return "中"
    return "低"


def get_opportunity_level(score: float) -> str:
    """Convert a total score into a Chinese-first business priority tier."""
    if score >= 80:
        return "高机会（High Opportunity）"
    if score >= 60:
        return "中等机会（Medium Opportunity）"
    if score >= 40:
        return "观察机会（Watchlist Opportunity）"
    return "低优先级（Low Priority）"


def build_opportunity_scores(analyzed: pd.DataFrame) -> pd.DataFrame:
    """Build the category-level SPF-002 evidence and opportunity table."""
    columns = [
        "pain_category", "comment_count", "percentage_of_total_comments",
        "average_emotion_intensity", "frequency_score", "emotion_score",
        "payment_potential_score", "ai_automation_fit_score", "content_value_score",
        "total_opportunity_score", "opportunity_level", "recommended_action",
        "top_example_comments", "why_it_matters", "business_interpretation",
        "market_signal_strength", "user_urgency", "monetization_angle",
        "target_scenario", "portfolio_value", "real_user_pain",
        "ai_solution_direction", "content_direction", "validation_suggestion",
    ]
    detected = analyzed[analyzed["detected_categories"].map(bool)].copy()
    if detected.empty:
        return pd.DataFrame(columns=columns)

    exploded = detected.explode("detected_categories").rename(
        columns={"detected_categories": "pain_category"}
    )
    maximum_count = int(exploded["pain_category"].value_counts().max())
    rows: list[dict[str, object]] = []
    for category, category_rows in exploded.groupby("pain_category"):
        comment_count = len(category_rows)
        average_emotion = float(category_rows["emotion_intensity_score"].mean())
        examples = (
            category_rows.sort_values("emotion_intensity_score", ascending=False)
            ["original_text"].astype(str).drop_duplicates().head(3).tolist()
        )
        frequency_score = comment_count / maximum_count * 100
        emotion_score = average_emotion / 5 * 100
        payment_score = _keyword_signal_score(category_rows["cleaned_text"], PAYMENT_KEYWORDS)
        automation_score = _keyword_signal_score(category_rows["cleaned_text"], AUTOMATION_KEYWORDS)
        content_score = _keyword_signal_score(category_rows["cleaned_text"], CONTENT_KEYWORDS)
        total_score = (
            frequency_score * 0.25
            + emotion_score * 0.20
            + payment_score * 0.25
            + automation_score * 0.20
            + content_score * 0.10
        )
        level = get_opportunity_level(total_score)
        rows.append({
            "pain_category": category,
            "comment_count": comment_count,
            "percentage_of_total_comments": comment_count / len(analyzed) * 100,
            "average_emotion_intensity": average_emotion,
            "frequency_score": frequency_score,
            "emotion_score": emotion_score,
            "payment_potential_score": payment_score,
            "ai_automation_fit_score": automation_score,
            "content_value_score": content_score,
            "total_opportunity_score": total_score,
            "opportunity_level": level,
            "recommended_action": OPPORTUNITY_ACTIONS[level],
            "top_example_comments": examples,
            "why_it_matters": WHY_IT_MATTERS[category],
            "business_interpretation": BUSINESS_INTERPRETATIONS[category],
            "market_signal_strength": _market_signal_strength(
                frequency_score, emotion_score, total_score
            ),
            "user_urgency": _user_urgency(category_rows["cleaned_text"], emotion_score),
            "monetization_angle": MONETIZATION_ANGLES[category],
            "target_scenario": TARGET_SCENARIOS[category],
            "portfolio_value": PORTFOLIO_VALUES[category],
            "real_user_pain": REAL_USER_PAINS[category],
            "ai_solution_direction": AI_SOLUTION_DIRECTIONS[category],
            "content_direction": CONTENT_DIRECTIONS[category],
            "validation_suggestion": VALIDATION_SUGGESTIONS[category],
        })

    result = pd.DataFrame(rows)
    numeric_columns = [
        "percentage_of_total_comments", "average_emotion_intensity", "frequency_score",
        "emotion_score", "payment_potential_score", "ai_automation_fit_score",
        "content_value_score", "total_opportunity_score",
    ]
    result[numeric_columns] = result[numeric_columns].round(1)
    return result[columns].sort_values(
        ["total_opportunity_score", "comment_count"], ascending=False
    ).reset_index(drop=True)


def get_top_opportunities(opportunities: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    """Return a safe copy of the highest-scoring opportunities."""
    return opportunities.sort_values("total_opportunity_score", ascending=False).head(limit).copy()
