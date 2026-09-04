# -*- coding: utf-8 -*-
''' 
This module is home to the SeriesForm and SeriesFormResult classes.

@author: Cory Banack
'''
import log
import clr
from buttondgv import ButtonDataGridView
from cvform import CVForm
from System.Windows.Forms import FormBorderStyle, DockStyle
from utils import sstr, fix_ctrl_backspace
from matchscore import MatchScore
import i18n
import System
from issuecoverpanel import IssueCoverPanel
 
clr.AddReference('System')
from System.Collections import IComparer

clr.AddReference('System.Drawing')
from System.Drawing import Point, Size

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import AutoScaleMode, Button, \
   DataGridViewAutoSizeColumnMode, DataGridViewContentAlignment, \
   DataGridViewSelectionMode, DataGridViewTriState, DialogResult, \
   Keys, Label, FormBorderStyle , TableLayoutPanel, \
   DataGridViewColumnHeadersHeightSizeMode, TextBox, Panel, ToolTip, \
   DataGridViewColumnSortMode, SortOrder, MouseButtons, Timer

#==============================================================================
def _compare_cell_values(v1, v2):
   ''' Compares two DataGridView cell values, numerically if both are
   numbers, or as case-insensitive strings otherwise. None sorts first. '''
   if v1 is None and v2 is None: return 0
   if v1 is None: return -1
   if v2 is None: return 1
   if isinstance(v1, (int, long, float)) and isinstance(v2, (int, long, float)):
      return -1 if v1 < v2 else (1 if v1 > v2 else 0)
   s1 = sstr(v1).lower()
   s2 = sstr(v2).lower()
   return -1 if s1 < s2 else (1 if s1 > s2 else 0)

#==============================================================================
class _MultiColumnComparer(IComparer):
   '''
   An IComparer that sorts DataGridViewRows by an ordered list of
   (column_index, ascending_bool) sort keys -- the first key is primary,
   the rest are tie-breakers, in order.  Used to support shift-click
   multi-column sorting in SeriesForm's table.
   '''
   def __init__(self, sort_keys):
      self.__sort_keys = list(sort_keys)

   def Compare(self, x, y):
      for col_index, ascending in self.__sort_keys:
         c = _compare_cell_values(x.Cells[col_index].Value, y.Cells[col_index].Value)
         if c != 0:
            return c if ascending else -c
      return 0

#==============================================================================
class SeriesForm(CVForm):
   log.debug('Init SeriesForm')
   ''' Dialog to pick a comic series. '''

   def __init__(self, scraper, book, series_refs, search_terms_s,
         has_previous_b=False):
      self.__config = scraper.config
      self.__series_refs = list(series_refs)
      self.__matchscore = MatchScore()
      self.__pressing_controlkey = False
      self.__ok_button = None
      self.__skip_button = None
      self.__issues_button = None
      # whether the "Previous Comic" button should be enabled -- lets the
      # user go back and redo the immediately-previous comic book
      self.__has_previous_b = has_previous_b
      self.__table = None
      self.__coverpanel = None
      self.__chosen_index = None
      self.__filter_series = self.__filter_year = None
      self.__filter_issues = self.__filter_publisher = None
      # ordered list of (column_index, ascending_bool) sort keys; the first
      # is the primary key, the rest are tie-breakers, in order. shift-click
      # on a column header appends/toggles a tie-breaker key; a plain click
      # resets to a single-column sort. defaults to Match score, descending.
      self.__sort_keys = [(5, False)]
      # debounces filter textbox changes, so that filtering a table with
      # lots of rows doesn't re-run on every single keystroke
      self.__filter_debounce_timer = Timer()
      self.__filter_debounce_timer.Interval = 1000
      self.__filter_debounce_timer.Tick += self.__filter_debounce_tick
      self.__book = book
      if len(series_refs) <= 0:
         raise Exception("do not invoke the SeriesForm with no series!")
      CVForm.__init__(self, scraper.comicrack.MainWindow, "seriesformLocation")
      log.debug('SeriesForm: building GUI (series count=%d)' % len(self.__series_refs))
      self.__build_gui(book, search_terms_s)
      scraper.cancel_listeners.append(self.Close)

   #===========================================================================   
   def __build_gui(self, book, search_terms_s):
      self.__ok_button = self.__build_okbutton()
      self.__skip_button = self.__build_skipbutton()
      search_button = self.__build_searchbutton()
      self.__issues_button = self.__build_issuesbutton()
      previous_button = self.__build_previousbutton()
      label = self.__build_label(search_terms_s, len(self.__series_refs))
      self.__table = self.__build_table(self.__series_refs, book, self.__ok_button)
      self.__table_container = self.__build_filters_panel(self.__table)
      self.__coverpanel = self.__build_coverpanel(book)
      self.AutoScaleMode = AutoScaleMode.Font
      self.ClientSize = Size(1200, 700)
      self.Text = i18n.get("SeriesFormTitle")
      self.FormClosed += self.__form_closed_fired
      self.KeyPreview = True
      self.KeyDown += self.__key_was_pressed
      self.KeyUp += self.__key_was_released
      self.Deactivate += self.__was_deactivated
      self.FormBorderStyle = FormBorderStyle.Sizable
      table_layout = TableLayoutPanel(); table_layout.RowCount = 3; table_layout.ColumnCount = 6; table_layout.Dock = DockStyle.Fill
      table_layout.RowStyles.Add(System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 64))
      table_layout.RowStyles.Add(System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100))
      table_layout.RowStyles.Add(System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 64))
      for _ in range(5): table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 14.29))
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 28.57))
      self.Controls.Add(table_layout)
      table_layout.Controls.Add(label,0,0); table_layout.SetColumnSpan(label, 5)
      table_layout.Controls.Add(self.__table_container,0,1); table_layout.SetColumnSpan(self.__table_container, 5)
      table_layout.Controls.Add(self.__ok_button,0,2); table_layout.Controls.Add(self.__skip_button,1,2)
      table_layout.Controls.Add(previous_button,2,2)
      table_layout.Controls.Add(search_button,3,2); table_layout.Controls.Add(self.__issues_button,4,2)
      table_layout.Controls.Add(self.__coverpanel,5,0); table_layout.SetRowSpan(self.__coverpanel, 3)
      self.__ok_button.TabIndex = 1; self.__skip_button.TabIndex = 2; previous_button.TabIndex = 3
      search_button.TabIndex = 4; self.__issues_button.TabIndex = 5
      self.__coverpanel.TabIndex = 6; self.__table.TabIndex = 7
      self.Shown += self.__change_table_selection_fired
      # actualizar posicion filtros al mostrar
      self.Shown += self.__update_filter_positions
      log.debug('SeriesForm: GUI build complete')

   # ==========================================================================
   def __build_filters_panel(self, table):
      container = Panel(); container.Dock = DockStyle.Fill
      # extra height (vs. the 24px the textboxes need) leaves a gap below
      # them so the filter row doesn't look glued to the table underneath
      filter_panel = Panel(); filter_panel.Height = 38; filter_panel.Dock = DockStyle.Top; filter_panel.BackColor = table.BackColor
      # crear textboxes
      self.__filter_series = TextBox(); self.__filter_year = TextBox(); self.__filter_issues = TextBox(); self.__filter_publisher = TextBox()
      self.__filter_series.BorderStyle = self.__filter_year.BorderStyle = self.__filter_issues.BorderStyle = self.__filter_publisher.BorderStyle
      # tooltips
      tip = ToolTip()
      tip.SetToolTip(self.__filter_series, i18n.get("SeriesFormSeriesCol"))
      tip.SetToolTip(self.__filter_year, i18n.get("SeriesFormYearCol"))
      tip.SetToolTip(self.__filter_issues, i18n.get("SeriesFormIssuesCol"))
      tip.SetToolTip(self.__filter_publisher, i18n.get("SeriesFormPublisherCol"))
      # eventos de texto
      for tb in [self.__filter_series,self.__filter_year,self.__filter_issues,self.__filter_publisher]:
         tb.Top = 4
         tb.TextChanged += self.__filters_changed
         tb.Height = 20
         fix_ctrl_backspace(tb)
         filter_panel.Controls.Add(tb)
      table.Dock = DockStyle.Fill
      container.Controls.Add(table); container.Controls.Add(filter_panel)
      # guardar referencias para posicionamiento dinamico
      self.__filter_panel = filter_panel
      self.__filter_textboxes = [self.__filter_series,self.__filter_year,self.__filter_issues,self.__filter_publisher]
      # suscribir eventos para recalcular posicion
      table.ColumnWidthChanged += self.__update_filter_positions
      table.Scroll += self.__update_filter_positions
      table.ColumnDisplayIndexChanged += self.__update_filter_positions
      table.SizeChanged += self.__update_filter_positions
      table.Layout += self.__update_filter_positions
      table.HandleCreated += self.__update_filter_positions
      # intento de posicion inicial (si el handle ya existe)
      try:
         self.__update_filter_positions(table, None)
      except Exception:
         pass
      return container

   def __update_filter_positions(self, sender, args):
      try:
         if self.__table is None: return
         # obtener rectangulos de las primeras 4 columnas visibles (Series, Year, Issues, Publisher)
         target_cols = [0,1,2,3]
         for idx, col_index in enumerate(target_cols):
            if col_index >= self.__table.Columns.Count: continue
            col = self.__table.Columns[col_index]
            if not col.Visible: continue
            rect = self.__table.GetCellDisplayRectangle(col_index, -1, True)
            tb = self.__filter_textboxes[idx]
            tb.Left = rect.X + 2  # pequeño margen
            new_width = rect.Width - 4
            if new_width < 15: new_width = 15
            tb.Width = new_width
         # ocultar cualquier textbox sobrante si columna se oculta
         self.__filter_panel.Refresh()
      except Exception as e:
         log.debug('SeriesForm: update_filter_positions error %s' % e)

   # ==========================================================================
   def __add_row(self, table, ref, model_index):
      try:
         table.Rows.Add()
         row_idx = table.Rows.Count - 1
         r = table.Rows[row_idx]
         name_s = ref.series_name_s or ''
         year_s = sstr(ref.volume_year_n) if ref.volume_year_n >= 0 else ''
         r.Cells[0].Value = name_s
         if year_s: r.Cells[1].Value = year_s
         r.Cells[2].Value = ref.issue_count_n
         r.Cells[3].Value = ref.publisher_s or ''
         r.Cells[4].Value = ref.series_key
         try:
            r.Cells[5].Value = self.__matchscore.compute_n(self.__book, ref)
         except Exception as em:
            log.debug('SeriesForm: matchscore error %s' % em); r.Cells[5].Value = 0
         r.Cells[6].Value = model_index
      except Exception as e:
         log.debug('SeriesForm: __add_row failed model_index=%s error=%s' % (model_index, e))

   def __apply_filters(self):
      if self.__table is None:
         log.debug('SeriesForm: apply_filters skipped (table is None)')
         return
      fs = (self.__filter_series.Text or '').lower(); fy = (self.__filter_year.Text or '').lower()
      fi = (self.__filter_issues.Text or '').lower(); fp = (self.__filter_publisher.Text or '').lower()
      log.debug('SeriesForm: apply_filters start fs="%s" fy="%s" fi="%s" fp="%s"' % (fs,fy,fi,fp))
      self.__chosen_index = None
      try:
         self.__table.Rows.Clear()
      except Exception as e:
         log.debug('SeriesForm: clearing rows failed %s' % e)
      added = 0
      for i, ref in enumerate(self.__series_refs):
         try:
            name_s = ref.series_name_s or ''
            year_s = sstr(ref.volume_year_n) if ref.volume_year_n >= 0 else ''
            issues_s = sstr(ref.issue_count_n)
            pub_s = ref.publisher_s or ''
            if fs and fs not in name_s.lower(): continue
            if fy and fy not in year_s.lower(): continue
            if fi and fi not in issues_s.lower(): continue
            if fp and fp not in pub_s.lower(): continue
            self.__add_row(self.__table, ref, i); added += 1
         except Exception as er:
            log.debug('SeriesForm: filter loop error index=%d err=%s' % (i, er))
      log.debug('SeriesForm: apply_filters added=%d total=%d' % (added, len(self.__series_refs)))
      # re-apply whatever sort (single or multi-column) is currently active
      self.__apply_sort()

   def __filters_changed(self, sender, args):
      ''' Called whenever the text in any filter textbox changes. Debounced:
      (re)starts a 1-second timer instead of filtering right away, so that
      typing "33" doesn't filter for "3" and then "33" -- with lots of rows
      in the table, filtering on every keystroke makes typing feel laggy. '''
      try:
         self.__filter_debounce_timer.Stop()
         self.__filter_debounce_timer.Start()
      except Exception as e:
         log.debug('filter debounce error: ' + sstr(e))

   def __filter_debounce_tick(self, sender, args):
      ''' Called ~1 second after the user stops typing in a filter textbox.'''
      self.__filter_debounce_timer.Stop()
      try:
         self.__apply_filters()
      except Exception as e:
         log.debug('filter error (outer): ' + sstr(e))

   # ==========================================================================
   def __build_table(self, series_refs, book, enter_button):
      table = ButtonDataGridView(enter_button)
      self.__table = table
      table.AllowUserToOrderColumns = True
      table.SelectionMode = DataGridViewSelectionMode.FullRowSelect
      table.MultiSelect = False
      table.ReadOnly = True
      table.RowHeadersVisible = False
      table.AllowUserToAddRows = False
      table.AllowUserToResizeRows = False
      table.AllowUserToResizeColumns = False
      table.DefaultCellStyle.NullValue = "--"
      table.Dock = DockStyle.Fill
      table.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.EnableResizing
      if table.ColumnHeadersHeight < 38: table.ColumnHeadersHeight = 42
      table.ColumnCount = 7
      table.Columns[0].Name = i18n.get("SeriesFormSeriesCol"); table.Columns[0].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleLeft; table.Columns[0].Resizable = DataGridViewTriState.True; table.Columns[0].FillWeight = 200; table.Columns[0].AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill
      table.Columns[1].Name = i18n.get("SeriesFormYearCol"); table.Columns[1].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter; table.Columns[1].Resizable = DataGridViewTriState.True; table.Columns[1].AutoSizeMode = DataGridViewAutoSizeColumnMode.AllCells
      table.Columns[2].Name = i18n.get("SeriesFormIssuesCol"); table.Columns[2].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter; table.Columns[2].Resizable = DataGridViewTriState.True; table.Columns[2].AutoSizeMode = DataGridViewAutoSizeColumnMode.AllCells
      table.Columns[3].Name = i18n.get("SeriesFormPublisherCol"); table.Columns[3].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleLeft; table.Columns[3].Resizable = DataGridViewTriState.True; table.Columns[3].AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill
      table.Columns[4].Name = "ID"; table.Columns[4].Visible = False
      table.Columns[5].Name = "Match"; table.Columns[5].Visible = False
      table.Columns[6].Name = "Model ID"; table.Columns[6].Visible = False
      # sorting is handled by us (multi-column, via __header_mouse_clicked),
      # not by the DataGridView's own single-column automatic sort
      for col in table.Columns:
         col.SortMode = DataGridViewColumnSortMode.Programmatic
      table.ColumnHeaderMouseClick += self.__header_mouse_clicked
      for i, ref in enumerate(series_refs):
         self.__add_row(table, ref, i)
      table.SelectionChanged += self.__change_table_selection_fired
      self.__apply_sort()
      log.debug('SeriesForm: initial rows loaded=%d' % table.Rows.Count)
      return table

   # ==========================================================================
   def __header_mouse_clicked(self, sender, args):
      '''
      Called whenever the user clicks a column header. A plain click sorts
      by just that column (toggling direction if it's already the sole sort
      key). Shift-click adds/toggles that column as an extra tie-breaker
      key, on top of whatever the table is already sorted by, so the user
      can sort by two (or more) columns at the same time.
      '''
      try:
         if args.Button != MouseButtons.Left:
            return
         col_index = args.ColumnIndex
         if col_index < 0 or col_index >= self.__table.Columns.Count:
            return
         if not self.__table.Columns[col_index].Visible:
            return
         shift_held = (System.Windows.Forms.Control.ModifierKeys \
            & Keys.Shift) == Keys.Shift
         existing_i = None
         for i, (ci, asc) in enumerate(self.__sort_keys):
            if ci == col_index:
               existing_i = i
               break
         if shift_held:
            if existing_i is not None:
               ci, asc = self.__sort_keys[existing_i]
               self.__sort_keys[existing_i] = (ci, not asc)
            else:
               self.__sort_keys.append((col_index, True))
         else:
            if existing_i == 0 and len(self.__sort_keys) == 1:
               ci, asc = self.__sort_keys[0]
               self.__sort_keys = [(ci, not asc)]
            else:
               self.__sort_keys = [(col_index, True)]
         self.__apply_sort()
      except Exception as e:
         log.debug('SeriesForm: header click/sort error %s' % e)

   # ==========================================================================
   def __apply_sort(self):
      ''' Re-sorts the table's current rows according to self.__sort_keys,
      updates the column header sort-arrow glyphs to match, and re-selects
      the first row (mirroring the old single-column-sort behavior). '''
      try:
         if self.__table.Rows.Count > 0:
            self.__table.Sort(_MultiColumnComparer(self.__sort_keys))
      except Exception as e:
         log.debug('SeriesForm: sort error %s' % e)
      try:
         sort_order_none = getattr(SortOrder, 'None') # 'None' is a py keyword
         sorted_cols = dict(self.__sort_keys)
         for col in self.__table.Columns:
            if col.Index in sorted_cols:
               col.HeaderCell.SortGlyphDirection = SortOrder.Ascending \
                  if sorted_cols[col.Index] else SortOrder.Descending
            else:
               col.HeaderCell.SortGlyphDirection = sort_order_none
      except Exception as eg:
         log.debug('SeriesForm: sort glyph error %s' % eg)
      if self.__table.Rows.Count > 0:
         try:
            self.__table.CurrentCell = self.__table.Rows[0].Cells[0]
         except Exception as es:
            log.debug('SeriesForm: sort selection error %s' % es)
      if self.__coverpanel is not None:
         self.__change_table_selection_fired(None, None)

   # ==========================================================================
   def __build_okbutton(self):
      ''' builds and returns the ok button for this form '''
      
      button = Button()
      button.DialogResult = DialogResult.OK
      button.Location = Point(15, 362)
      button.Size = Size(90, 24)
      button.Text = i18n.get("SeriesFormOK")
      button.Dock = DockStyle.Fill
      return button
   
   
   # ==========================================================================
   def __build_skipbutton(self):
      ''' builds and return the skip button for this form '''
      
      button = Button()
      button.DialogResult = DialogResult.Ignore
      button.Location = Point(110, 362)
      button.Size = Size(90, 24)
      button.Text = i18n.get("SeriesFormSkip")
      button.Dock = DockStyle.Fill
      return button


   # ==========================================================================
   def __build_searchbutton(self):
      ''' builds and return the 'search again' button for this form '''
      
      button = Button()
      button.DialogResult = DialogResult.Retry
      button.Location = Point(275, 362) \
         if self.__config.show_covers_b else Point(485, 362) 
      button.Size = Size(115, 24)
      button.Text = i18n.get("SeriesFormAgain")
      button.Dock = DockStyle.Fill
      return button
   
   # ==========================================================================
   def __build_previousbutton(self):
      ''' builds and returns the "previous comic" button for this form. it
      is only enabled when there's actually a previous comic to go back to
      (self.__has_previous_b), letting the user redo it in case they picked
      the wrong series/issue for it. '''

      button = Button()
      button.DialogResult = DialogResult.Abort
      button.Size = Size(115, 24)
      button.Text = i18n.get("SeriesFormPreviousComic")
      button.Dock = DockStyle.Fill
      button.Enabled = self.__has_previous_b
      return button


   # ==========================================================================
   def __build_issuesbutton(self):
      ''' builds and return the 'show issues' button for this form '''
      
      button = Button()
      button.DialogResult = DialogResult.Yes
      button.Location = Point(395, 362) \
         if self.__config.show_covers_b else Point(605, 362) 
      button.Size = Size(115, 24)
      button.Text = i18n.get("SeriesFormIssues")
      button.Dock = DockStyle.Fill
      return button
   
   
   # ==========================================================================
   def __build_label(self, search_terms_s, num_matches_n):
      ''' 
      Builds and return the text label for this form.
      'search_terms_s' -> user's search string that was used to find series
      'num_matches_n' -> number of series (table rows) the user's search matched
      '''
      
      label = Label()
      label.UseMnemonic = False
      label.Location = Point(10, 20)
      label.Size = Size(480, 40)
      label.Dock = DockStyle.Fill
      if num_matches_n > 1:
         label.Text = i18n.get("SeriesFormChooseText")\
            .format(search_terms_s, num_matches_n )
      else:
         label.Text = i18n.get("SeriesFormConfirmText").format(search_terms_s)
      return label
   

   # ==========================================================================
   def __build_coverpanel(self, book):
      ''' 
      Builds and returns the cover image PictureBox for this form.
      'book' -> the ComicBook being scraped
      '''
      panel = IssueCoverPanel(self.__config, -9991 \
         if self.__config.force_series_art_b else book.issue_num_s,
         editable_hint_b = not self.__config.force_series_art_b)
      panel.Location = Point(523, 30)
      panel.Dock = DockStyle.Fill
      # panel size is determined by the panel itself
      
      if self.__config.show_covers_b:
         panel.Show()
      else:
         panel.Hide()
      return panel
   
   # ==========================================================================
   def show_form(self):
      '''
      Displays this form, blocking until the user closes it.  When it is closed,
      it will return a SeriesFormResult describing how it was closed, and any
      SeriesRef that may have been chosen when it was closed. 
      '''
      
      dialogAnswer = self.ShowDialog(self.Owner) # blocks
      
      if dialogAnswer == DialogResult.OK:
         series = self.__series_refs[self.__chosen_index]
         result = SeriesFormResult( "OK", series,
            self.__coverpanel.get_issue_num_override_s() )
         alt_choice = self.__coverpanel.get_alt_issue_cover_choice()
         if alt_choice:
            issue_ref, image_ref = alt_choice
            # the user chose a non-default cover image for this issue.
            # we'll store that choice in the global "session data map",
            # in case any other part of the program wants to use it.
            alt_cover_key = sstr(issue_ref.issue_key) + "-altcover"
            self.__config.session_data_map[alt_cover_key] = image_ref
      elif dialogAnswer == DialogResult.Yes:
         series = self.__series_refs[self.__chosen_index]
         result = SeriesFormResult( "SHOW", series,
            self.__coverpanel.get_issue_num_override_s() )
      elif dialogAnswer == DialogResult.Cancel: 
         result = SeriesFormResult( "CANCEL")
      elif dialogAnswer == DialogResult.Ignore:
         if self.ModifierKeys == Keys.Control:
            result = SeriesFormResult( "PERMSKIP" )
         else:
            result = SeriesFormResult( "SKIP" )
      elif dialogAnswer == DialogResult.Retry:
         result = SeriesFormResult( "SEARCH" )
      elif dialogAnswer == DialogResult.Abort:
         result = SeriesFormResult( "PREVIOUS" )
      else:
         raise Exception()
      
      return result


   #===========================================================================
   def __form_closed_fired(self, sender, args):
      ''' this method is called whenever this SeriesForm is closed. '''

      self.__filter_debounce_timer.Stop()
      self.__filter_debounce_timer.Dispose()
      self.__table.Dispose()
      self.__coverpanel.free()
      self.Closed -= self.__form_closed_fired


   #===========================================================================         
   def __change_table_selection_fired(self, sender, args):
      ''' this method is called whenever the table's selected row changes. '''
      try:
         selected_rows = self.__table.SelectedRows
         if selected_rows.Count == 1:
            model_id = selected_rows[0].Cells[6].Value if selected_rows[0].Cells.Count > 6 else None
            log.debug('SeriesForm: selection changed model_id=%s' % (model_id,))
            if model_id is not None and isinstance(model_id, (int, long)) and 0 <= model_id < len(self.__series_refs):
               self.__chosen_index = model_id
               try:
                  ref = self.__series_refs[self.__chosen_index]
                  self.__coverpanel.set_ref(ref)
                  # Log todas las propiedades simples del objeto seleccionado
                  try:
                     # evitar log repetido para el mismo objeto consecutivamente
                     key = getattr(ref, 'series_key', None)
                     if getattr(self, '_SeriesForm__last_logged_series_key', None) != key:
                        simple_items = []
                        for name in dir(ref):
                           if name.startswith('_'): continue
                           try:
                              val = getattr(ref, name)
                           except Exception:
                              continue
                           # ignorar callables
                           if callable(val):
                              continue
                           # tipos simples
                           if isinstance(val, (int, long, float, bool)) or isinstance(val, (str, unicode)):
                              sval = sstr(val)
                              if len(sval) > 120:
                                 sval = sval[:117] + '...'
                              simple_items.append('%s=%s' % (name, sval))
                        simple_items.sort()
                        log.debug('SeriesForm: series properties => ' + '; '.join(simple_items))
                        self.__last_logged_series_key = key
                  except Exception as le:
                     log.debug('SeriesForm: logging series properties failed %s' % le)
               except Exception as e:
                  log.debug('SeriesForm: coverpanel set_ref error %s' % e)
            else:
               # fila inválida (probablemente fila vacía); ignorar
               self.__chosen_index = None
               self.__coverpanel.set_ref(None)
         else:
            self.__chosen_index = None
            self.__coverpanel.set_ref(None)
      except Exception as e:
         log.debug('SeriesForm: __change_table_selection_fired error %s' % e)
         self.__chosen_index = None
         try:
            self.__coverpanel.set_ref(None)
         except Exception:
            pass
      finally:
         self.__ok_button.Enabled = self.__chosen_index is not None
         self.__issues_button.Enabled = self.__chosen_index is not None
      # update __chosen_index (eventually used as this dialog's return value)
      # and then also use it to update the displayed cover image.
               
   #===========================================================================         
   def __key_was_pressed(self, sender, args):
      ''' Called whenever the user presses any key on this form. '''
      
      # highlight the skip button whenever the user presses control key
      if args.KeyCode == Keys.ControlKey and not self.__pressing_controlkey:
         self.__pressing_controlkey = True;
         self.__skip_button.Text = "- " + i18n.get("SeriesFormSkip") + " -"
         
   #===========================================================================         
   def __key_was_released(self, sender, args):
      ''' Called whenever the user releases any key on this form. '''
      
      # unhighlight the skip button bold whenever the user releases control key
      if args.KeyCode == Keys.ControlKey:
         self.__pressing_controlkey = False;
         self.__skip_button.Text = i18n.get("SeriesFormSkip")

   #===========================================================================         
   def __was_deactivated(self, sender, args):
      ''' Called whenever this form gets deactivated, for any reason '''
      
      # unhighlight the skip button bold whenever we deactivate
      if self.__pressing_controlkey:
         self.__pressing_controlkey = False;
         self.__skip_button.Text = i18n.get("SeriesFormSkip")
      
      
#==============================================================================      
class SeriesFormResult(object):
   '''
   Results that can be returned from the SeriesForm.show_form() method.  The
   'id' of this object describes the manner in which the user closed the 
   dialog:
   
   1) "CANCEL"  means the user cancelled this scrape operation.
   2) "SKIP" means the user elected to skip the current book.
   3) "PERMSKIP" means the user elected to skip the current book
      during this scrape, AND all future scrapes (i.e. add a 'skip tag' to book)
   4) "SEARCH" means the user chose to 'search again'
   5) "OK" means the user chose a SeriesRef, and the script
      should try to automatically choose the correct issue for that SeriesRef.
   6) "SHOW" means the user chose a SeriesRef, and the script
      should NOT automatically choose issue for that SeriesRef--it should
      show the IssueForm and let the user choose manually.
   7) "PREVIOUS" means the user chose to go back and redo the
      immediately-previous comic book (only possible when this form was
      built with has_previous_b=True)

   Note that if the SeriesFormResult has an id of 'OK' or 'SHOW', it must
   also have a non-None 'ref', which is of course the actual SeriesRef that
   the user chose.
   '''
   
   #===========================================================================
   def __init__(self, id, ref=None, issue_num_override_s=None):
      '''
      Creates a new SeriesFormResult.
      id -> the id of the result, i.e. "OK", "SHOW", "CANCEL", "SKIP", etc.
      ref -> the reference that the user chose, if they chose one at all.
             (required for "SHOW" and "OK".)
      issue_num_override_s -> only meaningful for "OK"/"SHOW". If the user
             manually edited the issue-number preview field on the series
             dialog's cover panel, this is the issue number they typed --
             callers should prefer it over the book's auto-detected issue
             number when picking which issue to scrape. None if the user
             never edited that field (i.e. use the book's own issue number).
      '''

      if id != "OK" and id != "SHOW" and id != "CANCEL" and \
         id != "SKIP" and id != "SEARCH" and id != "PERMSKIP" and \
         id != "PREVIOUS":
         raise Exception()
      if (id == "OK" or id == "SHOW") and ref == None:
         raise Exception()

      self.__ref = ref if id == "OK" or id == "SHOW" else None;
      self.__id = id;
      self.__issue_num_override_s = \
         issue_num_override_s if id == "OK" or id == "SHOW" else None


   #===========================================================================
   def equals(self, id):
      '''
      Returns True iff this SeriesFormResult has the given ID (i.e. one of
      "SHOW", "OK, "CANCEL", "SKIP", etc.)
      '''
      return self.__id == id


   #===========================================================================
   def get_issue_num_override_s(self):
      '''
      Gets the issue number the user manually typed into the series
      dialog's cover-preview field, overriding the book's own auto-detected
      issue number -- or None if they never edited that field. Only ever
      non-None when the id of this result is "OK" or "SHOW".
      '''
      return self.__issue_num_override_s


   #===========================================================================
   def get_ref(self):
      '''
      Gets the SeriesRef portion of this result, i.e. the one the user picked.
      This is only defined when the id of this result is "OK" or "SHOW".
      '''
      return self.__ref;

   
   #===========================================================================         
   def get_debug_string(self):
      ''' Gets a simple little debug string summarizing this result.'''
      
      if self.equals("SKIP"):
         return "SKIP scraping this book"
      elif self.equals("PERMSKIP"):
         return "ALWAYS SKIP scraping this book"
      elif self.equals("CANCEL"):
         return "CANCEL this scrape operation"
      elif self.equals("SEARCH"):
         return "SEARCH AGAIN for more series"
      elif self.equals("SHOW"):
         return "SHOW ISSUES for: '" + sstr(self.get_ref()) + "'"
      elif self.equals("OK"):
         return "SCRAPE using: '" + sstr(self.get_ref()) + "'"
      elif self.equals("PREVIOUS"):
         return "GO BACK to redo the previous comic book"
      else:
         raise Exception()
