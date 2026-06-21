"""SPF-004: Chinese-first, product-grade Streamlit dashboard."""

from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from modules.data_loader import combine_inputs, load_file, load_manual_text, load_path
from modules.report_builder import (
    analyze_comments,
    build_category_examples,
    build_export_filename,
    build_html_report,
    build_markdown_report,
    exportable_analysis,
    generate_product_lens,
    save_analysis_csv,
    save_text_report,
)


ROOT = Path(__file__).parent
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
    "No pain detected": "未识别到痛点（No Pain Detected）",
}


def get_category_display_name(category: str) -> str:
    """Map stable internal category keys to Chinese-first display labels."""
    return CATEGORY_DISPLAY_NAMES.get(category, category)


st.set_page_config(
    page_title="Social Pain Finder Agent｜痛点与商业机会挖掘",
    page_icon="🔎",
    layout="wide",
)
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.8rem; padding-bottom: 4rem; max-width: 1440px;}
      .spf-hero {padding: 1.4rem 1.5rem; border: 1px solid #dce4f0; border-radius: 16px;
                 background: linear-gradient(135deg, #f7f9ff 0%, #eef7ff 100%); margin-bottom: 1rem;}
      .spf-hero h1 {font-size: 2.05rem; line-height: 1.25; margin: 0 0 .55rem 0;}
      .spf-hero p {color: #475467; margin: 0; font-size: 1.02rem;}
      .spf-badges {display: flex; flex-wrap: wrap; gap: .55rem; margin: 1rem 0 .75rem 0;}
      .spf-badge {padding: .35rem .75rem; border-radius: 999px; background: #e8efff;
                  color: #2349a8; border: 1px solid #ccdafc; font-size: .88rem; font-weight: 600;}
      .spf-compliance {font-size: .9rem; color: #667085; margin-top: .7rem;}
      div[data-testid="stMetric"] {border: 1px solid #e0e6ef; border-radius: 12px;
                                   padding: .9rem 1rem; background: #ffffff;}
      div[data-testid="stMetric"] label {color: #667085;}
      h2 {padding-top: .35rem;}
    </style>
    <div class="spf-hero">
      <h1>Social Pain Finder Agent｜社交媒体痛点与商业机会挖掘 Agent</h1>
      <p>从评论、反馈、产品评价和社交媒体文本中，发现高频痛点、情绪强度、商业机会、AI Agent / AI Skill 想法和内容选题方向。</p>
      <div class="spf-badges">
        <span class="spf-badge">本地优先｜Local-first</span>
        <span class="spf-badge">商业机会评分｜Opportunity Scoring</span>
        <span class="spf-badge">AI Agent 选题辅助｜Agent Ideation</span>
      </div>
      <div class="spf-compliance">不包含爬虫，不上传云端，不需要 API Key，仅分析你有权使用的数据。</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("数据输入")
    uploaded_files = st.file_uploader(
        "上传数据",
        type=["csv", "xlsx", "txt"],
        accept_multiple_files=True,
        help="支持 CSV / Excel / TXT，可同时上传多个文件。",
    )
    st.caption("支持 CSV / Excel / TXT")
    use_sample = st.checkbox("包含示例数据", value=not uploaded_files)

    st.divider()
    st.subheader("使用流程")
    st.markdown("1. 上传或粘贴文本\n2. 自动识别痛点\n3. 计算商业机会评分\n4. 导出分析报告")

    st.divider()
    st.subheader("隐私与合规")
    st.warning("仅使用你有权分析的数据。请先删除个人隐私、敏感信息、真实客户身份信息。")

    st.divider()
    st.subheader("当前版本")
    st.markdown("**SPF-004 Product UI Polish**")
    st.caption("Local-first / Rule-based / No API key")

st.header("1. 数据输入与预览")
st.caption("文件上传位于左侧边栏；也可以在下方每行粘贴一条评论或反馈。")
manual_text = st.text_area(
    "手动输入文本",
    placeholder=(
        "例如：\n"
        "这个软件经常崩溃，客服也不回复。\n"
        "I spend three hours every week copying reports manually."
    ),
    height=130,
)

frames: list[pd.DataFrame] = []
for uploaded_file in uploaded_files:
    try:
        frames.append(load_file(uploaded_file, uploaded_file.name))
    except Exception as exc:
        st.error(f"无法读取 {uploaded_file.name}：{exc}")
if manual_text.strip():
    frames.append(load_manual_text(manual_text))
if use_sample:
    try:
        frames.append(load_path(ROOT / "data" / "sample_comments.csv"))
    except Exception as exc:
        st.error(f"无法读取示例数据：{exc}")

raw_data = combine_inputs(frames)
if raw_data.empty:
    st.info("请上传文件、手动输入文本，或勾选“包含示例数据”后开始分析。")
    st.stop()

try:
    analyzed, opportunities, ideas = analyze_comments(raw_data)
except Exception as exc:
    st.error(f"分析未能完成：{exc}")
    st.stop()
if analyzed.empty:
    st.warning("删除空白文本和重复评论后，没有可供分析的有效内容。")
    st.stop()

preview = analyzed[["comment_id", "source", "original_text"]].head(12).rename(
    columns={"comment_id": "评论 ID", "source": "数据来源", "original_text": "原始文本"}
)
st.dataframe(preview, width="stretch", hide_index=True)
st.caption(f"当前预览前 {min(12, len(analyzed))} 条；完整明细位于“痛点分类结果”。")

st.header("2. 核心指标总览")
top_score = float(opportunities.iloc[0]["total_opportunity_score"]) if not opportunities.empty else 0.0
top_category = (
    get_category_display_name(opportunities.iloc[0]["pain_category"])
    if not opportunities.empty else "暂无"
)
metric_row_one = st.columns(3)
metric_row_one[0].metric("总评论数", len(raw_data))
metric_row_one[1].metric("去重后评论数", len(analyzed))
metric_row_one[2].metric("识别出的痛点类别", len(opportunities))
metric_row_two = st.columns(3)
metric_row_two[0].metric("平均情绪强度", f"{analyzed['emotion_intensity_score'].mean():.1f} / 5")
metric_row_two[1].metric("最高商业机会分数", f"{top_score:.1f} / 100")
metric_row_two[2].metric("Top 机会类别", top_category)

st.header("3. 痛点分类结果")
classification_results = analyzed[
    ["comment_id", "original_text", "primary_category", "emotion_intensity_score"]
].copy()
classification_results["primary_category"] = classification_results["primary_category"].map(
    get_category_display_name
)
classification_results = classification_results.rename(columns={
    "comment_id": "评论 ID",
    "original_text": "原始文本",
    "primary_category": "痛点分类（Pain Category）",
    "emotion_intensity_score": "情绪强度（Emotion Intensity）",
})
st.dataframe(classification_results.head(20), width="stretch", hide_index=True)

with st.expander("查看完整分析明细", expanded=False):
    full_detail = analyzed.copy()
    full_detail["detected_categories"] = full_detail["detected_categories"].map(
        lambda categories: "；".join(get_category_display_name(item) for item in categories)
        if categories else "未识别到痛点（No Pain Detected）"
    )
    full_detail = full_detail.rename(columns={
        "comment_id": "评论 ID", "source": "数据来源", "original_text": "原始文本",
        "cleaned_text": "清洗后文本", "detected_categories": "全部痛点分类",
        "primary_category": "内部主分类", "emotion_intensity_score": "情绪强度",
    })
    st.dataframe(full_detail, width="stretch", hide_index=True)

examples = build_category_examples(analyzed)
with st.expander("查看各痛点类别示例评论证据", expanded=False):
    if examples:
        for category in opportunities["pain_category"].tolist():
            st.markdown(f"**{get_category_display_name(category)}**")
            for example in examples.get(category, []):
                st.markdown(f"- {example}")
    else:
        st.info("当前没有已分类的示例评论。")

display_opportunities = opportunities.copy()
if not display_opportunities.empty:
    display_opportunities["pain_category"] = display_opportunities["pain_category"].map(
        get_category_display_name
    )

st.header("4. 商业机会评分系统（Opportunity Scoring System）")
st.write("根据痛点频率、情绪强度，以及付费、自动化和内容价值关键词信号，对机会进行排序。")
st.caption("总分 = 频率 25% + 情绪 20% + 付费潜力 25% + AI 自动化适配度 20% + 内容价值 10%。")
opportunity_columns = [
    "pain_category", "comment_count", "percentage_of_total_comments", "frequency_score",
    "emotion_score", "payment_potential_score", "ai_automation_fit_score",
    "content_value_score", "total_opportunity_score", "opportunity_level",
]
opportunity_table = display_opportunities[opportunity_columns].copy()
if not opportunity_table.empty:
    opportunity_table["percentage_of_total_comments"] = opportunity_table[
        "percentage_of_total_comments"
    ].map(lambda value: f"{value:.1f}%")
opportunity_table = opportunity_table.rename(columns={
    "pain_category": "痛点分类（Pain Category）", "comment_count": "评论数量",
    "percentage_of_total_comments": "占比", "frequency_score": "频率（Frequency）",
    "emotion_score": "情绪（Emotion）", "payment_potential_score": "付费潜力（Payment）",
    "ai_automation_fit_score": "自动化适配度（AI Fit）", "content_value_score": "内容价值（Content）",
    "total_opportunity_score": "总机会分数（Total Score）", "opportunity_level": "机会等级",
})
st.dataframe(opportunity_table, width="stretch", hide_index=True)

st.subheader("可视化分析（Charts）")
if display_opportunities.empty:
    st.info("当前没有足够的痛点类别生成图表。")
else:
    distribution_chart = px.bar(
        display_opportunities.sort_values("comment_count"), x="comment_count", y="pain_category",
        orientation="h", title="痛点类别分布",
        labels={"comment_count": "评论数量", "pain_category": "痛点分类"},
    )
    distribution_chart.update_layout(height=430, margin=dict(l=0, r=10, t=45, b=0))

    score_chart = px.bar(
        display_opportunities.sort_values("total_opportunity_score"),
        x="total_opportunity_score", y="pain_category", orientation="h",
        text="total_opportunity_score", title="商业机会分数排行",
        labels={"total_opportunity_score": "总商业机会分数", "pain_category": "痛点分类"},
    )
    score_chart.update_layout(height=430, margin=dict(l=0, r=10, t=45, b=0))
    chart_columns = st.columns(2)
    chart_columns[0].plotly_chart(distribution_chart, width="stretch")
    chart_columns[1].plotly_chart(score_chart, width="stretch")

    components = display_opportunities.head(5)[[
        "pain_category", "frequency_score", "emotion_score", "payment_potential_score",
        "ai_automation_fit_score", "content_value_score",
    ]].melt(id_vars="pain_category", var_name="score_component", value_name="score")
    component_names = {
        "frequency_score": "频率", "emotion_score": "情绪", "payment_potential_score": "付费潜力",
        "ai_automation_fit_score": "AI 自动化适配度", "content_value_score": "内容价值",
    }
    components["score_component"] = components["score_component"].map(component_names)
    component_chart = px.bar(
        components, x="pain_category", y="score", color="score_component", barmode="group",
        title="Top 5 评分构成",
        labels={"pain_category": "痛点分类", "score": "分数", "score_component": "评分维度"},
    )
    component_chart.update_layout(height=500, margin=dict(l=0, r=10, t=45, b=0))
    st.plotly_chart(component_chart, width="stretch")

st.header("5. Top 5 商业机会（Top 5 Opportunities）")
if opportunities.empty:
    st.info("当前没有可展示的商业机会。")
else:
    for rank, (_, opportunity) in enumerate(opportunities.head(5).iterrows(), start=1):
        category_name = get_category_display_name(opportunity["pain_category"])
        with st.expander(f"#{rank}｜{category_name}｜{opportunity['total_opportunity_score']:.1f}/100", expanded=rank == 1):
            card_metrics = st.columns(3)
            card_metrics[0].metric("机会等级", opportunity["opportunity_level"])
            card_metrics[1].metric("市场信号强度", opportunity["market_signal_strength"])
            card_metrics[2].metric("用户紧迫度", opportunity["user_urgency"])
            st.markdown(f"**为什么这是一个机会：** {opportunity['why_it_matters']}")
            st.markdown(f"**变现角度：** {opportunity['monetization_angle']}")
            st.markdown(f"**推荐行动：** {opportunity['recommended_action']}")
            st.markdown("**证据评论：**")
            for comment in opportunity["top_example_comments"]:
                st.markdown(f"- {comment}")

st.header("6. 商业解读增强（Business Interpretation）")
if opportunities.empty:
    st.info("当前没有可展示的商业解读。")
else:
    for _, opportunity in opportunities.head(5).iterrows():
        with st.expander(get_category_display_name(opportunity["pain_category"])):
            st.markdown(f"**用户真实痛点：** {opportunity['real_user_pain']}")
            st.markdown(f"**适用场景：** {opportunity['target_scenario']}")
            st.markdown(f"**作品集展示价值：** {opportunity['portfolio_value']}")
            st.markdown(f"**内容方向：** {opportunity['content_direction']}")
            st.markdown(f"**验证建议：** {opportunity['validation_suggestion']}")

st.header("7. 产品视角建议（Founder / Product Lens）")
product_lens = generate_product_lens(opportunities, ideas)
if product_lens.empty:
    st.info("当前没有可生成的产品视角建议。")
else:
    for _, product in product_lens.iterrows():
        with st.expander(get_category_display_name(product["pain_category"])):
            st.markdown(f"**MVP idea：** {product['mvp_idea']}")
            st.markdown(f"**首轮用户测试方法：** {product['first_user_test_method']}")
            st.markdown(f"**下一步需要收集的数据：** {product['data_to_collect_next']}")
            st.markdown(f"**风险或限制：** {product['risk_or_limitation']}")
            st.markdown(f"**建议下一步：** {product['suggested_next_step']}")

st.header("8. AI Agent / AI Skill 建议")
if ideas.empty:
    st.info("识别到痛点类别后，这里将显示相应建议。")
else:
    for _, idea in ideas.iterrows():
        category_name = get_category_display_name(idea["pain_category"])
        with st.expander(f"{category_name}｜{idea['ai_agent_idea']}"):
            st.markdown(f"**AI Agent 想法：** {idea['ai_agent_idea']}")
            st.markdown(f"**AI Skill 想法：** {idea['ai_skill_idea']}")
            st.markdown(f"**自动化工作流建议：** {idea['automation_workflow_idea']}")
            st.markdown(f"**短视频选题：** {idea['short_video_topic']}")
            st.markdown(f"**小红书 / 抖音角度：** {idea['xiaohongshu_douyin_angle']}")
            st.markdown(f"**可付费服务方向：** {idea['paid_service_idea']}")
            st.markdown(f"**目标用户群体：** {idea['target_user_group']}")
            st.markdown(f"**推荐下一步：** {idea['recommended_next_action']}")

st.header("9. 导出分析结果（Export Results）")
st.info("Markdown 适合继续编辑，HTML 适合打开查看和展示，CSV 适合二次分析。")
export_data = exportable_analysis(analyzed)
generated_at = datetime.now().astimezone()
markdown_report = build_markdown_report(
    analyzed, opportunities, ideas, total_comments=len(raw_data), generated_at=generated_at
)
html_report = build_html_report(
    analyzed, opportunities, ideas, total_comments=len(raw_data), generated_at=generated_at
)
csv_filename = build_export_filename("social_pain_analysis", "csv", generated_at)
markdown_filename = build_export_filename("social_pain_report", "md", generated_at)
html_filename = build_export_filename("social_pain_report", "html", generated_at)
download_columns = st.columns(3)
download_columns[0].download_button(
    "下载分析明细 CSV", export_data.to_csv(index=False).encode("utf-8-sig"),
    file_name=csv_filename, mime="text/csv", type="primary",
)
download_columns[1].download_button(
    "下载 Markdown 报告", markdown_report.encode("utf-8"),
    file_name=markdown_filename, mime="text/markdown",
)
download_columns[2].download_button(
    "下载 HTML 报告", html_report.encode("utf-8"),
    file_name=html_filename, mime="text/html",
)
if st.button("保存报告到 outputs 文件夹"):
    try:
        output_dir = ROOT / "outputs"
        saved_paths = [
            save_text_report(markdown_report, output_dir, markdown_filename),
            save_text_report(html_report, output_dir, html_filename),
            save_analysis_csv(export_data, output_dir, csv_filename),
        ]
        st.success("报告已保存到本地：\n\n" + "\n\n".join(str(path) for path in saved_paths))
    except Exception as exc:
        st.error(f"保存报告失败：{exc}")

st.header("10. 报告预览（Report Preview）")
with st.expander("展开查看 Markdown 报告", expanded=False):
    st.markdown(markdown_report)

st.header("11. 隐私、限制与免责声明")
st.warning("请仅分析你有权使用的数据，并在导入前删除个人隐私、敏感信息和真实客户身份信息。")
st.markdown(
    "本工具不包含爬虫，不上传云端，不需要 API Key。当前分析依赖本地关键词和规则，"
    "适合作为需求初筛与商业假设工具，不应作为最终法律、财务或市场判断。重要结论需要人工检查和真实用户验证。"
)

