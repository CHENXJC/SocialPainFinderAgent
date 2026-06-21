# Final Release Checklist

Use this checklist immediately before publishing or updating the public GitHub repository.

## Application quality

- [ ] `python -m pytest tests -v` passes.
- [ ] `streamlit run app.py` starts successfully.
- [ ] The sample-data workflow completes without errors.
- [ ] CSV, Markdown, and HTML downloads work.
- [ ] Local outputs are written only after clicking the save button.

## Seven public screenshots

All screenshots must use the bundled synthetic sample data and contain no private information.

- [ ] `docs/screenshots/01_home_hero.png`
- [ ] `docs/screenshots/02_core_metrics_and_pain_categories.png`
- [ ] `docs/screenshots/03_opportunity_scoring.png`
- [ ] `docs/screenshots/04_score_components_chart.png`
- [ ] `docs/screenshots/05_top_5_opportunities.png`
- [ ] `docs/screenshots/06_export_and_report_preview.png`
- [ ] `docs/screenshots/07_html_report.png`

For each image, verify that no real customer data, private filename, email address, phone number, credential, local username, or confidential text is visible.

## Repository safety

- [ ] `python scripts/public_release_check.py` completes without failures.
- [ ] `outputs/` contains no generated reports intended for publication.
- [ ] `private_data/`, `.env`, logs, backups, and archives are not staged.
- [ ] `data/sample_comments.csv` remains synthetic.
- [ ] No API keys, access tokens, passwords, or secrets are present.
- [ ] Every staged file has been reviewed before push.

## Documentation

- [ ] README screenshot paths render correctly on GitHub.
- [ ] The README run and test commands are current.
- [ ] Privacy, limitations, and disclaimer text remain visible.
- [ ] Roadmap and changelog reflect the released version.

Missing screenshots are reported as warnings by the release script so development snapshots can still run the check. A public showcase release should include all seven images.

