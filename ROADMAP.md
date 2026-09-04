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
