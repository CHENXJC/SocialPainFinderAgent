"""Explainable English and Chinese keyword rules for pain detection."""

from __future__ import annotations

import re


PAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Time cost pain": ("takes too long", "time-consuming", "waste of time", "slow", "hours", "delay", "太慢", "浪费时间", "耗时", "花太久", "等很久", "效率低"),
    "Money cost pain": ("expensive", "overpriced", "cost too much", "price", "subscription", "refund", "太贵", "价格", "费用", "收费", "不值", "退款"),
    "Learning difficulty": ("hard to learn", "confusing", "steep learning", "don't understand", "tutorial", "learning curve", "学不会", "看不懂", "太难", "教程", "学习曲线", "不明白"),
    "Tool usability problem": ("bug", "crash", "broken", "hard to use", "interface", "login", "doesn't work", "not working", "卡住", "崩溃", "闪退", "难用", "界面", "登录", "出错", "故障"),
    "Information gap": ("can't find", "no documentation", "unclear", "missing information", "information overload", "不知道哪里", "找不到", "没有说明", "信息不足", "信息太多", "不清楚", "缺少资料"),
    "Trust issue": ("don't trust", "misleading", "scam", "fake", "privacy", "security", "hidden fee", "不信任", "骗人", "虚假", "隐私", "安全", "隐藏费用", "割韭菜"),
    "Service complaint": ("customer service", "support", "no response", "ignored", "rude", "complaint", "客服", "没人回复", "不回复", "态度差", "售后", "投诉"),
    "Anxiety / uncertainty": ("anxious", "worried", "overwhelmed", "uncertain", "afraid", "stress", "panic", "焦虑", "担心", "迷茫", "不确定", "害怕", "压力", "慌"),
    "Repeated manual work": ("every day", "repetitive", "copy and paste", "manually", "spreadsheet", "repeat", "每天", "重复", "复制粘贴", "手动", "表格", "反复"),
    "Need for automation": ("automate", "automation", "automatically", "one click", "workflow", "integrate", "自动化", "自动", "一键", "工作流", "批量", "集成"),
}


def _matches(text: str, keyword: str) -> bool:
    lowered = text.casefold()
    if keyword.isascii() and " " not in keyword:
        return re.search(rf"\b{re.escape(keyword.casefold())}\b", lowered) is not None
    return keyword.casefold() in lowered


def detect_pain_categories(text: str) -> list[str]:
    """Return all matching categories; a comment may have several."""
    return [
        category for category, keywords in PAIN_KEYWORDS.items()
        if any(_matches(text, keyword) for keyword in keywords)
    ]


def detect_pain(text: str) -> dict[str, object]:
    """Return both the complete category list and a stable primary category."""
    categories = detect_pain_categories(text)
    return {
        "detected_categories": categories,
        "primary_category": categories[0] if categories else "No pain detected",
    }

