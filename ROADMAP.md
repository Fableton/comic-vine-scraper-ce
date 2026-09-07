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

- [x] **Detect/flag collection-type entries (TPBs) in series search
  results**: Comic Vine has no field that says this directly, so the
  series-selection window now tags a result as "Collection" (new "Type"
  column) using a best-effort keyword match (hardcover, omnibus, tpb,
  trade paperback, collected edition, collects issue(s)) against the
  series's name/deck text. Done, see CHANGELOG.md [Unreleased].

- [x] **Show a cover-match percentage in the issue-selection window**:
  compares the comic's own (local) first-page image against whichever
  Comic Vine cover is currently shown, using the existing perceptual-hash
  algorithm (`imagehash.py`) the auto-scraper already relies on
  internally. Done, see CHANGELOG.md [Unreleased].

- [x] **Semi-automatic accept/skip based on cover match**: an "Auto-accept"
  checkbox (with an editable match-percentage threshold, default 85%)
  below the cover match in the issue-selection window starts a 5-second
  countdown as soon as a cover's match is known, ending in an automatic
  OK (match met the threshold) or Skip (it didn't) unless cancelled --
  a middle ground between fully manual and fully automatic scraping.
  Done, see CHANGELOG.md [Unreleased].

- [x] **Dev-only grid debug overlay**: Ctrl+Shift+G in any window toggles
  an overlay tinting every TableLayoutPanel's cells by nesting depth, so
  nested grids are visually distinct (added to `CVForm`, so it applies
  everywhere automatically) -- meant purely to make layout discussions
  ("row 2, column 1") precise without guesswork; never shown to end
  users. Done, see CHANGELOG.md [Unreleased].

- [x] **Rebuild the issue/series cover panel's layout as an actual grid**:
  `IssueCoverPanel` (shared by the issue- and series-selection windows)
  used to position every control (cover, buttons, labels) by
  hand-computed pixel math on every resize. Replaced with a single
  `TableLayoutPanel` stacking the rows, with a small inner grid for any
  row that itself needs more than one column. The cover image now relies
  on `PictureBoxSizeMode.Zoom` to keep its aspect ratio instead of custom
  math. Done, see CHANGELOG.md [Unreleased].

- [x] **Show the cover-match percentage in the series-selection window
  too**: reuses the issue-selection window's existing match-percentage
  logic (local-hash comparison, background computation) -- just the
  status/percentage label, not (yet) the auto-accept checkbox. Done, see
  CHANGELOG.md [Unreleased].

- [x] **Extend auto-accept/skip to the series-selection window** (beta
  branch, not yet on master): shares the issue-selection window's
  checkbox/threshold; a candidate only counts once it resolves to a real
  issue, and it tries up to 4 candidates (current table sort order)
  before giving up and skipping. Done, see CHANGELOG.md
  `[Unreleased - beta, not yet on master]`.

- [ ] **Review the Comic Vine API documentation**
  (https://comicvine.gamespot.com/api/documentation) for anything new
  this fork could take advantage of -- it was last really gone over long
  ago (upstream itself hasn't changed since v1.0.102), so there may be
  new fields, resources, or endpoints worth using.

- [x] **Let the year range be overridden per-search, from the "Search for
  a Comic Book" dialog (`searchform.py`)**: `IGNORE_BEFORE_YEAR`/
  `IGNORE_AFTER_YEAR` can now be overridden with a checkbox + numeric field
  right in the search dialog, for that one search only (never persisted --
  same spirit as "Ignore Publisher for this session only"). Implemented via
  two new optional params on `ScrapeEngine.__query_series_refs`, so
  `self.config`'s values remain the fallback when left unchecked. Done, see
  CHANGELOG.md [1.1.0-ce].
