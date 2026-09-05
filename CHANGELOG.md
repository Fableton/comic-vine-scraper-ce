# Changelog

Functional summary of the changes in this fork (comic-vine-scraper-ce),
starting from where it diverges from upstream
[cbanack/comic-vine-scraper](https://github.com/cbanack/comic-vine-scraper)
v1.0.102.

## [1.1.0-ce] - Unreleased

- Added a "Previous Comic" button to the series-selection window,
  matching the one already in the issue-selection window, so you can go
  back and redo the previous comic if you picked the wrong series for it.
- Fixed the generic error dialog not showing up when an unexpected,
  non-database error happened while scraping or opening the
  configuration -- it used to fail silently, without telling the user.
- Fixed the "Configure..." toolbar button doing nothing: ComicRack was
  mistakenly loading an unbuilt copy of the script (from the source
  submodule); now only the real, packaged copy gets loaded.
- Added a `ROADMAP.md` to track this fork's known pending features.
- Added a "Publishers" tab to the configuration dialog to build a list
  of publishers to ignore: pick or type a name into a combobox (which
  fills in on its own from publishers you've already come across while
  scraping, without any extra download), add it with a button, and
  remove entries from a table. The series-selection window now filters
  those publishers out of its results automatically, and its right-click
  menu also offers to ignore a publisher on the spot -- either for good,
  or just for the current batch of comics you're scraping.
- Unified the look of every dialog in this plugin: consistent button and
  row heights, every window is now resizable (with a sensible minimum
  size, so it can't be shrunk into something unusable) and remembers the
  size you leave it at (before, only the main scraping-progress window
  did), and every window that still used a fixed, non-resizable layout
  (the scraping-progress, "finished scraping", and search-progress
  windows) now uses the same responsive layout as the rest.
- Added an "Appearance" tab to the configuration dialog with a slider to
  scale the size of buttons, rows, and text across every window in this
  plugin at once (75%-150%), with a live preview as you drag it.
- Fixed a crash while scraping ("'TableLayoutPanel' object has no
  attribute '_can_change_page'") that could happen when the
  scraping-progress window tried to redraw its cover image's
  page-turning arrows.
- Gave the advanced settings (previously only editable as raw text on
  the "Advanced" tab) their own dedicated controls, across three new/
  reorganized tabs: "Search Filters" (ignored search terms, year range,
  never-ignore threshold, max search results), "Publisher Aliases", and
  a rebuilt "Advanced" tab (the remaining behavior checkboxes, scrape
  delay, alternate filename regex, and imprint mappings) -- each with an
  "(i)" button explaining what its settings do. The raw text box is
  still available on a new "Manual" tab, now locked behind an "Enable
  manual editing" checkbox to prevent accidental edits.
- Added a "Don't show this dialog again" checkbox to the Welcome dialog,
  with a note that it can be turned back on from Settings > Advanced.
- Added an optional year-range override (checkbox + year field, for
  "ignore series before/after year") to the "Search for a Comic Book"
  dialog, so you can narrow a single search without changing your
  permanent Search Filters default -- the override only applies to that
  one search and is never saved to disk.

## [1.0.102-ce2] - 2026-09-01

- Restored visual customizations (responsive TableLayoutPanel layouts)
  in several windows that had been lost when the submodule was created.
- Added a "Search" button next to the issue-number preview field, and
  improved the spacing between the filters and the tables in the
  series/issue selection windows.
- Automated building releases (GitHub Actions) on tag push, without
  needing Ant/ipy.exe installed locally.

## [1.0.102-ce1] - 2026-09-01

- Added search and filters (by Series/Year/Issues/Publisher) with
  multi-column sorting to the series-selection table, and matching
  filters (with Year/Month columns) to the issue-selection table.
- Adjusted the static layout of the series and issue selection forms so
  they're responsive and adapt to larger resolutions (they used to have
  fixed size/position).
- Added an editable field to force the issue number to search for, a
  combobox that remembers the last 20 searches, a 24h disk cache for a
  series' issue list, and a "Previous Comic" button in the
  issue-selection window.
- Fixed Ctrl+Backspace in the new filter/combobox fields.
- Documented this fork's changes in the README, and added a PowerShell
  build script that doesn't depend on Ant/ipy.exe.
