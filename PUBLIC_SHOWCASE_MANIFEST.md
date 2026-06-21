# Public Showcase Manifest

## Project

**Name:** SocialPainFinderAgent  
**Display name:** 社交媒体痛点与商业机会挖掘 Agent  
**Release scope:** Local-first public portfolio showcase

## Public showcase scope

This repository demonstrates a Python and Streamlit workflow for analyzing user-provided text with local, rule-based logic. The public version is intended to show data ingestion, cleaning, bilingual pain detection, transparent scoring, business interpretation, AI Agent ideation, visualization, testing, and local report export.

It does not include production customer data, private integrations, credentials, automated data collection, or cloud infrastructure.

## Files safe to include

- Application source code in `app.py` and `modules/`
- Automated tests in `tests/`
- Synthetic demonstration data in `data/sample_comments.csv`
- Public documentation in `README.md` and `docs/`
- Dependency list in `requirements.txt`
- `.gitignore`
- Empty directory placeholders:
  - `outputs/.gitkeep`
  - `docs/screenshots/.gitkeep`

## Files and data that must remain excluded

- Real customer comments, reviews, support conversations, or exports
- Personal names, email addresses, phone numbers, account IDs, or addresses
- Confidential company, course, creator, or client data
- API keys, access tokens, passwords, secrets, certificates, or session cookies
- `.env` files
- Generated CSV, Markdown, or HTML reports in `outputs/`
- Files in `private_data/`
- Local virtual environments, caches, logs, backups, and archives
- Screenshots that expose private data or local user information

## Data statement

The bundled `data/sample_comments.csv` is synthetic and created for testing and demonstration. It contains no known real customer records. Public screenshots should use this dataset only.

## Design statement

- Local-first processing
- Rule-based and explainable MVP logic
- No web scraper
- No unofficial social media crawling
- No cloud database
- No API key required
- No automatic local writes; output files are saved only after a user action

## Safety checklist before publishing

- [ ] Run `python -m pytest tests -v`.
- [ ] Start the app and confirm the synthetic sample workflow works.
- [ ] Review `git status` and every staged file.
- [ ] Confirm only synthetic data is present under `data/`.
- [ ] Confirm `outputs/` contains no tracked generated reports.
- [ ] Confirm `private_data/`, `.env`, logs, archives, and backups are not staged.
- [ ] Scan for API keys, tokens, passwords, secrets, emails, and phone numbers.
- [ ] Inspect screenshots at full resolution for private text and local identifiers.
- [ ] Confirm documentation does not claim that heuristic scores are validated market demand.
- [ ] Confirm dependencies are limited to the packages in `requirements.txt`.

## GitHub release readiness

- [x] Portfolio-ready README
- [x] Architecture and project-overview documentation
- [x] Privacy and compliance documentation
- [x] Roadmap and changelog
- [x] Screenshot guide and placeholder folder
- [x] Synthetic sample dataset
- [x] Automated tests
- [x] Generated-output exclusions
- [x] Local-first and no-scraping statements
- [x] No required secrets or API credentials

The repository is ready for a public showcase after the publisher completes the unchecked pre-publish review items for the exact files being committed.

