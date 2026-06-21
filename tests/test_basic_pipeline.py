"""End-to-end tests for the SPF-001 local pipeline."""

from datetime import datetime
from pathlib import Path

import pandas as pd

from modules.data_loader import load_path
from modules.idea_generator import generate_ideas
from modules.pain_detector import detect_pain_categories
from modules.report_builder import (
    analyze_comments,
    build_export_filename,
    build_html_report,
    build_markdown_report,
    exportable_analysis,
    generate_markdown_report,
    generate_product_lens,
    save_analysis_csv,
    save_text_report,
)
from modules.scoring import build_opportunity_scores, get_top_opportunities
from modules.text_cleaner import clean_comments


ROOT = Path(__file__).parents[1]


def test_sample_data_can_be_loaded() -> None:
    data = load_path(ROOT / "data" / "sample_comments.csv")
    assert len(data) >= 40
    assert {"comment_id", "source", "text"}.issubset(data.columns)


def test_cleaning_removes_empty_and_duplicates() -> None:
    data = pd.DataFrame({
        "comment_id": [1, 2, 3, 4],
        "source": ["test"] * 4,
        "text": ["  Same comment  ", "Same   comment", "", None],
    })
    cleaned = clean_comments(data)
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["cleaned_text"] == "Same comment"
    assert "original_text" in cleaned.columns


def test_chinese_and_english_pain_detection() -> None:
    english = detect_pain_categories("This manual workflow takes too long to repeat every day.")
    chinese = detect_pain_categories("每天都要手动复制粘贴，希望可以自动化。")
    assert "Time cost pain" in english
    assert "Repeated manual work" in chinese
    assert "Need for automation" in chinese


def test_scoring_ideas_and_report_are_generated() -> None:
    raw = load_path(ROOT / "data" / "sample_comments.csv")
    analyzed, opportunities, ideas = analyze_comments(raw)
    assert analyzed["emotion_intensity_score"].between(0, 5).all()
    assert not opportunities.empty
    score_columns = {
        "frequency_score",
        "emotion_score",
        "payment_potential_score",
        "ai_automation_fit_score",
        "content_value_score",
        "total_opportunity_score",
    }
    assert score_columns.issubset(opportunities.columns)
    assert opportunities[list(score_columns)].apply(lambda column: column.between(0, 100).all()).all()
    assert {
        "opportunity_level",
        "recommended_action",
        "comment_count",
        "percentage_of_total_comments",
        "average_emotion_intensity",
        "top_example_comments",
        "why_it_matters",
        "business_interpretation",
    }.issubset(opportunities.columns)
    assert opportunities["total_opportunity_score"].is_monotonic_decreasing
    assert opportunities["top_example_comments"].map(lambda comments: len(comments) <= 3).all()
    interpretation_fields = {
        "market_signal_strength",
        "user_urgency",
        "monetization_angle",
        "target_scenario",
        "portfolio_value",
        "real_user_pain",
        "ai_solution_direction",
        "content_direction",
        "validation_suggestion",
    }
    assert interpretation_fields.issubset(opportunities.columns)
    assert opportunities["market_signal_strength"].isin({"强", "中", "弱"}).all()
    assert opportunities["user_urgency"].isin({"高", "中", "低"}).all()
    assert opportunities[list(interpretation_fields - {"market_signal_strength", "user_urgency"})].notna().all().all()
    assert opportunities["pain_category"].notna().all()
    assert opportunities["pain_category"].str.strip().ne("").all()

    top_opportunities = get_top_opportunities(opportunities, limit=5)
    assert 0 < len(top_opportunities) <= 5
    assert top_opportunities["total_opportunity_score"].is_monotonic_decreasing

    assert not ideas.empty
    expected_idea_fields = {
        "pain_category",
        "ai_agent_idea",
        "ai_skill_idea",
        "automation_workflow_idea",
        "short_video_topic",
        "xiaohongshu_douyin_angle",
        "paid_service_idea",
        "target_user_group",
        "recommended_next_action",
    }
    assert expected_idea_fields.issubset(ideas.columns)
    assert ideas[list(expected_idea_fields - {"pain_category"})].notna().all().all()
    assert generate_ideas(build_opportunity_scores(analyzed)).shape[0] > 0
    report = generate_markdown_report(analyzed, opportunities, ideas)
    assert report.startswith("# Social Pain Finder Agent")
    assert "商业机会评分公式" in report
    assert "Top 5 商业机会" in report
    assert "商业解读增强" in report
    assert "产品视角建议" in report
    assert "风险与限制" in report
    assert "隐私与合规说明" in report

    product_lens = generate_product_lens(opportunities, ideas)
    assert 0 < len(product_lens) <= 3
    assert {
        "pain_category",
        "mvp_idea",
        "first_user_test_method",
        "data_to_collect_next",
        "risk_or_limitation",
        "suggested_next_step",
    }.issubset(product_lens.columns)
    assert product_lens.drop(columns="pain_category").notna().all().all()


def test_keyword_signals_influence_business_scores() -> None:
    raw = pd.DataFrame({
        "comment_id": [1, 2],
        "source": ["test", "test"],
        "text": [
            "Urgent customer report is expensive; I manually copy and summarize it every day.",
            "每天手动整理客户报告，成本太高，希望自动化并做成教程。",
        ],
    })
    _, opportunities, _ = analyze_comments(raw)
    repeated = opportunities.loc[
        opportunities["pain_category"] == "Repeated manual work"
    ].iloc[0]
    assert repeated["payment_potential_score"] > 0
    assert repeated["ai_automation_fit_score"] > 0
    assert repeated["content_value_score"] > 0


def test_report_exports_and_local_saving(tmp_path: Path) -> None:
    raw = load_path(ROOT / "data" / "sample_comments.csv")
    analyzed, opportunities, ideas = analyze_comments(raw)
    generated_at = datetime(2026, 6, 21, 15, 30, 0)

    markdown = build_markdown_report(
        analyzed, opportunities, ideas, total_comments=len(raw), generated_at=generated_at
    )
    html = build_html_report(
        analyzed, opportunities, ideas, total_comments=len(raw), generated_at=generated_at
    )
    assert "Top 5 商业机会" in markdown
    assert "生成时间" in markdown
    assert "产品视角建议" in markdown
    assert '<meta charset="UTF-8">' in html
    assert "Top 5 商业机会" in html
    assert "隐私与合规说明" in html
    assert "<table>" in html

    markdown_name = build_export_filename("social_pain_report", "md", generated_at)
    html_name = build_export_filename("social_pain_report", ".html", generated_at)
    csv_name = build_export_filename("social_pain_analysis", "csv", generated_at)
    assert markdown_name == "social_pain_report_20260621_153000.md"
    assert html_name.endswith("_20260621_153000.html")
    assert csv_name.endswith("_20260621_153000.csv")

    markdown_path = save_text_report(markdown, tmp_path, markdown_name)
    html_path = save_text_report(html, tmp_path, html_name)
    csv_path = save_analysis_csv(exportable_analysis(analyzed), tmp_path, csv_name)
    assert markdown_path.read_text(encoding="utf-8") == markdown
    assert html_path.read_text(encoding="utf-8") == html
    assert csv_path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded_csv = pd.read_csv(csv_path, encoding="utf-8-sig")
    assert len(loaded_csv) == len(analyzed)
