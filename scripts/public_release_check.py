"""Run lightweight, dependency-free checks before a public GitHub release."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SCREENSHOTS = (
    "docs/screenshots/01_home_hero.png",
    "docs/screenshots/02_core_metrics_and_pain_categories.png",
    "docs/screenshots/03_opportunity_scoring.png",
    "docs/screenshots/04_score_components_chart.png",
    "docs/screenshots/05_top_5_opportunities.png",
    "docs/screenshots/06_export_and_report_preview.png",
    "docs/screenshots/07_html_report.png",
)
REQUIRED_FILES = (
    "app.py",
    "README.md",
    "requirements.txt",
    "data/sample_comments.csv",
    "docs/SCREENSHOTS_GUIDE.md",
    "docs/FINAL_RELEASE_CHECKLIST.md",
    "PUBLIC_SHOWCASE_MANIFEST.md",
    "outputs/.gitkeep",
)
EXPECTED_REQUIREMENTS = ["streamlit", "pandas", "openpyxl", "plotly", "pytest"]
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def main() -> int:
    """Print a readable release summary and fail only on blocking issues."""
    failures: list[str] = []
    warnings: list[str] = []

    for relative_path in REQUIRED_FILES:
        if not (ROOT / relative_path).is_file():
            failures.append(f"Missing required file: {relative_path}")

    requirements_path = ROOT / "requirements.txt"
    if requirements_path.is_file():
        requirements = [
            line.strip()
            for line in requirements_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        if requirements != EXPECTED_REQUIREMENTS:
            failures.append(
                "requirements.txt should contain only: " + ", ".join(EXPECTED_REQUIREMENTS)
            )

    readme = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").is_file() else ""
    found_screenshots = 0
    for relative_path in EXPECTED_SCREENSHOTS:
        screenshot = ROOT / relative_path
        if not screenshot.is_file():
            warnings.append(f"Missing screenshot: {relative_path}")
            continue
        found_screenshots += 1
        if screenshot.stat().st_size <= len(PNG_SIGNATURE):
            warnings.append(f"Screenshot is empty or too small: {relative_path}")
        elif screenshot.read_bytes()[: len(PNG_SIGNATURE)] != PNG_SIGNATURE:
            warnings.append(f"Screenshot is not a valid PNG file: {relative_path}")
        if relative_path not in readme:
            failures.append(f"README does not reference screenshot: {relative_path}")

    output_files = [
        path for path in (ROOT / "outputs").glob("*")
        if path.is_file() and path.name != ".gitkeep"
    ]
    if output_files:
        warnings.append(
            f"outputs/ contains {len(output_files)} generated file(s); confirm they remain untracked."
        )

    for private_path in (".env", "private_data"):
        if (ROOT / private_path).exists():
            failures.append(f"Private path exists in project root: {private_path}")

    print("SocialPainFinderAgent public release check")
    print(f"[PASS] Required project files checked: {len(REQUIRED_FILES)}")
    print(f"[PASS] Screenshot files found: {found_screenshots}/{len(EXPECTED_SCREENSHOTS)}")
    if requirements_path.is_file() and not any("requirements.txt" in item for item in failures):
        print("[PASS] requirements.txt contains only approved dependencies")

    for warning in warnings:
        print(f"[WARNING] {warning}")
    for failure in failures:
        print(f"[FAIL] {failure}")

    if failures:
        print(f"Result: FAIL ({len(failures)} blocking issue(s), {len(warnings)} warning(s))")
        return 1
    print(f"Result: PASS ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())

