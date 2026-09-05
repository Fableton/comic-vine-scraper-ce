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

- [x] **Give the "Advanced" free-text settings their own UI, plus an
  explanation button**: all 14 settings now have dedicated controls across
  the "Search Filters", "Publisher Aliases", and rebuilt "Advanced" tabs
  in `ConfigForm`, each with an "(i)" info button; the raw free-text box
  moved to a new "Manual" tab, locked behind an "Enable manual editing"
  checkbox. Done, see CHANGELOG.md [1.1.0-ce].

- [ ] **Detect/flag collection-type entries (TPBs) in series search
  results**: check whether the Comic Vine API exposes a way to tell that
  a "series" result is actually a collected edition/compilation of
  another series (e.g. a trade paperback collecting several single
  issues, rather than an ongoing series in its own right), so the
  series-selection window could filter or visually flag those entries
  -- they currently show up mixed in with regular series with no way to
  tell them apart at a glance.

- [x] **Let the year range be overridden per-search, from the "Search for
  a Comic Book" dialog (`searchform.py`)**: `IGNORE_BEFORE_YEAR`/
  `IGNORE_AFTER_YEAR` can now be overridden with a checkbox + numeric field
  right in the search dialog, for that one search only (never persisted --
  same spirit as "Ignore Publisher for this session only"). Implemented via
  two new optional params on `ScrapeEngine.__query_series_refs`, so
  `self.config`'s values remain the fallback when left unchecked. Done, see
  CHANGELOG.md [1.1.0-ce].
