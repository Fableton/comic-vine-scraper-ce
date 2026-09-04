# Roadmap

## Known pending items

- [x] **Go back to the previous comic from the series-selection window**:
  the "Previous Comic" button now exists in both the issue-selection
  window (`issueform.py`) and the series-selection window
  (`seriesform.py`). Done, see CHANGELOG.md [1.1.0-ce].

- [ ] **Ignore Publishers from the options**: add the ability to mark
  Publishers to ignore to the scraper's configuration
  (`configform.py` / `configuration.py`), making it easier to exclude
  publishers known to have no comics in the library. Includes:
  - Cache a list of Publishers on disk (to populate the selector of
    which ones to ignore) -- avoid re-requesting it from the API every
    time.
  - In the series list (wherever a result's Publisher is shown),
    automatically filter/hide series whose Publisher is on the ignore
    list.
  - Add a right-click context menu on a series/result in that list with
    an **"Ignore Publisher"** option, adding that Publisher to the
    ignore-list configuration directly from there.
