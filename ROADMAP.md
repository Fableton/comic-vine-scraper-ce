# Roadmap

## Known pending items

- [x] **Go back to the previous comic from the series-selection window**:
  the "Previous Comic" button now exists in both the issue-selection
  window (`issueform.py`) and the series-selection window
  (`seriesform.py`). Done, see CHANGELOG.md [1.1.0-ce].

- [x] **Ignore Publishers from the options**: a new ConfigForm "Publishers"
  tab lets you build an ignore list (editable combobox + "Add" button,
  table with a "Remove" button per row); the combobox is populated
  organically from publishers seen in past series searches, not a bulk
  Comic Vine API fetch. The series-selection window also filters out
  ignored publishers automatically, and its right-click menu offers
  "Ignore Publisher" (persistent) and "Ignore Publisher for this session
  only". Done, see CHANGELOG.md [1.1.0-ce].

- [ ] **Give the "Advanced" free-text settings their own UI, plus an
  explanation button**: `Configuration`'s advanced settings (parsed from
  a single free-text box on the "Advanced" tab -- see
  `__set_advanced_settings_s` in `configuration.py`) currently include
  `IGNORE_SEARCHTERM`, `IGNORE_BEFORE_YEAR`, `IGNORE_AFTER_YEAR`,
  `NEVER_IGNORE_THRESHOLD`, `SCRAPE_RATING`, `SHOW_COVERS`,
  `WELCOME_DIALOG`, `ALT_SEARCH_REGEX`, `IGNORE_FOLDERS`,
  `FORCE_SERIES_ART`, `NOTE_SCRAPE_DATE`, `PUBLISHER_ALIAS`, `IMPRINT`,
  `SCRAPE_DELAY`, and `MAX_SEARCH_RESULTS` -- none of them editable
  through a proper control (checkbox, textbox, etc), the same way
  `IGNORE_PUBLISHER` used to be before the Publishers tab. Review which
  of these are worth promoting to their own dedicated UI (checkboxes,
  textboxes, etc, likely on their own tab), and add an "i" (info) button
  on that tab that explains what each setting does -- they're currently
  undocumented in the UI itself, so most users (including the one who
  requested this) have no idea they exist or what they're for.

- [ ] **Detect/flag collection-type entries (TPBs) in series search
  results**: check whether the Comic Vine API exposes a way to tell that
  a "series" result is actually a collected edition/compilation of
  another series (e.g. a trade paperback collecting several single
  issues, rather than an ongoing series in its own right), so the
  series-selection window could filter or visually flag those entries
  -- they currently show up mixed in with regular series with no way to
  tell them apart at a glance.

- [ ] **Let the search-terms year range / never-ignore threshold / max
  results be overridden per-search, from the "Search for a Comic Book"
  dialog (`searchform.py`), instead of only as permanent global defaults
  in `ConfigForm`**: these settings (`IGNORE_BEFORE_YEAR`,
  `IGNORE_AFTER_YEAR`, `NEVER_IGNORE_THRESHOLD`, `MAX_SEARCH_RESULTS`) are
  often more useful tuned for one particular search than set-and-forgotten
  globally. The override should apply only to that one search/comic, and
  should NOT be persisted to disk (same spirit as the existing
  session-only "Ignore Publisher for this session only" option). Touch
  points found so far: `SearchForm`/`SearchFormResult`
  (`gui/forms/searchform.py`) would need new optional fields and to carry
  the override through its result; `ScrapeEngine.__query_series_refs`
  (`scrapeengine.py`, around lines 851-867) currently reads
  `self.config.ignored_before_year_n` / `ignored_after_year_n` /
  `never_ignore_threshold_n` / `ignored_searchterms_sl` directly and would
  need optional override parameters instead; `max_search_results_n` is
  currently applied only once, session-wide, via `db.initialize()`
  (`scrapeengine.py`, around lines 207-208) -- overriding it per-search
  would need a deeper look at `db.py`/`cvconnection.py` to see whether a
  per-call override is even plumbed through there. `scrapeengine.py`'s own
  comments mark its book-scraping loop "EXTREMELY SUBTLE", so this needs
  its own careful, dedicated pass rather than being bundled into an
  unrelated change.
