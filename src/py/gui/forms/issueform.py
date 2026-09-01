# -*- coding: utf-8 -*-
'''
This module is home to the IssuesForm and IssuesFormResult classes. 

@author: Cory Banack
'''

import clr
import log
import i18n
import utils
from utils import sstr
from buttondgv import ButtonDataGridView
from issuecoverpanel import IssueCoverPanel
from cvform import CVForm

clr.AddReference('Microsoft.VisualBasic')
from System.ComponentModel import ListSortDirection

clr.AddReference('System.Drawing')
from System.Drawing import Point, Size

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import AutoScaleMode, Button, \
   DataGridViewAutoSizeColumnMode, DataGridViewContentAlignment, \
   DataGridViewSelectionMode, DialogResult, Keys, Label, \
   TableLayoutPanel, DockStyle, DataGridViewColumnHeadersHeightSizeMode, \
   FormBorderStyle, TextBox, Panel, ToolTip, Timer  # añadido FormBorderStyle para hacer ventana sizeable
import System  # para ColumnStyle/RowStyle



#==============================================================================
class IssueForm(CVForm):
   '''
   This class is a popup, modal dialog that displays all of the Comic Book
   issues in a series.  The issues are shown in a table, which the user can 
   navigate through, browsing the cover art for each issue. Once the user has 
   selected the issue that matches the comic that she is scraping, she clicks 
   the ok button to close this dialog and continue scraping her comic using the 
   identified IssueRef.
   '''
   
   #===========================================================================
   def __init__(self, scraper, issue_ref_hint, issue_refs, series_ref,
         has_previous_b=False):
      '''
      Initializes this form.  If a good issue key hint is given, that issue will
      be preselected in the table if possible.

      'scraper' -> the currently running ScrapeEngine
      'issue_ref_hint' -> may be the issue id for the given book (or may not!)
      'issue_refs' -> a set or list containing the IssueRefs to display
      'series_ref' -> SeriesRef for the series that the given issues belong to
      'has_previous_b' -> whether there's a previous comic book that the user
          can go back and redo (enables the "Previous Comic" button).
      '''

      # the the shared global configuration
      self.__config = scraper.config

      # whether the "Previous Comic" button should be enabled
      self.__has_previous_b = has_previous_b

      # a list of IssueRef objects that back this form; one ref per table row,
      # where each IssueRef represents an issue that the user can pick
      self.__issue_refs = list(issue_refs)

      # true when the user is pressing the control key, false otherwise
      self.__pressing_controlkey = False;

      # the ok button for this dialog
      self.__ok_button = None

      # the skip button for this dialog
      self.__skip_button = None

      # the label for this dialog
      self.__label = None
      
      # the table that displays issues (one per row) for the user to pick from
      self.__table = None

      # the panel that hosts the table plus the filter row above it
      self.__table_container = None

      # the filter panel and its textboxes (Issue, Title, Year, Month)
      self.__filter_panel = None
      self.__filter_issue = self.__filter_title = None
      self.__filter_year = self.__filter_month = None
      self.__filter_textboxes = []

      # debounces filter textbox changes, so that filtering a table with
      # hundreds of rows doesn't re-run on every single keystroke
      self.__filter_debounce_timer = Timer()
      self.__filter_debounce_timer.Interval = 1000
      self.__filter_debounce_timer.Tick += self.__filter_debounce_tick

      # whether or no we were able to pre-select the "hinted" issue in the table
      self.__found_issue_in_table = False
      
      # IssueCoverPAnel that shows the cover for the currently selected IssueRef
      self.__coverpanel = None
      
      ## the index (into self.__issue_refs) of the currently selected IssueRef
      self.__chosen_index = None
      
      if len(issue_refs) <= 0:
         raise Exception("do not invoke the IssueForm with no IssueRefs!")
      CVForm.__init__(self, scraper.comicrack.MainWindow, "issueformLocation")
      self.__build_gui(issue_ref_hint, series_ref)
      scraper.cancel_listeners.append(self.Close)
      
   # ==========================================================================
   def __build_gui(self, issue_ref_hint, series_ref):
      ''' Constructs and initializes the gui for this form. '''
      
      # 1. --- build each gui component
      self.__ok_button = self.__build_okbutton()
      self.__skip_button = self.__build_skipbutton()
      back_button = self.__build_backbutton()
      previous_button = self.__build_previousbutton()
      self.__table = self.__build_table(
         self.__issue_refs, issue_ref_hint, self.__ok_button)
      self.__table_container = self.__build_filters_panel(self.__table)
      self.__label = self.__build_label(series_ref) # must build AFTER table!
      self.__coverpanel = self.__build_coverpanel()

      # 2. --- configure this form, and add all the gui components to it
      self.AutoScaleMode = AutoScaleMode.Font
      self.ClientSize = Size(950, 560)
      self.Text = i18n.get("IssueFormTitle")
      self.FormBorderStyle = FormBorderStyle.Sizable  # permitir redimensionar
      self.FormClosed += self.__form_closed_fired
      self.KeyPreview = True;
      self.KeyDown += self.__key_was_pressed
      self.KeyUp += self.__key_was_released
      self.Deactivate += self.__was_deactivated

      # Responsive layout using TableLayoutPanel
      main_layout = TableLayoutPanel()
      if self.__config.show_covers_b:
         main_layout.ColumnCount = 2
         # left column fixed for cover panel, right column stretches
         main_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 210))
         main_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 100))
      else:
         main_layout.ColumnCount = 1
         main_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 100))
      main_layout.RowCount = 3
      main_layout.RowStyles.Add(System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 64))
      main_layout.RowStyles.Add(System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100))
      main_layout.RowStyles.Add(System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 64))
      main_layout.Dock = DockStyle.Fill

      # Buttons sublayout
      buttons_layout = TableLayoutPanel()
      buttons_layout.ColumnCount = 4
      buttons_layout.RowCount = 1
      buttons_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 25))
      buttons_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 25))
      buttons_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 25))
      buttons_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 25))
      buttons_layout.Dock = DockStyle.Fill
      self.__ok_button.Dock = DockStyle.Fill
      self.__skip_button.Dock = DockStyle.Fill
      back_button.Dock = DockStyle.Fill
      previous_button.Dock = DockStyle.Fill
      buttons_layout.Controls.Add(self.__ok_button, 0, 0)
      buttons_layout.Controls.Add(self.__skip_button, 1, 0)
      buttons_layout.Controls.Add(back_button, 2, 0)
      buttons_layout.Controls.Add(previous_button, 3, 0)

      # Add controls
      if self.__config.show_covers_b:
         self.__coverpanel.Dock = DockStyle.Fill
         main_layout.Controls.Add(self.__coverpanel, 0, 0)
         main_layout.SetRowSpan(self.__coverpanel, 3)
         main_layout.Controls.Add(self.__label, 1, 0)
         main_layout.Controls.Add(self.__table_container, 1, 1)
         main_layout.Controls.Add(buttons_layout, 1, 2)
      else:
         main_layout.Controls.Add(self.__label, 0, 0)
         main_layout.Controls.Add(self.__table_container, 0, 1)
         main_layout.Controls.Add(buttons_layout, 0, 2)

      self.Controls.Add(main_layout)

      # 3. --- define the keyboard focus tab traversal ordering      
      self.__ok_button.TabIndex = 1
      self.__skip_button.TabIndex = 2
      back_button.TabIndex = 3
      previous_button.TabIndex = 4
      self.__coverpanel.TabIndex = 5
      self.__table.TabIndex = 6

      #4. --- make sure the UI goes into a good initial state
      self.Shown += self.__change_table_selection_fired
      self.Shown += self.__update_filter_positions


   # =========================================================================   
   def __build_table(self, issue_refs, issue_ref_hint, enter_button):
      '''
      Builds and returns the table for this form. If a good issue key hint is 
      given, that issue will be preselected in the table if possible.
      
      'issue_refs' -> a list with one IssueRef object for each row in the table
      'issue_ref_hint' -> may be the issue key for the given book (or may not!)
      'enter_button' -> the button to "press" if the user hits enter
      '''
      
      # 1. --- configure the table itself
      table = ButtonDataGridView(enter_button)
      table.SortCompare += self.__sort_compare_fired
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
      # Ajuste de altura encabezados para alta resolucion
      table.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.EnableResizing
      if table.ColumnHeadersHeight < 38:
         table.ColumnHeadersHeight = 42
      
      # 2. --- build columns
      table.ColumnCount = 6
      table.Columns[0].Name = i18n.get("IssueFormIssueCol")
      table.Columns[0].DefaultCellStyle.Alignment =\
         DataGridViewContentAlignment.MiddleCenter
      table.Columns[0].AutoSizeMode = \
         DataGridViewAutoSizeColumnMode.AllCells

      table.Columns[1].Name = i18n.get("IssueFormTitleCol")
      table.Columns[1].DefaultCellStyle.Alignment =\
         DataGridViewContentAlignment.MiddleLeft
      table.Columns[1].AutoSizeMode = \
         DataGridViewAutoSizeColumnMode.Fill

      table.Columns[2].Name = i18n.get("IssueFormYearCol")
      table.Columns[2].DefaultCellStyle.Alignment =\
         DataGridViewContentAlignment.MiddleCenter
      table.Columns[2].AutoSizeMode = \
         DataGridViewAutoSizeColumnMode.AllCells

      table.Columns[3].Name = i18n.get("IssueFormMonthCol")
      table.Columns[3].DefaultCellStyle.Alignment =\
         DataGridViewContentAlignment.MiddleCenter
      table.Columns[3].AutoSizeMode = \
         DataGridViewAutoSizeColumnMode.AllCells

      table.Columns[4].Name = "ID"
      table.Columns[4].Visible = False
      table.Columns[4].DefaultCellStyle.Alignment =\
         DataGridViewContentAlignment.MiddleCenter
      table.Columns[4].AutoSizeMode = \
         DataGridViewAutoSizeColumnMode.AllCells

      table.Columns[5].Name = "Model ID"
      table.Columns[5].Visible = False
      table.Columns[5].DefaultCellStyle.Alignment =\
         DataGridViewContentAlignment.MiddleCenter
      table.Columns[5].AutoSizeMode =\
         DataGridViewAutoSizeColumnMode.AllCells

      # 3. --- copy model data into the table, each issue is a row
      for i in range(len(issue_refs)):
         self.__add_row(table, issue_refs[i], i)

      # 4. --- sort and preselect
      table.Sort(table.Columns[0], ListSortDirection.Ascending)
      if issue_ref_hint:
         for i in range(table.Rows.Count):
            if table.Rows[i].Cells[4].Value == issue_ref_hint.issue_key:
               table.CurrentCell = table.Rows[i].Cells[0]
               self.__found_issue_in_table = True
               break
      if not self.__found_issue_in_table and table.Rows.Count > 0:
         table.CurrentCell = table.Rows[0].Cells[0]

      table.SelectionChanged += self.__change_table_selection_fired
      return table


   # =========================================================================
   def __add_row(self, table, issue_ref, model_index):
      ''' Adds a single row (for the given IssueRef) to the given table. '''
      title_s = issue_ref.title_s
      key = issue_ref.issue_key
      issue_num_s = issue_ref.issue_num_s
      year_s = sstr(issue_ref.pub_year_n) if issue_ref.pub_year_n > 0 else ''
      month_s = ('%02d' % issue_ref.pub_month_n) \
         if issue_ref.pub_month_n > 0 else ''
      table.Rows.Add()
      row = table.Rows[table.Rows.Count - 1]
      row.Cells[0].Value = issue_num_s if issue_num_s else ''
      row.Cells[1].Value = '   ' + title_s if title_s else ''
      row.Cells[2].Value = year_s
      row.Cells[3].Value = month_s
      row.Cells[4].Value = key
      row.Cells[5].Value = model_index


   # =========================================================================
   def __build_filters_panel(self, table):
      '''
      Wraps the given table in a container Panel that also holds a thin
      filter row (docked to the top) with one textbox per visible column
      (Issue, Title, Year, Month), letting the user filter the table's rows.
      Returns the container Panel, which should be added to this form's
      layout INSTEAD OF the table itself.
      '''
      container = Panel()
      container.Dock = DockStyle.Fill
      filter_panel = Panel()
      filter_panel.Height = 28
      filter_panel.Dock = DockStyle.Top
      filter_panel.BackColor = table.BackColor

      self.__filter_issue = TextBox()
      self.__filter_title = TextBox()
      self.__filter_year = TextBox()
      self.__filter_month = TextBox()

      tip = ToolTip()
      tip.SetToolTip(self.__filter_issue, i18n.get("IssueFormIssueCol"))
      tip.SetToolTip(self.__filter_title, i18n.get("IssueFormTitleCol"))
      tip.SetToolTip(self.__filter_year, i18n.get("IssueFormYearCol"))
      tip.SetToolTip(self.__filter_month, i18n.get("IssueFormMonthCol"))

      self.__filter_textboxes = [self.__filter_issue, self.__filter_title,
         self.__filter_year, self.__filter_month]

      # give each box a safe, non-overlapping default position/size right
      # away, roughly matching the columns' relative proportions. this
      # matters because __update_filter_positions (below) can only compute
      # real column rectangles once the table has actually been laid out
      # (i.e. after HandleCreated/Shown); until then, leaving Left/Width at
      # their WinForms defaults (0,0) would stack all four boxes on top of
      # each other, making only the last one (Month) clickable/typeable.
      default_lefts_n = [0, 90, 340, 420]
      default_widths_n = [85, 245, 75, 75]
      for idx, tb in enumerate(self.__filter_textboxes):
         tb.Top = 4
         tb.Height = 20
         tb.Left = default_lefts_n[idx]
         tb.Width = default_widths_n[idx]
         tb.TextChanged += self.__filters_changed
         utils.fix_ctrl_backspace(tb)
         filter_panel.Controls.Add(tb)

      table.Dock = DockStyle.Fill
      container.Controls.Add(table)
      container.Controls.Add(filter_panel)
      self.__filter_panel = filter_panel

      table.ColumnWidthChanged += self.__update_filter_positions
      table.Scroll += self.__update_filter_positions
      table.ColumnDisplayIndexChanged += self.__update_filter_positions
      table.SizeChanged += self.__update_filter_positions
      table.Layout += self.__update_filter_positions
      table.HandleCreated += self.__update_filter_positions
      try:
         self.__update_filter_positions(table, None)
      except Exception:
         pass
      return container


   # =========================================================================
   def __update_filter_positions(self, sender, args):
      ''' Keeps the filter textboxes aligned under their table columns. '''
      try:
         if self.__table is None or self.__filter_panel is None:
            return
         target_cols = [0, 1, 2, 3]
         for idx, col_index in enumerate(target_cols):
            if col_index >= self.__table.Columns.Count:
               continue
            col = self.__table.Columns[col_index]
            if not col.Visible:
               continue
            rect = self.__table.GetCellDisplayRectangle(col_index, -1, True)
            if rect.Width <= 0:
               # column isn't actually laid out/displayed yet (e.g. before
               # the form is shown) -- keep the current position rather
               # than collapsing this box to a sliver at the left edge;
               # a later Layout/SizeChanged/Shown event will retry this.
               continue
            tb = self.__filter_textboxes[idx]
            tb.Left = rect.X + 2
            new_width = rect.Width - 4
            if new_width < 15:
               new_width = 15
            tb.Width = new_width
         self.__filter_panel.Refresh()
      except Exception as e:
         log.debug('IssueForm: update_filter_positions error %s' % e)


   # =========================================================================
   def __apply_filters(self):
      ''' Shows/hides each of the table's (already built) rows depending on
      whether the underlying IssueRef matches all of the current (substring,
      case-insensitive) filter textbox values. Rows are never removed or
      re-added here, so clearing the filters always restores every row. '''
      if self.__table is None:
         return
      f_issue = (self.__filter_issue.Text or '').strip().lower()
      f_title = (self.__filter_title.Text or '').strip().lower()
      f_year = (self.__filter_year.Text or '').strip().lower()
      f_month = (self.__filter_month.Text or '').strip().lower()

      # deselect first -- hiding the currently selected/current row while
      # it's still selected can confuse the grid's internal state.
      self.__chosen_index = None
      try:
         self.__table.CurrentCell = None
      except Exception:
         pass

      first_visible_row = None
      for row in self.__table.Rows:
         try:
            model_index = row.Cells[5].Value
            ref = self.__issue_refs[model_index]
            issue_s = (ref.issue_num_s or '').lower()
            title_s = (ref.title_s or '').lower()
            year_s = sstr(ref.pub_year_n).lower() if ref.pub_year_n > 0 else ''
            month_s = ('%02d' % ref.pub_month_n) if ref.pub_month_n > 0 else ''

            matches = True
            if f_issue and f_issue not in issue_s:
               matches = False
            if f_title and f_title not in title_s:
               matches = False
            if f_year and f_year not in year_s:
               matches = False
            if f_month and f_month not in month_s:
               matches = False

            row.Visible = matches
            if matches and first_visible_row is None:
               first_visible_row = row
         except Exception as e:
            log.debug('IssueForm: filter row error %s' % e)

      if first_visible_row is not None:
         try:
            self.__table.CurrentCell = first_visible_row.Cells[0]
         except Exception as es:
            log.debug('IssueForm: filter selection error %s' % es)
      self.__change_table_selection_fired(None, None)


   # =========================================================================
   def __filters_changed(self, sender, args):
      ''' Called whenever the text in any of the filter textboxes changes.
      Debounced: (re)starts a 1-second timer instead of filtering right
      away, so that typing "33" doesn't filter for "3" and then "33" --
      with hundreds of rows in the table, filtering on every keystroke
      makes typing feel laggy. '''
      try:
         self.__filter_debounce_timer.Stop()
         self.__filter_debounce_timer.Start()
      except Exception as e:
         log.debug('IssueForm: filter debounce error: ' + sstr(e))

   # =========================================================================
   def __filter_debounce_tick(self, sender, args):
      ''' Called ~1 second after the user stops typing in a filter textbox.'''
      self.__filter_debounce_timer.Stop()
      try:
         self.__apply_filters()
      except Exception as e:
         log.debug('IssueForm: filter error: ' + sstr(e))


   # ==========================================================================
   def __build_okbutton(self):
      ''' builds and returns the ok button for this form '''
      button = Button() 
      button.DialogResult = DialogResult.OK
      button.Text = i18n.get("IssueFormOK")
      return button

   # ==========================================================================
   def __build_skipbutton(self):
      ''' builds and returns the skip button for this form '''
      button = Button()
      button.DialogResult = DialogResult.Ignore
      button.Text = i18n.get("IssueFormSkip")
      return button
      
   # ==========================================================================
   def __build_backbutton(self):
      ''' builds and returns the back button for this form '''
      button = Button()
      button.DialogResult = DialogResult.Retry
      button.Text = i18n.get("IssueFormGoBack")
      return button

   # ==========================================================================
   def __build_previousbutton(self):
      ''' builds and returns the "previous comic" button for this form. it
      is only enabled when there's actually a previous comic to go back to
      (self.__has_previous_b), letting the user redo it in case they picked
      the wrong series/issue for it. '''
      button = Button()
      button.DialogResult = DialogResult.Abort
      button.Text = i18n.get("IssueFormPreviousComic")
      button.Enabled = self.__has_previous_b
      return button

   # ==========================================================================
   def __build_label(self, series_ref):
      ''' builds and returns the main text label for this form '''
      name_s = series_ref.series_name_s
      publisher_s = series_ref.publisher_s
      vol_year_n = series_ref.volume_year_n
      vol_year_s = sstr(vol_year_n) if vol_year_n > 0 else ''
      fullname_s = ''
      if name_s:
         if publisher_s:
            if vol_year_s:
               fullname_s = "'"+name_s+"' ("+publisher_s+", " + vol_year_s + ")"
            else:
               fullname_s = "'"+name_s+"' (" + publisher_s + ")"
         else:
            fullname_s = "'"+name_s+"'"
      label = Label()
      label.UseMnemonic = False
      sep = '  ' if len(fullname_s) > 40 else '\n'
      label.Text = i18n.get("IssueFormChooseText").format(fullname_s, sep)
      label.Dock = DockStyle.Fill
      return label
   
   # ==========================================================================
   def __build_coverpanel(self):
      ''' builds and returns the IssueCoverPanel for this form '''
      panel = IssueCoverPanel(self.__config)
      return panel
   
   # ==========================================================================
   def show_form(self):
      '''
      Displays this form, blocking until the user closes it.  When it is closed,
      it will return an IssueFormResult describing how it was closed, and any
      IssueRef that may have been chosen when it was closed.
      '''
      dialogAnswer = self.ShowDialog(self.Owner) # blocks
      if dialogAnswer == DialogResult.OK:
         issue = self.__issue_refs[self.__chosen_index]
         result = IssueFormResult( "OK", issue )
         alt_choice = self.__coverpanel.get_alt_issue_cover_choice()
         if alt_choice:
            issue_ref, image_ref = alt_choice
            alt_cover_key = sstr(issue_ref.issue_key) + "-altcover"
            self.__config.session_data_map[alt_cover_key] = image_ref
      elif dialogAnswer == DialogResult.Cancel:
         result = IssueFormResult( "CANCEL" )
      elif dialogAnswer == DialogResult.Ignore:
         if self.ModifierKeys == Keys.Control:
            result = IssueFormResult( "PERMSKIP" )
         else:
            result = IssueFormResult( "SKIP" )
      elif dialogAnswer == DialogResult.Retry:
         result = IssueFormResult( "BACK" )
      elif dialogAnswer == DialogResult.Abort:
         result = IssueFormResult( "PREVIOUS" )
      else:
         raise Exception()
      return result
   
   # ==========================================================================
   def __form_closed_fired(self, sender, args):
      ''' this method is called whenever this IssueForm is closed. '''
      self.__filter_debounce_timer.Stop()
      self.__filter_debounce_timer.Dispose()
      self.__table.Dispose()
      self.__coverpanel.free()
      self.Closed -= self.__form_closed_fired
      
   # ==========================================================================
   def __change_table_selection_fired(self, sender, args):
      ''' this method is called whenever the table's selected row changes '''
      selected_rows = self.__table.SelectedRows
      if selected_rows.Count == 1:
         self.__chosen_index = selected_rows[0].Cells[5].Value
         self.__coverpanel.set_ref(
            self.__issue_refs[self.__chosen_index] )
      else:
         self.__chosen_index = None
         self.__coverpanel.set_ref( None ) 
      self.__ok_button.Enabled = selected_rows.Count == 1
      
   # ==========================================================================
   def __sort_compare_fired(self, sender, args):
      ''' this method is called whenever the table is resorted '''
      if args.Column.Index == 0: 
         args.SortResult = utils.natural_compare( \
            args.CellValue1, args.CellValue2 )
         args.Handled = True
         
   #===========================================================================         
   def __key_was_pressed(self, sender, args):
      ''' Called whenever the user presses any key on this form. '''
      if args.KeyCode == Keys.ControlKey and not self.__pressing_controlkey:
         self.__pressing_controlkey = True;
         self.__skip_button.Text = "- " + i18n.get("IssueFormSkip") + " -"
         
   #===========================================================================         
   def __key_was_released(self, sender, args):
      ''' Called whenever the user releases any key on this form. '''
      if args.KeyCode == Keys.ControlKey:
         self.__pressing_controlkey = False;
         self.__skip_button.Text = i18n.get("IssueFormSkip")
         
   #===========================================================================         
   def __was_deactivated(self, sender, args):
      ''' Called whenever this form gets deactivated, for any reason '''
      if self.__pressing_controlkey:
         self.__pressing_controlkey = False;
         self.__skip_button.Text = i18n.get("IssueFormSkip")
      
#==============================================================================      
class IssueFormResult(object):
   '''
   Results that can be returned from the IssueForm.show_form() method.  The
   'id' of this object describes the manner in which the user closed the 
   dialog:
   
   1) "CANCEL" means the user cancelled this scrape operation.
   2) "SKIP" means the user elected to skip the current book.
   3) "PERMSKIP" means the user elected to skip the current book
      during this scrape, AND all future scrapes (i.e. add a 'skip tag' to book)
   4) "BACK" means the user chose to return to the SeriesForm
   5) "OK" means the user chose an IssueRef from those displayed
   6) "PREVIOUS" means the user chose to go back and redo the
      immediately-previous comic book (only possible when this form was
      built with has_previous_b=True)

   Note that if the IssueFormResult has an id of 'OK', it must also have a
   non-None 'ref', which is of course the actual IssueRef that the user chose.
   '''

   #===========================================================================
   def __init__(self, id, ref=None):
      '''
      Creates a new IssueFormResult.
      id -> the id of the result, i.e. "OK", "CANCEL", "BACK", etc.
      ref -> the reference that the user chose, if they chose one at all.
             (required for "OK".)
      '''
      if id != "OK" and id != "CANCEL" and id != "SKIP" and \
         id != "BACK" and id != "PERMSKIP" and id != "PREVIOUS":
         raise Exception()
      if id == "OK" and ref == None:
         raise Exception()
      self.__ref = ref if id == "OK" else None;
      self.__id = id;

   #===========================================================================         
   def equals(self, id): 
      ''' Returns True iff this SeriesFormResult has the given ID. '''
      return self.__id == id

   #===========================================================================         
   def get_ref(self):
      ''' Gets the IssueRef chosen (only valid for id == "OK"). '''
      return self.__ref;

   #===========================================================================         
   def get_debug_string(self):
      ''' Gets a simple debug string summarizing this result.'''
      if self.equals("SKIP"):
         return "SKIP scraping this book"
      elif self.equals("PERMSKIP"):
         return "ALWAYS SKIP scraping this book"
      elif self.equals("CANCEL"):
         return "CANCEL this scrape operation"
      elif self.equals("BACK"):
         return "GO BACK to the series dialog"
      elif self.equals("PREVIOUS"):
         return "GO BACK to redo the previous comic book"
      elif self.equals("OK"):
         return "SCRAPE using: '" + sstr(self.get_ref()) + "'"
      else:
         raise Exception()

