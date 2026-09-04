# Changelog

All notable changes to this fork (comic-vine-scraper-ce) are documented
here, starting from where it diverged from upstream
[cbanack/comic-vine-scraper](https://github.com/cbanack/comic-vine-scraper)
at v1.0.102.

## [1.1.0-ce] - Unreleased

### Added
- "Previous Comic" button in the series picker (SeriesForm), matching the
  one already in the issue picker -- lets you go back and redo the
  immediately-previous book if you picked the wrong series for it.
- `ROADMAP.md` to track known pending features.

### Fixed
- `handle_error()` crashed with a secondary `AttributeError` whenever a
  non-`DatabaseConnectionError` exception occurred, silently swallowing
  the real error and the "unexpected error" dialog that should have shown
  it.
- ComicRack's "Configure..." toolbar button did nothing. The live
  `ComicRackFiles/Scripts` profile folder held this submodule's raw,
  unbuilt source tree, which ComicRack was also scanning and registering
  as a second (broken) copy of the plugin. Moved the submodule out of
  `ComicRackFiles/Scripts` in the main ComicRackCE repo so only the built
  plugin folder is ever loaded.

## [1.0.102-ce2] - 2026-09-01

### Added
- GitHub Actions workflow to auto-build releases (`.crplugin`) on `v*`
  tag push.

### Fixed
- Restored pre-existing customizations to `comicform.py`, `configform.py`,
  `finishform.py`, `log.py`, and `welcomeform.py` that were lost when this
  submodule was first created (only the files touched in that session had
  been carried over from the live plugin folder).

### Changed
- Added a "Search" button next to the issue-number preview field (Enter
  still worked, but it wasn't discoverable on its own).
- Added a gap between each table's filter row and the table itself in
  SeriesForm/IssueForm; they looked glued together before.

## [1.0.102-ce1] - 2026-09-01

### Added
- `build.ps1`: builds the `.crplugin` in plain PowerShell (flattens
  `src/`, substitutes the version placeholder, zips) -- no Ant/ipy.exe
  required.
- Series/issue picker UX improvements:
  - Filterable Series/Year/Issues/Publisher search panel, plus
    shift-click multi-column sorting, in the series picker.
  - Year/Month columns and a matching (debounced) filter panel in the
    issue picker.
  - Editable "issue number to preview" field under the series cover,
    which can override the auto-detected issue number.
  - Turned the search dialog's textbox into a combobox that remembers
    the last 20 search terms.
  - Cached a series' issue list to disk (24h TTL) so re-scraping many
    books from the same large series doesn't re-fetch it every time.
  - "Previous Comic" button in the issue picker, to go back and redo
    the immediately-previous book if it was scraped incorrectly.
  - Responsive, resizable layout for both picker dialogs.

### Fixed
- Ctrl+Backspace inserted a stray character instead of deleting the
  previous word in the new filter/combobox controls.

### Changed
- `HelpLink` now points at this fork, so installs are distinguishable
  from upstream's official release.
- Documented this fork's changes in the README.
