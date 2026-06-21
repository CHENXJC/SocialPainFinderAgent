# Privacy and Compliance

## Public project policy

SocialPainFinderAgent is designed as a local-first research and portfolio application. The public repository must contain only source code, documentation, synthetic sample data, tests, and empty placeholder directories.

## No-scraping policy

- The project does not include a web scraper.
- The project does not use unofficial social media crawling.
- The project does not bypass platform access controls or collect data automatically.
- Data collection is outside the application's scope.

## User-provided data only

The application analyzes only files a user uploads or text a user pastes manually. Users are responsible for confirming that they are authorized to use the data and that their analysis follows applicable laws, contracts, platform terms, and organizational policies.

## Synthetic sample data

`data/sample_comments.csv` contains synthetic comments created for demonstration and testing. It must not be replaced with real customer exports in the public repository.

## No secrets or cloud storage

- No API keys are required.
- No tokens or passwords should be stored in the repository.
- No cloud database is used.
- No external AI service is called.
- The `.env` file is ignored if a developer creates one locally in the future.

## Personal-data commitment

The public project must not include names of real customers, email addresses, phone numbers, account identifiers, private conversations, confidential business records, or generated reports based on real data.

## Before uploading a file

Users should:

1. Confirm they have permission to analyze the data.
2. Remove names, contact details, IDs, addresses, payment information, and sensitive attributes.
3. Replace real identities with neutral synthetic labels when examples are needed.
4. Avoid uploading secrets, credentials, internal URLs, or confidential documents.
5. Review downloaded reports before sharing them.
6. Delete local output files when they are no longer needed.

## Local outputs

Reports are generated in memory for download. The application writes Markdown, HTML, and CSV files to `outputs/` only after the user clicks the save button. Generated output files are ignored by Git, while `outputs/.gitkeep` preserves the empty folder structure.

## Public GitHub safety principles

- Commit synthetic demonstration data only.
- Keep generated reports and private datasets out of version control.
- Run a secret and personal-data scan before each public release.
- Inspect staged files before pushing.
- Treat screenshots as data: use only synthetic sample results and check the browser for visible local paths or private filenames.
- Document analytical limitations clearly.

## Disclaimer

This document describes project safeguards but is not legal advice or a formal privacy assessment. Users should obtain appropriate professional review for regulated, sensitive, or high-risk use cases.

