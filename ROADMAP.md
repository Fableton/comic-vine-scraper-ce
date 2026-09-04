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
