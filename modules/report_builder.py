"""Pipeline orchestration and Markdown reporting for SPF-002."""

from __future__ import annotations

from datetime import datetime
from html import escape

import pandas as pd

from modules.export_utils import (
    build_export_filename,
    save_analysis_csv,
    save_text_report,
)
from modules.idea_generator import generate_ideas
from modules.pain_detector import detect_pain_categories
from modules.scoring import (
    build_opportunity_scores,
    get_top_opportunities,
    score_emotion_intensity,
)
from modules.text_cleaner import clean_comments


CATEGORY_DISPLAY_NAMES = {
    "Time cost pain": "时间成本痛点（Time Cost Pain）",
    "Money cost pain": "金钱成本痛点（Money Cost Pain）",
    "Learning difficulty": "学习困难（Learning Difficulty）",
    "Tool usability problem": "工具易用性问题（Tool Usability Problem）",
    "Information gap": "信息差痛点（Information Gap）",
    "Trust issue": "信任问题（Trust Issue）",
    "Service complaint": "服务投诉（Service Complaint）",
    "Anxiety / uncertainty": "焦虑与不确定性（Anxiety / Uncertainty）",
    "Repeated manual work": "重复性手工工作（Repeated Manual Work）",
    "Need for automation": "自动化需求（Need for Automation）",
}

MVP_IDEAS = {
    "Time cost pain": "做一个读取任务记录并自动生成耗时瓶颈与改进清单的轻量工具。",
    "Money cost pain": "做一个导入订阅或费用清单后自动标记重复支出和隐性成本的 MVP。",
    "Learning difficulty": "做一个把单篇课程材料拆成重点、例子、复习卡和测试题的学习 Skill。",
    "Tool usability problem": "做一个只覆盖某款工具 Top 10 常见问题的诊断与引导 Agent。",
    "Information gap": "做一个从用户授权资料中生成带来源摘要和行动清单的研究 Agent。",
    "Trust issue": "做一个汇总授权评价并输出信任信号与人工复核清单的分析工具。",
    "Service complaint": "做一个对 CSV 工单进行分类、紧急度判断和回复草稿生成的 MVP。",
    "Anxiety / uncertainty": "做一个将选项、约束和风险整理成一页决策卡的轻量产品。",
    "Repeated manual work": "做一个只处理 CSV 评论数据的整理、分类和周报自动生成工具。",
    "Need for automation": "做一个把流程描述转换为触发、步骤、审批和异常清单的设计助手。",
}

NEXT_DATA_TO_COLLECT = {
    "Time cost pain": "任务出现频率、当前耗时、等待时间和用户期望节省的时间。",
    "Money cost pain": "实际支出、损失金额、替代方案和可接受付费价格。",
    "Learning difficulty": "学习基础、卡点、完成率、理解率和复习行为。",
    "Tool usability problem": "故障频率、复现步骤、完成任务失败率和支持请求数量。",
    "Information gap": "常见问题、可信来源、查找耗时和信息对决策的实际影响。",
    "Trust issue": "影响购买的信任信号、风险类型和用户需要的证据。",
    "Service complaint": "问题类型、响应时间、重复联系率、解决率和人工修改率。",
    "Anxiety / uncertainty": "被推迟的决定、判断标准、行动完成率和用户反馈。",
    "Repeated manual work": "每周执行次数、单次耗时、输入格式、异常比例和期望输出。",
    "Need for automation": "流程频率、规则稳定性、异常分支、审批要求和失败成本。",
}

PRODUCT_RISKS = {
    "Trust issue": "规则可能误判评价和可信度，必须显示证据、保留人工复核并避免作出事实定论。",
    "Anxiety / uncertainty": "产品不应替代专业建议或利用焦虑促成购买，应清楚说明能力边界。",
    "Need for automation": "自动执行可能放大流程错误，应先半自动测试并保留审批、日志和回退机制。",
}


def analyze_comments(raw_data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run cleaning, detection, evidence-based scoring, and idea generation."""
    analyzed = clean_comments(raw_data)
    analyzed["detected_categories"] = analyzed["cleaned_text"].map(detect_pain_categories)
    analyzed["primary_category"] = analyzed["detected_categories"].map(
        lambda categories: categories[0] if categories else "No pain detected"
    )
    analyzed["emotion_intensity_score"] = analyzed["cleaned_text"].map(
        score_emotion_intensity
    )
    opportunities = build_opportunity_scores(analyzed)
    return analyzed, opportunities, generate_ideas(opportunities)


def build_category_examples(analyzed: pd.DataFrame, limit: int = 3) -> dict[str, list[str]]:
    """Select high-intensity evidence comments for each category."""
    examples: dict[str, list[str]] = {}
    for _, row in analyzed.sort_values("emotion_intensity_score", ascending=False).iterrows():
        for category in row["detected_categories"]:
            examples.setdefault(category, [])
            if len(examples[category]) < limit:
                examples[category].append(str(row["original_text"]))
    return examples


def exportable_analysis(analyzed: pd.DataFrame) -> pd.DataFrame:
    """Convert list values into CSV-friendly strings."""
    exported = analyzed.copy()
    exported["detected_categories"] = exported["detected_categories"].map("; ".join)
    return exported


def generate_product_lens(
    opportunities: pd.DataFrame, ideas: pd.DataFrame, limit: int = 3
) -> pd.DataFrame:
    """Generate a rule-based Founder / Product Lens for top opportunities."""
    columns = [
        "pain_category", "mvp_idea", "first_user_test_method", "data_to_collect_next",
        "risk_or_limitation", "suggested_next_step",
    ]
    idea_lookup = ideas.set_index("pain_category").to_dict("index") if not ideas.empty else {}
    rows = []
    for _, opportunity in get_top_opportunities(opportunities, limit).iterrows():
        category = opportunity["pain_category"]
        idea = idea_lookup.get(category, {})
        risk = PRODUCT_RISKS.get(
            category,
            "当前版本依赖关键词和规则，可能无法理解反讽、复杂语境或行业差异；它适合初筛，不适合作为最终商业判断。",
        )
        rows.append({
            "pain_category": category,
            "mvp_idea": MVP_IDEAS[category],
            "first_user_test_method": opportunity["validation_suggestion"],
            "data_to_collect_next": NEXT_DATA_TO_COLLECT[category],
            "risk_or_limitation": risk,
            "suggested_next_step": idea.get(
                "recommended_next_action", opportunity["recommended_action"]
            ),
        })
    return pd.DataFrame(rows, columns=columns)


def _display_category(category: str) -> str:
    return CATEGORY_DISPLAY_NAMES.get(category, category)


def build_markdown_report(
    analyzed: pd.DataFrame,
    opportunities: pd.DataFrame,
    ideas: pd.DataFrame,
    total_comments: int | None = None,
    generated_at: datetime | None = None,
) -> str:
    """Generate the complete Chinese-first SPF-003 Markdown report."""
    report_time = generated_at or datetime.now().astimezone()
    input_count = total_comments if total_comments is not None else len(analyzed)
    detected_count = int(analyzed["detected_categories"].map(bool).sum())
    source_count = analyzed["source"].nunique() if "source" in analyzed else 0
    lines = [
        "# Social Pain Finder Agent｜用户痛点与商业机会分析报告",
        "",
        f"生成时间：{report_time.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        "",
        "## 数据集摘要",
        "",
        f"- 分析评论数量：{input_count}",
        f"- 去重后评论数量：{len(analyzed)}",
        f"- 识别出的痛点类别数量：{len(opportunities)}",
        f"- 包含痛点信号的评论：{detected_count}",
        f"- 数据来源数量：{source_count}",
        f"- 平均情绪强度：{analyzed['emotion_intensity_score'].mean():.1f} / 5",
        "",
        "## 商业机会评分公式",
        "",
        "总商业机会分数 = 频率分数 × 25% + 情绪分数 × 20% + "
        "付费潜力 × 25% + AI 自动化适配度 × 20% + 内容价值 × 10%。",
        "付费潜力、AI 自动化适配度和内容价值来自当前评论中的中英文关键词信号。",
        "",
        "## 痛点分类排行榜",
        "",
    ]
    if opportunities.empty:
        lines.append("当前数据没有匹配到已配置的痛点类别。")
    else:
        for index, row in opportunities.iterrows():
            lines.append(
                f"{index + 1}. **{_display_category(row['pain_category'])}**："
                f"{row['comment_count']} 条评论，占比 {row['percentage_of_total_comments']:.1f}%，"
                f"总分 {row['total_opportunity_score']:.1f}/100，{row['opportunity_level']}"
            )

    top_five = get_top_opportunities(opportunities)
    idea_lookup = ideas.set_index("pain_category").to_dict("index") if not ideas.empty else {}
    lines.extend(["", "## Top 5 商业机会", ""])
    for _, row in top_five.iterrows():
        category = row["pain_category"]
        lines.extend([
            f"### {_display_category(category)}｜{row['total_opportunity_score']:.1f}/100",
            "",
            f"- 机会等级：{row['opportunity_level']}",
            f"- 为什么重要：{row['why_it_matters']}",
            f"- 商业解读：{row['business_interpretation']}",
            f"- 市场信号强度：{row['market_signal_strength']}",
            f"- 用户紧迫度：{row['user_urgency']}",
            f"- 用户真实痛点：{row['real_user_pain']}",
            f"- 可做 AI Agent / AI Skill：{row['ai_solution_direction']}",
            f"- 可做内容选题：{row['content_direction']}",
            f"- 变现角度：{row['monetization_angle']}",
            f"- 推荐下一步行动：{row['recommended_action']}",
            "- 证据评论：",
        ])
        for comment in row["top_example_comments"]:
            lines.append(f"  - {comment}")

        idea = idea_lookup.get(category)
        if idea:
            lines.extend([
                f"- AI Agent 建议：{idea['ai_agent_idea']}",
                f"- AI Skill 建议：{idea['ai_skill_idea']}",
                f"- 自动化工作流建议：{idea['automation_workflow_idea']}",
                f"- 内容选题建议：{idea['short_video_topic']}",
                f"- 小红书 / 抖音角度：{idea['xiaohongshu_douyin_angle']}",
                f"- 可付费服务：{idea['paid_service_idea']}",
            ])
        lines.append("")

    lines.extend(["## 商业解读增强", ""])
    for _, row in top_five.iterrows():
        lines.extend([
            f"### {_display_category(row['pain_category'])}",
            "",
            f"- 市场信号强度：{row['market_signal_strength']}",
            f"- 用户紧迫度：{row['user_urgency']}",
            f"- 变现角度：{row['monetization_angle']}",
            f"- 适用场景：{row['target_scenario']}",
            f"- 作品集展示价值：{row['portfolio_value']}",
            "",
        ])

    product_lens = generate_product_lens(opportunities, ideas)
    lines.extend(["## 产品视角建议（Founder / Product Lens）", ""])
    for _, row in product_lens.iterrows():
        lines.extend([
            f"### {_display_category(row['pain_category'])}",
            "",
            f"- MVP idea：{row['mvp_idea']}",
            f"- 首轮用户测试：{row['first_user_test_method']}",
            f"- 下一步收集数据：{row['data_to_collect_next']}",
            f"- 推荐下一步：{row['suggested_next_step']}",
            "",
        ])

    lines.extend([
        "## 风险与限制",
        "",
    ])
    for _, row in product_lens.iterrows():
        lines.append(f"- **{_display_category(row['pain_category'])}：** {row['risk_or_limitation']}")

    lines.extend([
        "## 隐私与合规说明",
        "",
        "本报告仅分析用户主动上传或粘贴的数据。项目不包含网络爬虫、非官方社交媒体抓取、"
        "云数据库或 API Key。请在分析前删除个人隐私、敏感信息和真实客户身份信息。",
        "",
        "## Disclaimer",
        "",
        "本报告由本地规则生成，仅用于研究和机会发现。评分不代表已验证的市场需求、财务回报、"
        "法律意见或自动化可行性；重要结论必须经过人工检查和真实用户验证。",
    ])
    return "\n".join(lines)


def generate_markdown_report(
    analyzed: pd.DataFrame,
    opportunities: pd.DataFrame,
    ideas: pd.DataFrame,
    total_comments: int | None = None,
    generated_at: datetime | None = None,
) -> str:
    """Backward-compatible alias retained for SPF-001 through SPF-002B callers."""
    return build_markdown_report(
        analyzed, opportunities, ideas, total_comments, generated_at
    )


def build_html_report(
    analyzed: pd.DataFrame,
    opportunities: pd.DataFrame,
    ideas: pd.DataFrame,
    total_comments: int | None = None,
    generated_at: datetime | None = None,
) -> str:
    """Generate a self-contained UTF-8 HTML report with no online resources."""
    report_time = generated_at or datetime.now().astimezone()
    input_count = total_comments if total_comments is not None else len(analyzed)
    detected_count = int(analyzed["detected_categories"].map(bool).sum())
    top_five = get_top_opportunities(opportunities)
    product_lens = generate_product_lens(opportunities, ideas)
    idea_lookup = ideas.set_index("pain_category").to_dict("index") if not ideas.empty else {}

    ranking_rows = "".join(
        "<tr>"
        f"<td>{escape(_display_category(row['pain_category']))}</td>"
        f"<td>{int(row['comment_count'])}</td>"
        f"<td>{row['percentage_of_total_comments']:.1f}%</td>"
        f"<td>{row['total_opportunity_score']:.1f}</td>"
        f"<td>{escape(str(row['opportunity_level']))}</td>"
        "</tr>"
        for _, row in opportunities.iterrows()
    ) or '<tr><td colspan="5">当前没有识别到痛点类别。</td></tr>'

    opportunity_cards: list[str] = []
    for _, row in top_five.iterrows():
        category = row["pain_category"]
        comments = "".join(
            f"<li>{escape(str(comment))}</li>" for comment in row["top_example_comments"]
        )
        idea = idea_lookup.get(category, {})
        idea_html = ""
        if idea:
            idea_html = (
                "<h4>AI Agent / AI Skill 与内容建议</h4>"
                f"<p><strong>AI Agent：</strong>{escape(idea['ai_agent_idea'])}</p>"
                f"<p><strong>AI Skill：</strong>{escape(idea['ai_skill_idea'])}</p>"
                f"<p><strong>自动化：</strong>{escape(idea['automation_workflow_idea'])}</p>"
                f"<p><strong>内容选题：</strong>{escape(idea['short_video_topic'])}</p>"
                f"<p><strong>小红书 / 抖音角度：</strong>{escape(idea['xiaohongshu_douyin_angle'])}</p>"
            )
        opportunity_cards.append(
            '<article class="card">'
            f"<h3>{escape(_display_category(category))}｜{row['total_opportunity_score']:.1f}/100</h3>"
            f"<p><span class='tag'>{escape(str(row['opportunity_level']))}</span> "
            f"市场信号：<strong>{escape(str(row['market_signal_strength']))}</strong>　"
            f"用户紧迫度：<strong>{escape(str(row['user_urgency']))}</strong></p>"
            f"<p><strong>为什么这是一个机会：</strong>{escape(str(row['why_it_matters']))}</p>"
            f"<p><strong>用户真实痛点：</strong>{escape(str(row['real_user_pain']))}</p>"
            f"<p><strong>变现角度：</strong>{escape(str(row['monetization_angle']))}</p>"
            f"<p><strong>适用场景：</strong>{escape(str(row['target_scenario']))}</p>"
            f"<p><strong>作品集展示价值：</strong>{escape(str(row['portfolio_value']))}</p>"
            f"<p><strong>推荐行动：</strong>{escape(str(row['recommended_action']))}</p>"
            f"<h4>证据评论</h4><ul>{comments}</ul>{idea_html}</article>"
        )

    product_cards = "".join(
        '<article class="card">'
        f"<h3>{escape(_display_category(row['pain_category']))}</h3>"
        f"<p><strong>MVP idea：</strong>{escape(row['mvp_idea'])}</p>"
        f"<p><strong>首轮用户测试：</strong>{escape(row['first_user_test_method'])}</p>"
        f"<p><strong>下一步收集数据：</strong>{escape(row['data_to_collect_next'])}</p>"
        f"<p><strong>风险与限制：</strong>{escape(row['risk_or_limitation'])}</p>"
        f"<p><strong>建议下一步：</strong>{escape(row['suggested_next_step'])}</p>"
        "</article>"
        for _, row in product_lens.iterrows()
    ) or '<p class="muted">当前没有可生成的产品视角建议。</p>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Social Pain Finder Agent｜分析报告</title>
  <style>
    :root {{ color-scheme: light; --ink:#172033; --muted:#667085; --line:#d9e0ea; --accent:#2855d9; --soft:#f5f7fb; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:#eef2f7; color:var(--ink); font-family:"Microsoft YaHei","PingFang SC","Segoe UI",sans-serif; line-height:1.65; }}
    main {{ width:min(1120px, calc(100% - 32px)); margin:32px auto; background:white; padding:40px; border-radius:16px; box-shadow:0 8px 30px rgba(20,35,70,.08); }}
    h1 {{ line-height:1.25; margin-top:0; }} h2 {{ margin-top:40px; border-bottom:2px solid var(--line); padding-bottom:8px; }}
    .meta,.muted {{ color:var(--muted); }} .summary {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; }}
    .metric,.card {{ border:1px solid var(--line); border-radius:12px; padding:18px; background:#fff; }}
    .metric strong {{ display:block; font-size:1.55rem; color:var(--accent); }} .card {{ margin:14px 0; }}
    .tag {{ display:inline-block; background:#eaf0ff; color:#2146b7; border-radius:999px; padding:2px 10px; }}
    table {{ width:100%; border-collapse:collapse; margin:14px 0; font-size:.94rem; }} th,td {{ border:1px solid var(--line); padding:10px; text-align:left; vertical-align:top; }}
    th {{ background:var(--soft); }} code {{ background:var(--soft); padding:2px 5px; }}
    @media (max-width:650px) {{ main {{ padding:22px; }} table {{ display:block; overflow-x:auto; }} }}
  </style>
</head>
<body><main>
  <h1>Social Pain Finder Agent｜用户痛点与商业机会分析报告</h1>
  <p class="meta">生成时间：{escape(report_time.strftime('%Y-%m-%d %H:%M:%S %Z'))}</p>
  <h2>数据集摘要</h2>
  <div class="summary">
    <div class="metric">分析评论数量<strong>{input_count}</strong></div>
    <div class="metric">去重后评论数量<strong>{len(analyzed)}</strong></div>
    <div class="metric">识别出的痛点类别<strong>{len(opportunities)}</strong></div>
    <div class="metric">平均情绪强度<strong>{analyzed['emotion_intensity_score'].mean():.1f} / 5</strong></div>
  </div>
  <p class="muted">包含痛点信号的评论：{detected_count}</p>
  <h2>商业机会评分公式</h2>
  <p>总商业机会分数 = 频率 25% + 情绪 20% + 付费潜力 25% + AI 自动化适配度 20% + 内容价值 10%。</p>
  <h2>痛点分类排行榜</h2>
  <table><thead><tr><th>痛点分类</th><th>评论数量</th><th>占比</th><th>总分</th><th>机会等级</th></tr></thead><tbody>{ranking_rows}</tbody></table>
  <h2>Top 5 商业机会</h2>
  {''.join(opportunity_cards) or '<p class="muted">当前没有可展示的商业机会。</p>'}
  <h2>商业解读增强</h2>
  <p>以上机会卡包含市场信号强度、用户紧迫度、变现角度、适用场景与作品集展示价值。</p>
  <h2>产品视角建议（Founder / Product Lens）</h2>
  {product_cards}
  <h2>风险与限制</h2>
  <p>当前分析依赖本地关键词和规则，可能无法理解反讽、复杂语境与行业差异。结果适合初筛和形成假设，不适合作为最终商业、法律或财务判断。</p>
  <h2>隐私与合规说明</h2>
  <p>本报告仅分析用户主动上传或粘贴的数据。项目不包含爬虫、非官方社交媒体抓取、云数据库或 API Key。请先删除个人隐私、敏感信息和真实客户身份信息。</p>
  <h2>Disclaimer</h2>
  <p>本报告由本地规则生成，仅用于研究和机会发现。重要结论必须经过人工检查和真实用户验证。</p>
</main></body></html>"""
