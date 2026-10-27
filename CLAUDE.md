# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

- `PRD.md` — product requirements for the **EU Steel Decarbonisation Policy Tracker**, a Korean-language Streamlit app that tracks EU climate policies affecting the steel industry. The **decisions appended below section 13 override the PRD body**.
- `PROMPTS.md` — the four-stage build plan (1: skeleton, 2: features + data research, 3: UI design, 4: Playwright QA). Work follows these stages in order.
- `eu-steel-policy-tracker/` — the app. Stages 1–3 are done (skeleton, features F1–F8, researched policy data for 26 policies, UI design). Stage 4 (Playwright QA) is done. The e2e suite in `tests/e2e/` has 113 tests and all pass; the results are in `eu-steel-policy-tracker/QA_REPORT.md`. Open items:
- Deployment: no environment has been chosen yet.
- Policy data: 24 of 26 policies are `verify_needed`, because nobody has checked them against EUR-Lex in a real browser.

## Decisions that override the PRD body

- **Internal use only.** Do not deploy to a public URL. Deploy as a private Streamlit Community Cloud app (viewer email allowlist) or as an internal Docker server. The disclaimer must say "사내용".
- **Weekly data updates.** A policy whose `last_verified` is more than **14 days** old gets the "재확인 필요" badge. This replaces the PRD's 90-day rule.
- **Korean steelmaker perspective is in scope.** Each policy has a `korea_note` field, and the impact matrix has a 한국 column next to 역내 (EU) and 역외 (non-EU).
- **No calculators.** Do not build CFP (carbon footprint) calculation, CBAM embedded-emissions calculation or certificate-cost calculation, including the CBAM calculator listed under the PRD's v2 milestone. The app covers policy trends only.

## Architecture

**Data**
- **Data is separate from code.** All policy content lives in `data/policies.yaml`, and the update history lives in `data/changelog.yaml`. Updating policies must never require code changes.
- **Overriding the data folder.** The environment variable `EU_POLICY_DATA_DIR` points the app at another data folder; e2e tests use it so they never touch `data/`.
- **Schema.** `src/models.py` holds the pydantic v2 schema. Unknown fields are rejected (`extra="forbid"`). The Korean UI labels for enum values (`STATUS_LABELS`, `CATEGORY_LABELS`, ...) also live there; add new enum values both there and in the matching `Literal`.
- **Fields beyond PRD §6:**
  - `korea_note` and `korea_level`, under `impact`. When `korea_level` is empty, the Korea impact level falls back to the non-EU level (`Impact.korea_effective_level`).
  - `effective_date`, `sub_acts`, `verify_needed` and `note`.
  - The category `climate_framework`.
- **Loading.** `src/loader.py` validates the YAML. An invalid entry produces a warning and is skipped, and a broken file is reported; neither crashes the app. Every page calls `load_data()` itself. The call is cached and keyed on the YAML files' modification times.
- **Derived values are computed, not stored.** Consultation status, D-day and staleness are calculated from today's date, in functions that take the date as an argument so they can be tested.
- **Status.** Each policy's `status` is `in_force` or `pending`, which drives the two-tab split. A `pending` policy also has a legislative `stage`.

**Pages and routing**
- **Pages live in `views/`, never `pages/`.** If a `pages/` folder exists, Streamlit also runs its legacy auto-discovery. A deep link such as `/dashboard` then executes the page file alone, without the sidebar filters.
- **The router is `src/navigation.py`.** `app.py` only calls `run_app()`. `PAGE_SPECS` defines each page's file, title and `url_path`: `dashboard`, `policies`, `detail`, `consultations`, `impact` and `changelog`. Page paths are absolute (`VIEWS_DIR`).
- **Links between pages** use `st.page_link(DETAIL_PAGE, query_params={"policy": id})`. The detail page follows `?policy=<id>`.
- **Sidebar filters** are widgets with `f_*` session-state keys. `render_sidebar()` draws them on every run, so their state survives page changes. Pages call `filtered_policies(result)`; the filter and sort logic is pure functions in `src/filters.py`. The "영향 대상" filter keeps a policy when its impact level for that target is medium or high.

**UI layers** — each concern has one home:
- Shared widgets: `src/components.py`.
- Plotly charts: `src/charts.py`. Every figure goes through `apply_layout()` and is rendered with `config=CHART_CONFIG`.
- Colors and icons: `src/theme.py`. Badges use the semantic maps `BADGE`/`LEVEL_BADGE`, never hard-coded color names. Charts use `CHART`/`LEVEL_HEX`.
- CSS: only `assets/style.css`, injected once by `inject_css()`. Keep its hex values in sync with `theme.py`.
- Theme: `.streamlit/config.toml` defines both `[theme.light]` and `[theme.dark]`, so the app follows the OS setting.

**Rendering rules**
- **Wrap data text rendered as markdown in `md()`.** This applies to `st.markdown`, `st.caption` and alerts. Policy text is full of ranges like `2031~2040`, which markdown would render as strikethrough.
- **Escape data text with `html.escape`** before putting it in `st.html` snippets.
- **Never render a lone `-` as a value under a bold label.** `"**label**  \n-"` becomes a setext heading, so use `—`.
- **Dates generated by the app are `YYYY-MM-DD`.** Dates inside free data text may use other formats.
- **Give a container a key when CSS or tests need to target it.** Its `.st-key-<key>` class is the hook: `kpis` gives the 2×2 KPI grid on mobile, and `card_<policy id>` marks a policy card.
- **No emoji in titles or navigation.** Use Material icons (`ICON` in `theme.py`).

## Commands (run from `eu-steel-policy-tracker/`)

```bash
pip install -r requirements-dev.txt                   # app + pytest-playwright
python -m playwright install chromium                 # once, for e2e
streamlit run app.py                                  # local dev (http://localhost:8501)
pytest                                                # unit + AppTest tests (e2e excluded by pytest.ini)
pytest tests/test_models.py::test_is_stale_boundary   # single test
pytest -m e2e tests/e2e                               # Playwright e2e (starts its own servers, ~10 min)
pytest -m e2e tests/e2e/test_behaviour.py -k b3       # subset of e2e
pytest -m "e2e and not network" tests/e2e             # e2e without the external link check
python scripts/check_links.py                         # link check; exit 1 if any link is broken
```

The link checker treats 202 (EUR-Lex bot challenge), 403, 429 and 5xx as warnings and does not fail on them.

## Testing

- **AppTest (`tests/test_app.py`).** It boots the real router with `AppTest.from_string("...run_app(default='<file>')")`. `AppTest.switch_page` does not work with the `views/` layout, and a view file run on its own breaks `st.page_link`. Inject filter values through `at.session_state["f_..."]`.
- **E2E (`tests/e2e/`).**
  - Server: `conftest.py` starts Streamlit on a free port. Set `E2E_BASE_URL` to reuse a running server instead.
  - Changed data: the `custom_server` fixture copies the data into a temp folder, mutates it and starts an extra server. Never edit `data/` from a test.
  - Waiting: after any interaction, call `settle()`, which waits until no element has `data-stale="true"`.
  - Card titles: read them with `visible_card_titles()`. Cards sit in two columns, so the DOM order is the left column, then the right column.
  - Dataframes are canvas-rendered and their text is not in the DOM. Read chart data from the Plotly element instead (`gd.data[0]`).
  - Output: screenshots go to `tests/e2e/screenshots/` and measurements to `tests/e2e/results/`.
- **Known benign console errors.** On a deep link to a sub-path, the Streamlit frontend first requests `<path>/_stcore/host-config` and `<path>/_stcore/health`, gets 404s, then retries at the root. `BENIGN_FAILED_REQUEST` in the e2e conftest allows only these two.
- **Do not loosen a test to make it pass.** Fix the app, or leave the test failing and record why in `QA_REPORT.md`.
- **Seed-data checks.** `tests/test_loader.py` checks that the 17 PRD seed policies still exist, that every `verify_needed` entry has a `note`, and that changelog ids exist.

## Working on Windows

- **Restart the server after editing anything in `src/`.** A running Streamlit server keeps old copies of `src/` modules, which produces errors such as `cannot import name ...`. Stopping only the process that listens on the port can leave other servers running, so kill every `streamlit run` process (`Get-CimInstance Win32_Process` filtered on the command line) and start one fresh server.
- **Set `PYTHONUTF8=1` before printing Korean or emoji.** The console uses cp949, and printing them otherwise raises `UnicodeEncodeError`. `scripts/check_links.py` reconfigures stdout itself.
- **Don't pipe Python containing backslash escapes through a Git Bash heredoc.** The heredoc collapsed `\\n` into `\n` in this session. Write such scripts with the Write tool instead.

## Data accuracy rules

- EU policy status changes quickly. Before you edit the policy data, verify facts against official sources: EUR-Lex, the Commission DG pages, Have Your Say and the European Parliament's OEIL.
- EUR-Lex blocks automated requests (202 bot challenge). Check legal texts in a real browser, and keep `verify_needed: true` until you have.
- Never invent dates, legal references or consultation details. Each `verify_needed` entry explains what is unconfirmed in its `note`.
- Whenever you change `policies.yaml`, record the change in `changelog.yaml` and set `last_verified`. Keep the source-URL comments above each entry.
- Prefer EUR-Lex ELI permalinks for legal texts.
