# Duffy V2 Regression Fixture

Purpose: keep the Duffy 10-year friendship V2 manual fix as a reusable regression shape without copying or modifying the client project.

Rules captured by the regression:

- A customer proposal is not a production table and not a short pitch.
- Detailed customer decks may be 22-45+ pages when the story needs that space.
- Every page must remain low-density, customer-readable, and decision-oriented.
- Before PPT builder, `client_outline.csv` must include page title, narrative body, client confirmation point, material role, visual slot, and visual asset status.
- Visual status must distinguish existing image, placeholder, pending generation, text-only, or no-visual pages.
- Asset intake must first search local files, Grok, ChatGPT projects, ImageGen, downloads, and original pools before replacement generation.
- Every candidate asset needs source, platform, conversation, local file, hash, original/processed status, direct client use, used slide, and QA flags.
- Visual layout review must catch distortion, crop, small image, crowded layout, nested cards, report-like pages, short copy, image/copy mismatch, repeated-image misuse, and portrait/landscape mismatch.

Executable coverage lives in the goal-workflow regression suite:

- `test_duffy_v2_regression_allows_long_low_density_client_outline`
- `test_browser_asset_current_manifest_records_platform_conversation_and_qa_flags`

Non-goal: this fixture does not approve creative quality, visual taste, licensing, or client send readiness.
