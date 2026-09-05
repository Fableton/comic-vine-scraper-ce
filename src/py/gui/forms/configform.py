'''
This module contains the ConfigForm class (a popup dialog).

@author: Cory Banack
'''
import re
import clr
import log
from cvform import CVForm
from System.Windows.Forms import FormBorderStyle, DockStyle
from configuration import Configuration, load_known_publishers_sl
from utils import sstr
import guistyle
import i18n
import System

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import AutoScaleMode, Button, CheckBox, ComboBox, \
    ComboBoxStyle, ContextMenu, CheckedListBox, DataGridView, \
    DataGridViewAutoSizeColumnMode, DataGridViewButtonColumn, \
    DataGridViewColumnHeadersHeightSizeMode, \
    DataGridViewContentAlignment, DataGridViewSelectionMode, DialogResult, \
    FlatStyle, Label, MenuItem, MessageBox, MessageBoxButtons, \
    MessageBoxIcon, NumericUpDown, RichTextBox, SelectionMode, TabControl, \
    TabPage, TextBox, LinkLabel, TableLayoutPanel, TrackBar, TickStyle

clr.AddReference('System.Drawing')
from System.Drawing import Color, Point, Size, ContentAlignment

# =============================================================================
class ConfigForm(CVForm):
   '''
   This class is a popup, modal dialog that displays all of the configurable
   options available to the user.   The user can change any of the options, 
   and then click OK or Cancel to quit the dialog and contine the normal 
   execution of the program.   Clicking Cancel will discard any configuration
   changes that were made; clicking OK will save them permanently.
   '''
   
   # ==========================================================================
   def __init__(self, owner):
      ''' 
      Initializes this form.
      owner -> this form's owner window/dialog
      '''
      
      # these are the strings that the user sees for each checkbox; they can 
      # also be used to reference each checkbox inside the checkboxlist
      ConfigForm.__SERIES_CB = i18n.get("ConfigFormSeriesCB")
      ConfigForm.__NUMBER_CB = i18n.get("ConfigFormNumberCB")
      ConfigForm.__PUBLISHED_CB = i18n.get("ConfigFormPublishedCB")
      ConfigForm.__RELEASED_CB = i18n.get("ConfigFormReleasedCB")
      ConfigForm.__TITLE_CB = i18n.get("ConfigFormTitleCB")
      ConfigForm.__CROSSOVERS_CB = i18n.get("ConfigFormCrossoversCB")
      ConfigForm.__WRITER_CB = i18n.get("ConfigFormWriterCB")
      ConfigForm.__PENCILLER_CB = i18n.get("ConfigFormPencillerCB")
      ConfigForm.__INKER_CB = i18n.get("ConfigFormInkerCB")
      ConfigForm.__COVER_ARTIST_CB = i18n.get("ConfigFormCoverCB")
      ConfigForm.__COLORIST_CB = i18n.get("ConfigFormColoristCB")
      ConfigForm.__LETTERER_CB = i18n.get("ConfigFormLettererCB")
      ConfigForm.__EDITOR_CB = i18n.get("ConfigFormEditorCB")
      ConfigForm.__SUMMARY_CB = i18n.get("ConfigFormSummaryCB")
      ConfigForm.__IMPRINT_CB = i18n.get("ConfigFormImprintCB")
      ConfigForm.__PUBLISHER_CB = i18n.get("ConfigFormPublisherCB")
      ConfigForm.__VOLUME_CB = i18n.get("ConfigFormVolumeCB")
      ConfigForm.__CHARACTERS_CB = i18n.get("ConfigFormCharactersCB")
      ConfigForm.__TEAMS_CB = i18n.get("ConfigFormTeamsCB")
      ConfigForm.__LOCATIONS_CB = i18n.get("ConfigFormLocationsCB")
      ConfigForm.__WEBPAGE_CB = i18n.get("ConfigFormWebCB")
      
      # the TabControl that contains all our TabPages
      self.__tabcontrol = None
      
      # the ok button for this dialog
      self.__ok_button = None
      
      # the cancel button for this dialog
      self.__cancel_button = None
      
      # the restore defaults button for this dialog
      self.__restore_button = None
      
      # "options" checkboxes
      self.__ow_existing_cb = None 
      self.__ignore_blanks_cb = None                                          
      self.__autochoose_series_cb = None
      self.__confirm_issue_cb = None
      self.__convert_imprints_cb = None
      self.__summary_dialog_cb = None
      self.__download_thumbs_cb = None
      self.__preserve_thumbs_cb = None
      self.__fast_rescrape_cb = None
      self.__rescrape_tags_cb = None
      self.__rescrape_notes_cb = None
      
      # "api key" textbox
      self.__api_key_tbox = None
      
      # "advanced settings" textbox
      self.__advanced_tbox = None

      # "data" checkbox list
      self.__update_checklist = None

      # the "add a publisher to ignore" combobox and button (publishers tab)
      self.__publisher_combobox = None
      self.__publisher_add_button = None

      # the table listing all currently-ignored publishers (publishers tab)
      self.__publisher_table = None

      # the "add a search term to ignore" combobox/button/table
      # (search filters tab)
      self.__searchterm_combobox = None
      self.__searchterm_table = None

      # the year-range / never-ignore-threshold / max-results controls
      # (search filters tab)
      self.__before_year_cb = None
      self.__before_year_nud = None
      self.__after_year_cb = None
      self.__after_year_nud = None
      self.__threshold_cb = None
      self.__threshold_nud = None
      self.__max_results_nud = None

      # the "add a publisher alias" textboxes and the alias table
      # (publisher aliases tab)
      self.__alias_from_tbox = None
      self.__alias_to_tbox = None
      self.__alias_table = None

      # the behavior checkboxes, scrape delay, and alt search regex
      # controls (advanced tab)
      self.__rating_cb = None
      self.__show_covers_cb = None
      self.__welcome_dialog_cb = None
      self.__ignore_folders_cb = None
      self.__force_series_art_cb = None
      self.__note_scrape_date_cb = None
      self.__scrape_delay_nud = None
      self.__alt_regex_tbox = None
      self.__alt_regex_warning_label = None

      # the "add an imprint mapping" textboxes and the imprint table
      # (advanced tab)
      self.__imprint_from_tbox = None
      self.__imprint_to_tbox = None
      self.__imprint_table = None

      # the "enable manual editing" checkbox that gates the raw advanced
      # settings textbox (manual tab); always starts unchecked, and is
      # never persisted to Configuration -- it's a GUI-only safety catch
      # against accidentally editing that box.
      self.__manual_enable_cb = None

      # the UI scale slider and its "NNN%" label (appearance tab)
      self.__appearance_slider = None
      self.__appearance_pct_label = None

      # (RowStyle, height_func) pairs that __apply_scale() rescales live
      # as the appearance slider moves
      self.__scalable_rows = []

      # (ColumnStyle, button) pairs that __apply_scale() re-measures live
      # as the appearance slider moves, so each button's column always
      # matches its own text at the current font
      self.__scalable_columns = []

      # load the persisted settings up front (instead of only inside
      # show_form(), as before) so __build_gui() can size everything
      # according to the user's saved UI scale from the very first paint,
      # instead of building at 100% and immediately re-scaling.
      self.__config = Configuration()
      self.__config.load_defaults()
      self.__scale_n = self.__config.ui_scale_n

      CVForm.__init__(self, owner, "configformLocation", "configformSize")
      self.__build_gui()
          
         
          
   # ==========================================================================
   def __build_gui(self):
      ''' Constructs and initializes the gui for this form. '''

      # the form's own, un-scaled font -- __apply_scale() always computes
      # from this, never from an already-scaled self.Font, so repeated
      # calls (as the appearance slider is dragged) don't compound.
      self.__base_font = self.Font

      # 1. --- build each gui component
      self.__ok_button = self.__build_okbutton()
      self.__cancel_button = self.__build_cancel_button()
      self.__restore_button = self.__build_restore_button()
      self.__tabcontrol = self.__build_tabcontrol()


          # 2. -- create and configure the TableLayoutPanel
      self.table_layout = TableLayoutPanel()
      self.table_layout.RowCount = 2
      self.table_layout.ColumnCount = 1
      self.table_layout.Dock = DockStyle.Fill

      self.table_layout.RowStyles.Add(System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100))
      self.__add_scaled_row(self.table_layout, guistyle.button_row_height)
      self.table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Percent, 100))

      # buttons sublayout, isolated from the tabcontrol's column above --
      # each button's column is measured (and live-rescaled) from its
      # own text via __add_scaled_column(), instead of an even (and
      # easily too narrow) 3-way split.
      buttons_layout = TableLayoutPanel()
      buttons_layout.ColumnCount = 4
      buttons_layout.RowCount = 1
      # without an explicit RowStyle, this row defaults to AutoSize (fits
      # the buttons' own natural height) instead of filling the scaled
      # height given to it by the outer row -- force it to fill instead.
      buttons_layout.RowStyles.Add(System.Windows.Forms.RowStyle(
         System.Windows.Forms.SizeType.Percent, 100))
      for btn in (self.__restore_button, self.__cancel_button, self.__ok_button):
         self.__add_scaled_column(buttons_layout, btn)
      # trailing spacer column absorbs any leftover width, so the actual
      # button columns stay at their measured (not stretched) size.
      buttons_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Percent, 100))
      buttons_layout.Dock = DockStyle.Fill
      buttons_layout.Controls.Add(self.__restore_button, 0, 0)
      buttons_layout.Controls.Add(self.__cancel_button, 1, 0)
      buttons_layout.Controls.Add(self.__ok_button, 2, 0)

      self.table_layout.Controls.Add(self.__tabcontrol, 0, 0)
      self.table_layout.Controls.Add(buttons_layout, 0, 1)

      # 2. -- configure this form, and add all the gui components to it
      self.AutoScaleMode = AutoScaleMode.Font
      self.ClientSize = Size(700, 600)
      self.MinimumSize = Size(550, 450)
      self.Text = i18n.get("ConfigFormTitle")

      self.Controls.Add(self.table_layout)

      # apply the persisted UI scale (fonts + all rows registered above)
      # now that every scalable control/row actually exists.
      self.__apply_scale(self.__scale_n)

      # 3. -- define the keyboard focus tab traversal ordering
      self.__ok_button.TabIndex = 0                                        
      self.__cancel_button.TabIndex = 1                                    
      self.__restore_button.TabIndex = 2
      self.__tabcontrol.TabIndex = 3                                 

      self.__fired_update_gui()  

      
      
   # ==========================================================================
   def __add_scaled_row(self, table_layout, height_func):
      '''
      Adds an Absolute RowStyle to 'table_layout', sized by calling
      'height_func(self.Font)' -- one of guistyle's *_row_height()
      functions, which derive the height from the font itself (so the
      row always fits its text, at any scale) -- and remembers the pair
      so the Appearance tab's slider can live-rescale it later via
      __apply_scale().
      '''
      row_style = System.Windows.Forms.RowStyle(
         System.Windows.Forms.SizeType.Absolute, height_func(self.Font))
      table_layout.RowStyles.Add(row_style)
      self.__scalable_rows.append((row_style, height_func))


   # ==========================================================================
   def __add_scaled_column(self, table_layout, button):
      '''
      Adds an Absolute ColumnStyle to 'table_layout', sized to fit
      'button's own text at the current font on a single line (measured
      directly, since SizeType.AutoSize columns combined with a
      Dock=Fill button can under-measure the needed width and let the
      text silently wrap onto a second, invisible line) -- and remembers
      the pair so the Appearance tab's slider can live-rescale it later
      via __apply_scale().
      '''
      col_style = System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Absolute,
         guistyle.button_column_width(button.Text, self.Font))
      table_layout.ColumnStyles.Add(col_style)
      self.__scalable_columns.append((col_style, button))


   # ==========================================================================
   def __apply_scale(self, scale_n):
      '''
      Applies the given UI scale factor to this form's font and to every
      row/column registered via __add_scaled_row()/__add_scaled_column(),
      live -- called both when this form's Configuration is
      loaded/restored, and as the Appearance tab's slider is dragged.
      '''
      self.__scale_n = scale_n
      self.Font = guistyle.scaled_font(self.__base_font, scale_n)
      for row_style, height_func in self.__scalable_rows:
         row_style.Height = height_func(self.Font)
      for col_style, button in self.__scalable_columns:
         col_style.Width = guistyle.button_column_width(button.Text, self.Font)
      if self.__appearance_slider is not None:
         value_n = int(round(scale_n * 100))
         if self.__appearance_slider.Value != value_n:
            self.__appearance_slider.Value = value_n
         self.__appearance_pct_label.Text = "{0}%".format(value_n)


   # ==========================================================================
   def __build_okbutton(self):
      ''' builds and returns the ok button for this form '''
      
      button = Button()
      button.DialogResult = DialogResult.OK
      button.Location = Point(228, 343)
      button.Size = Size(80, 46)
      button.Text = i18n.get("ConfigFormOK")
      button.Dock = DockStyle.Fill
      return button


   
   # ==========================================================================
   def __build_restore_button(self):
      ''' builds and returns the restore button for this form '''
      
      button = Button()
      button.Click += self.__fired_restore_defaults
      button.Location = Point(10, 343)
      button.Size = Size(170, 46)
      button.Text = i18n.get("ConfigFormRestore")
      button.Dock = DockStyle.Fill
      return button


   
   # ==========================================================================
   def __build_cancel_button(self):
      ''' builds and returns the cancel button for this form '''
      
      button = Button()
      button.DialogResult = DialogResult.Cancel
      button.Location = Point(315, 343)
      button.Size = Size(90, 46)
      button.Text = i18n.get("ConfigFormCancel")
      button.Dock = DockStyle.Fill
      return button


      
   # ==========================================================================
   def __build_tabcontrol(self):
      ''' builds and returns the TabControl for this dialog '''
      
      tabcontrol = TabControl()
      tabcontrol.Location = Point(10, 15)
      tabcontrol.Size = Size(500, 400)
      tabcontrol.Dock = DockStyle.Fill
      
      tabcontrol.Controls.Add( self.__build_comicvinetab() )
      tabcontrol.Controls.Add( self.__build_detailstab() )
      tabcontrol.Controls.Add( self.__build_behaviourtab() )
      tabcontrol.Controls.Add( self.__build_datatab() )
      tabcontrol.Controls.Add( self.__build_publisherstab() )
      tabcontrol.Controls.Add( self.__build_searchfilterstab() )
      tabcontrol.Controls.Add( self.__build_publisheraliasestab() )
      tabcontrol.Controls.Add( self.__build_appearancetab() )
      tabcontrol.Controls.Add( self.__build_advancedtab() )
      tabcontrol.Controls.Add( self.__build_manualtab() )
      return tabcontrol

   
   # ==========================================================================
   def __build_comicvinetab(self):
      ''' builds and returns the "ComicVine" Tab for the TabControl '''
      
      tabpage = TabPage()
      tabpage.Text = i18n.get("ConfigFormComicVineTab")
      tabpage.Name = "comicvine"
      
      # 1. --- a description label for this tabpage
      label = Label()
      label.UseMnemonic = False
      label.AutoSize = False
      label.Dock = DockStyle.Fill
      label.Text = i18n.get("ConfigFormComicVineText")

      # 2. --- the API key text box
      fired_update_gui = self.__fired_update_gui
      class ApiKeyTextBox(TextBox):
         def OnTextChanged(self, args):
            fired_update_gui()

      self.__api_key_tbox = ApiKeyTextBox()
      tbox = self.__api_key_tbox
      tbox.Dock = DockStyle.Fill

      menu = ContextMenu()
      items = menu.MenuItems
      items.Add( MenuItem(i18n.get("TextCut"), lambda s, ea : tbox.Cut() ) )
      items.Add( MenuItem(i18n.get("TextCopy"), lambda s, ea : tbox.Copy() ) )
      items.Add( MenuItem(i18n.get("TextPaste"), lambda s, ea : tbox.Paste() ) )
      tbox.ContextMenu = menu

      # 3. --- add a clickable link to send the user to ComicVine
      linklabel = LinkLabel()
      linklabel.UseMnemonic = False
      linklabel.AutoSize = False
      linklabel.Dock = DockStyle.Fill
      linklabel.Text = i18n.get("ConfigFormComicVineClickHere")
      linklabel.LinkClicked += self.__fired_linkclicked

      # 4. --- layout: description, api key field, link, then a spacer
      table_layout = TableLayoutPanel()
      table_layout.RowCount = 4
      table_layout.ColumnCount = 1
      table_layout.Dock = DockStyle.Fill
      table_layout.Padding = System.Windows.Forms.Padding(34, 20, 34, 0)
      self.__add_scaled_row(table_layout, guistyle.header_row_height)
      self.__add_scaled_row(table_layout, guistyle.control_row_height)
      self.__add_scaled_row(table_layout, guistyle.label_row_height)
      table_layout.RowStyles.Add(System.Windows.Forms.RowStyle(
         System.Windows.Forms.SizeType.Percent, 100))
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Percent, 100))

      table_layout.Controls.Add(label, 0, 0)
      table_layout.Controls.Add(tbox, 0, 1)
      table_layout.Controls.Add(linklabel, 0, 2)

      # 5. --- add 'em all to this tabpage
      tabpage.Controls.Add(table_layout)

      return tabpage
   
   
   # ==========================================================================
   def __build_detailstab(self):
      ''' builds and returns the "Details" Tab for the TabControl '''
      
      tabpage = TabPage()
      tabpage.Text = i18n.get("ConfigFormDetailsTab")
      tabpage.Name = "details"
      
      # 1. --- a description label for this tabpage
      label = Label()
      label.UseMnemonic = False
      label.AutoSize = True
      label.Location = Point(14, 35)
      label.Size = Size(299, 17)
      label.Text = i18n.get("ConfigFormDetailsText")
      
       # Create TableLayoutPanel
      table_layout = TableLayoutPanel()
      table_layout.RowCount = 4
      table_layout.ColumnCount = 3
      table_layout.Dock = DockStyle.Fill

      self.__add_scaled_row(table_layout, guistyle.label_row_height)
      table_layout.RowStyles.Add(System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 66))
      table_layout.RowStyles.Add(System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 66))
      table_layout.RowStyles.Add(System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100))

      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 50))
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 50))
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 100))

      # 2. --- the 'select all' button
      checkall_button = Button()
      checkall_button.Click += self.__fired_checkall
      checkall_button.Location = Point(280, 107)
      checkall_button.Size = Size(100, 23)
      checkall_button.Text = i18n.get("ConfigFormDetailsAll")
      checkall_button.Dock = DockStyle.Fill
      
      # 3. --- the 'deselect all' button
      uncheckall_button = Button()
      uncheckall_button.Click += self.__fired_uncheckall
      uncheckall_button.Location = Point(280, 138)
      uncheckall_button.Size = Size(100, 23)
      uncheckall_button.Text = i18n.get("ConfigFormDetailsNone")
      uncheckall_button.Dock = DockStyle.Fill
      
      # 4. --- build the update checklist (contains all the 'data' checkboxes)
      self.__update_checklist = CheckedListBox()
      self.__update_checklist.CheckOnClick = True
      self.__update_checklist.ColumnWidth = 125
      self.__update_checklist.ThreeDCheckBoxes = True
      self.__update_checklist.Location = Point(15, 65)
      self.__update_checklist.MultiColumn = True
      self.__update_checklist.SelectionMode = SelectionMode.One
      self.__update_checklist.Size = Size(260, 170)
      self.__update_checklist.ItemCheck += self.__fired_update_gui
      self.__update_checklist.Dock = DockStyle.Fill
      
      self.__update_checklist.Items.Add(ConfigForm.__SERIES_CB)
      self.__update_checklist.Items.Add(ConfigForm.__VOLUME_CB)
      self.__update_checklist.Items.Add(ConfigForm.__NUMBER_CB)
      self.__update_checklist.Items.Add(ConfigForm.__TITLE_CB)
      self.__update_checklist.Items.Add(ConfigForm.__PUBLISHED_CB)
      self.__update_checklist.Items.Add(ConfigForm.__RELEASED_CB)
      self.__update_checklist.Items.Add(ConfigForm.__CROSSOVERS_CB)
      self.__update_checklist.Items.Add(ConfigForm.__PUBLISHER_CB)
      self.__update_checklist.Items.Add(ConfigForm.__IMPRINT_CB)
      self.__update_checklist.Items.Add(ConfigForm.__WRITER_CB)
      self.__update_checklist.Items.Add(ConfigForm.__PENCILLER_CB)
      self.__update_checklist.Items.Add(ConfigForm.__INKER_CB)
      self.__update_checklist.Items.Add(ConfigForm.__COLORIST_CB)
      self.__update_checklist.Items.Add(ConfigForm.__LETTERER_CB)
      self.__update_checklist.Items.Add(ConfigForm.__COVER_ARTIST_CB)
      self.__update_checklist.Items.Add(ConfigForm.__EDITOR_CB)
      self.__update_checklist.Items.Add(ConfigForm.__SUMMARY_CB)
      self.__update_checklist.Items.Add(ConfigForm.__CHARACTERS_CB)
      self.__update_checklist.Items.Add(ConfigForm.__TEAMS_CB)
      self.__update_checklist.Items.Add(ConfigForm.__LOCATIONS_CB)     
      self.__update_checklist.Items.Add(ConfigForm.__WEBPAGE_CB)
   
      # 5. --- add 'em all to this tabpage
      tabpage.Controls.Add(table_layout)

      table_layout.Controls.Add(label, 0, 0)
      table_layout.SetColumnSpan(label, 3)
      table_layout.Controls.Add(self.__update_checklist, 0, 1)
      table_layout.SetColumnSpan(self.__update_checklist, 2)
      table_layout.SetRowSpan(self.__update_checklist, 3)
      table_layout.Controls.Add(checkall_button, 2, 1)
      table_layout.Controls.Add(uncheckall_button, 2, 2)
      '''
      table_layout.Controls.Add(label)
      table_layout.Controls.Add(checkall_button)
      table_layout.Controls.Add(uncheckall_button)
      table_layout.Controls.Add(self.__update_checklist)
      '''

      return tabpage

   
   
   # ==========================================================================
   def __build_behaviourtab(self):
      ''' builds and returns the "Behaviour" Tab for the TabControl '''
      
      tabpage = TabPage()
      tabpage.Text = i18n.get("ConfigFormBehaviourTab")
      
      # Create TableLayoutPanel
      table_layout = TableLayoutPanel()
      table_layout.RowCount = 8
      table_layout.ColumnCount = 2
      table_layout.Dock = DockStyle.Fill
      
      for _ in range(7):
         self.__add_scaled_row(table_layout, guistyle.control_row_height)
      table_layout.RowStyles.Add(System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100))

      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 60))
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 100))

      # 1. --- build the 'When scraping for the first time' label
      first_scrape_label = Label()
      first_scrape_label.AutoSize = False
      first_scrape_label.FlatStyle = FlatStyle.System
      first_scrape_label.Location = Point(52, 27)
      first_scrape_label.Text = i18n.get("ConfigFormFirstScrapeLabel")
      first_scrape_label.Size = Size(300, 17)
      first_scrape_label.Dock = DockStyle.Fill
      first_scrape_label.TextAlign = ContentAlignment.BottomLeft

      # 1. --- build the 'autochoose series' checkbox
      self.__autochoose_series_cb = CheckBox()
      #self.__autochoose_series_cb.AutoSize = False
      self.__autochoose_series_cb.FlatStyle = FlatStyle.System
      self.__autochoose_series_cb.Location = Point(82, 45)
      self.__autochoose_series_cb.Size = Size(300, 34)
      self.__autochoose_series_cb.Text = "     "+i18n.get("ConfigFormAutochooseSeriesCB")
      self.__autochoose_series_cb.CheckedChanged += self.__fired_update_gui
      self.__autochoose_series_cb.Dock = DockStyle.Fill

      # 2. --- build the 'confirm issue' checkbox
      self.__confirm_issue_cb = CheckBox()
      #self.__confirm_issue_cb.AutoSize = False
      self.__confirm_issue_cb.FlatStyle = FlatStyle.System
      self.__confirm_issue_cb.Location = Point(82, 75)
      self.__confirm_issue_cb.Size = Size(300, 34)
      self.__confirm_issue_cb.Text = "     "+ i18n.get("ConfigFormConfirmIssueCB")
      self.__confirm_issue_cb.CheckedChanged += self.__fired_update_gui
      self.__confirm_issue_cb.Dock = DockStyle.Fill

      # 3. -- build the 'use fast rescrape' checkbox
      self.__fast_rescrape_cb = CheckBox()
      #self.__fast_rescrape_cb.AutoSize = False
      self.__fast_rescrape_cb.FlatStyle = FlatStyle.System
      self.__fast_rescrape_cb.Location = Point(52, 116)
      self.__fast_rescrape_cb.Size = Size(300, 34)
      self.__fast_rescrape_cb.Text = i18n.get("ConfigFormRescrapeCB")
      self.__fast_rescrape_cb.CheckedChanged += self.__fired_update_gui
      self.__fast_rescrape_cb.Dock = DockStyle.Fill

      # 4. -- build the 'add rescrape hints to notes' checkbox
      self.__rescrape_notes_cb = CheckBox()
      #self.__rescrape_notes_cb.AutoSize = False
      self.__rescrape_notes_cb.FlatStyle = FlatStyle.System
      self.__rescrape_notes_cb.Location = Point(82, 151)
      self.__rescrape_notes_cb.Size = Size(270, 17)
      self.__rescrape_notes_cb.Text = "     "+ i18n.get("ConfigFormRescrapeNotesCB")
      self.__rescrape_notes_cb.CheckedChanged += self.__fired_update_gui
      self.__rescrape_notes_cb.Dock = DockStyle.Fill

      # 5. -- build the 'add rescrape hints to tags' checkbox
      self.__rescrape_tags_cb = CheckBox()
      #self.__rescrape_tags_cb.AutoSize = False
      self.__rescrape_tags_cb.FlatStyle = FlatStyle.System
      self.__rescrape_tags_cb.Location = Point(82, 181)
      self.__rescrape_tags_cb.Size = Size(270, 17)
      self.__rescrape_tags_cb.Text = "     "+ i18n.get("ConfigFormRescrapeTagsCB")
      self.__rescrape_tags_cb.CheckedChanged += self.__fired_update_gui 
      self.__rescrape_tags_cb.Dock = DockStyle.Fill

      # 6. --- build the 'specify series name' checkbox
      self.__summary_dialog_cb = CheckBox()
      #self.__summary_dialog_cb.AutoSize = False
      self.__summary_dialog_cb.FlatStyle = FlatStyle.System
      self.__summary_dialog_cb.Location = Point(52, 214)
      self.__summary_dialog_cb.Size = Size(300, 34)
      self.__summary_dialog_cb.Text = i18n.get("ConfigFormShowSummaryCB")
      self.__summary_dialog_cb.CheckedChanged += self.__fired_update_gui 
      self.__summary_dialog_cb.Dock = DockStyle.Fill

      # 7. --- add 'em all to the tabpage 
      table_layout.Controls.Add(first_scrape_label,0,0)
      table_layout.SetColumnSpan(first_scrape_label, 2)
      table_layout.Controls.Add(self.__autochoose_series_cb,1,1)
      table_layout.Controls.Add(self.__confirm_issue_cb,1,2)
      table_layout.Controls.Add(self.__fast_rescrape_cb,0,3)
      table_layout.SetColumnSpan(self.__fast_rescrape_cb, 2)
      table_layout.Controls.Add(self.__rescrape_tags_cb,1,4)
      table_layout.Controls.Add(self.__rescrape_notes_cb,1,5)
      table_layout.Controls.Add(self.__summary_dialog_cb,0,6)
      table_layout.SetColumnSpan(self.__summary_dialog_cb, 2)
      
      tabpage.Controls.Add(table_layout)

      return tabpage
   
   
   
   # ==========================================================================
   def __build_datatab(self):
      ''' builds and returns the "Data" Tab for the TabControl '''
      
      tabpage = TabPage()
      tabpage.Text = i18n.get("ConfigFormDataTab")
      
      # Create TableLayoutPanel
      table_layout = TableLayoutPanel()
      table_layout.RowCount = 6
      table_layout.ColumnCount = 2
      table_layout.Dock = DockStyle.Fill
      
      for _ in range(5):
         self.__add_scaled_row(table_layout, guistyle.control_row_height)
      table_layout.RowStyles.Add(System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100))

      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 60))
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 100))

      # 1. --- build the 'convert imprints checkbox'
      self.__convert_imprints_cb = CheckBox()
      #self.__convert_imprints_cb.AutoSize = False
      self.__convert_imprints_cb.FlatStyle = FlatStyle.System
      self.__convert_imprints_cb.Location = Point(52, 35)
      self.__convert_imprints_cb.Size = Size(300, 34)
      self.__convert_imprints_cb.Text = i18n.get("ConfigFormImprintsCB")
      self.__convert_imprints_cb.CheckedChanged += self.__fired_update_gui
      self.__convert_imprints_cb.Dock = DockStyle.Fill
       
      # 2. -- build the 'overwrite existing' checkbox
      self.__ow_existing_cb = CheckBox()
      #self.__ow_existing_cb.AutoSize = False
      self.__ow_existing_cb.FlatStyle = FlatStyle.System
      self.__ow_existing_cb.Location = Point(52, 85)
      self.__ow_existing_cb.Size = Size(310, 34)
      self.__ow_existing_cb.Text = i18n.get("ConfigFormOverwriteCB")
      self.__ow_existing_cb.CheckedChanged += self.__fired_update_gui 
      self.__ow_existing_cb.Dock = DockStyle.Fill
   
      # 3. --- build the 'ignore blanks' checkbox
      self.__ignore_blanks_cb = CheckBox()                                          
      #self.__ignore_blanks_cb.AutoSize = False                                       
      self.__ignore_blanks_cb.FlatStyle = FlatStyle.System                          
      self.__ignore_blanks_cb.Location = Point(82, 125)                             
      self.__ignore_blanks_cb.Size = Size(270, 34)                                  
      self.__ignore_blanks_cb.TextAlign = ContentAlignment.TopLeft                                  
      self.__ignore_blanks_cb.Text = i18n.get("ConfigFormOverwriteEmptyCB")                  
      self.__ignore_blanks_cb.CheckedChanged += self.__fired_update_gui
      self.__ignore_blanks_cb.Dock = DockStyle.Fill
   
      # 4. --- build the 'download thumbnails' checkbox
      self.__download_thumbs_cb = CheckBox()
      #self.__download_thumbs_cb.AutoSize = False
      self.__download_thumbs_cb.FlatStyle = FlatStyle.System
      self.__download_thumbs_cb.Location = Point(52, 165)
      self.__download_thumbs_cb.Size = Size(300, 34)
      self.__download_thumbs_cb.Text = i18n.get("ConfigFormFilelessCB")
      self.__download_thumbs_cb.CheckedChanged += self.__fired_update_gui
      self.__download_thumbs_cb.Dock = DockStyle.Fill
      
      # 5. --- build the 'preserve thumbnails' checkbox
      self.__preserve_thumbs_cb = CheckBox()
      #self.__preserve_thumbs_cb.AutoSize = False
      self.__preserve_thumbs_cb.FlatStyle = FlatStyle.System
      self.__preserve_thumbs_cb.Location = Point(82, 205)
      self.__preserve_thumbs_cb.Size = Size(270, 34)
      self.__preserve_thumbs_cb.TextAlign = ContentAlignment.TopLeft
      self.__preserve_thumbs_cb.Text = i18n.get("ConfigFormFilelessOverwriteCB")
      self.__preserve_thumbs_cb.CheckedChanged += self.__fired_update_gui
      self.__preserve_thumbs_cb.Dock = DockStyle.Fill
            
      # 6. --- add 'em all to the tabpage 

      tabpage.Controls.Add(table_layout)

      table_layout.Controls.Add(self.__ow_existing_cb,0,0)
      table_layout.SetColumnSpan(self.__ow_existing_cb, 2)
      table_layout.Controls.Add(self.__ignore_blanks_cb,1,1)
      table_layout.Controls.Add(self.__convert_imprints_cb,0,2)
      table_layout.SetColumnSpan(self.__convert_imprints_cb, 2)
      table_layout.Controls.Add(self.__download_thumbs_cb,0,3)
      table_layout.SetColumnSpan(self.__download_thumbs_cb, 2)
      table_layout.Controls.Add(self.__preserve_thumbs_cb,1,4)
      
      return tabpage
  
  
   # ==========================================================================
   def __build_publisherstab(self):
      ''' builds and returns the "Publishers" Tab for the TabControl '''

      tabpage = TabPage()
      tabpage.Text = i18n.get("ConfigFormPublishersTab")

      # 1. --- a description label for this tabpage
      label = Label()
      label.UseMnemonic = False
      label.AutoSize = True
      label.Dock = DockStyle.Fill
      label.Text = i18n.get("ConfigFormPublishersText")

      # 2. --- the "pick or type a publisher" combobox; its dropdown list is
      #    populated organically (see configuration.record_known_publisher)
      #    from publishers actually seen in past series searches -- it is
      #    NOT a bulk download of Comic Vine's entire publisher catalog.
      #    the user can still type any name freehand, even if the list
      #    is empty (e.g. nothing has been scraped yet).
      add_button = self.__build_publisher_addbutton()
      class PublisherComboBox(ComboBox):
         def OnKeyPress(self, args):
            if args.KeyChar == chr(13):
               add_button.PerformClick()
               args.Handled = True
            else:
               ComboBox.OnKeyPress(self, args)
      cbox = PublisherComboBox()
      cbox.DropDownStyle = ComboBoxStyle.DropDown # editable text + dropdown
      cbox.Dock = DockStyle.Fill
      for publisher_s in load_known_publishers_sl():
         cbox.Items.Add(publisher_s)
      self.__publisher_combobox = cbox
      self.__publisher_add_button = add_button

      # 3. --- the table of currently-ignored publishers
      self.__publisher_table = self.__build_publisher_table()

      # 4. --- layout: description on top, combobox+add button below it,
      #    and the ignore-list table filling the rest
      table_layout = TableLayoutPanel()
      table_layout.RowCount = 3
      table_layout.ColumnCount = 2
      table_layout.Dock = DockStyle.Fill
      self.__add_scaled_row(table_layout, guistyle.label_row_height)
      self.__add_scaled_row(table_layout, guistyle.control_row_height)
      table_layout.RowStyles.Add(System.Windows.Forms.RowStyle(
         System.Windows.Forms.SizeType.Percent, 100))
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Percent, 100))
      self.__add_scaled_column(table_layout, add_button)

      table_layout.Controls.Add(label, 0, 0)
      table_layout.SetColumnSpan(label, 2)
      table_layout.Controls.Add(cbox, 0, 1)
      table_layout.Controls.Add(add_button, 1, 1)
      table_layout.Controls.Add(self.__publisher_table, 0, 2)
      table_layout.SetColumnSpan(self.__publisher_table, 2)

      tabpage.Controls.Add(table_layout)
      return tabpage


   # ==========================================================================
   def __build_publisher_addbutton(self):
      ''' builds and returns the "add publisher to ignore list" button '''

      button = Button()
      button.Click += self.__fired_add_publisher
      button.Text = i18n.get("ConfigFormPublishersAdd")
      button.Dock = DockStyle.Fill
      return button


   # ==========================================================================
   def __build_publisher_table(self):
      ''' builds and returns the table listing all currently-ignored
      publishers, each row with a "Remove" button. '''

      table = DataGridView()
      table.AllowUserToAddRows = False
      table.AllowUserToResizeRows = False
      table.RowHeadersVisible = False
      table.ReadOnly = True
      table.SelectionMode = DataGridViewSelectionMode.FullRowSelect
      table.MultiSelect = False
      table.Dock = DockStyle.Fill
      table.ColumnHeadersHeightSizeMode = \
         DataGridViewColumnHeadersHeightSizeMode.AutoSize
      table.ColumnCount = 2
      table.Columns[0].Name = i18n.get("ConfigFormPublishersCol")
      table.Columns[0].DefaultCellStyle.Alignment = \
         DataGridViewContentAlignment.MiddleLeft
      table.Columns[0].AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill

      remove_col = DataGridViewButtonColumn()
      remove_col.Text = i18n.get("ConfigFormPublishersRemove")
      remove_col.UseColumnTextForButtonValue = True
      remove_col.Width = guistyle.scale(90, self.__scale_n)
      table.Columns.RemoveAt(1)
      table.Columns.Add(remove_col)

      table.CellContentClick += self.__fired_remove_publisher
      return table


   # ==========================================================================
   def __fired_add_publisher(self, sender, args):
      ''' called when the user clicks the "add publisher" button; adds the
      combobox's current text to the ignore-list table, unless it's blank
      or (case-insensitively) already in that table. '''

      publisher_s = self.__publisher_combobox.Text.strip()
      if not publisher_s:
         return
      for row in self.__publisher_table.Rows:
         if sstr(row.Cells[0].Value).lower() == publisher_s.lower():
            return # already in the list -- don't add a duplicate
      self.__publisher_table.Rows.Add(publisher_s, None)
      self.__publisher_combobox.Text = ""


   # ==========================================================================
   def __fired_remove_publisher(self, sender, args):
      ''' called when the user clicks a "Remove" button in the ignore-list
      table; removes that row from the table. '''

      if args.RowIndex >= 0 and args.ColumnIndex == 1:
         self.__publisher_table.Rows.RemoveAt(args.RowIndex)


   # ==========================================================================
   def __build_info_button(self, info_text_key):
      ''' builds and returns a small "(i)" button that, when clicked, pops
      a MessageBox explaining every control on the tab it's placed on
      (text taken from the i18n key 'info_text_key'). '''

      button = Button()
      button.Text = i18n.get("ConfigFormInfoButton")
      button.Dock = DockStyle.Fill
      button.Click += lambda sender, args: MessageBox.Show(self,
         i18n.get(info_text_key), i18n.get("ConfigFormInfoTitle"),
         MessageBoxButtons.OK, MessageBoxIcon.Information)
      return button


   # ==========================================================================
   def __build_named_list_editor(self, col_header_i18n_key):
      '''
      Builds and returns (combobox, add_button, table) for a single-column
      "type freeform text, click Add, remove via a per-row button" editor
      -- the same shape as the ignore-list on the Publishers tab (see
      __build_publisherstab), generalized here so it can be reused for
      other single-column lists (see also __build_map_list_editor, for
      two-column name->value lists). The caller is responsible for wiring
      up 'add_button's Click handler and for storing the returned
      combobox/table on self.
      '''

      add_button = Button()
      add_button.Text = i18n.get("ConfigFormPublishersAdd")
      add_button.Dock = DockStyle.Fill

      class ListComboBox(ComboBox):
         def OnKeyPress(self, args):
            if args.KeyChar == chr(13):
               add_button.PerformClick()
               args.Handled = True
            else:
               ComboBox.OnKeyPress(self, args)
      cbox = ListComboBox()
      cbox.DropDownStyle = ComboBoxStyle.DropDown
      cbox.Dock = DockStyle.Fill

      table = DataGridView()
      table.AllowUserToAddRows = False
      table.AllowUserToResizeRows = False
      table.RowHeadersVisible = False
      table.ReadOnly = True
      table.SelectionMode = DataGridViewSelectionMode.FullRowSelect
      table.MultiSelect = False
      table.Dock = DockStyle.Fill
      table.ColumnHeadersHeightSizeMode = \
         DataGridViewColumnHeadersHeightSizeMode.AutoSize
      table.ColumnCount = 2
      table.Columns[0].Name = i18n.get(col_header_i18n_key)
      table.Columns[0].DefaultCellStyle.Alignment = \
         DataGridViewContentAlignment.MiddleLeft
      table.Columns[0].AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill

      remove_col = DataGridViewButtonColumn()
      remove_col.Text = i18n.get("ConfigFormPublishersRemove")
      remove_col.UseColumnTextForButtonValue = True
      remove_col.Width = guistyle.scale(90, self.__scale_n)
      table.Columns.RemoveAt(1)
      table.Columns.Add(remove_col)

      table.CellContentClick += self.__fired_remove_list_row
      return cbox, add_button, table


   # ==========================================================================
   def __build_map_list_editor(self, from_col_i18n_key, to_col_i18n_key):
      '''
      Builds and returns (from_tbox, to_tbox, add_button, table) for a
      two-column name->value editor (Publisher Aliases, Imprints): two
      freeform textboxes plus an Add button feed a table with a per-row
      Remove button. The caller is responsible for wiring up 'add_button's
      Click handler and for storing the returned textboxes/table on self.
      '''

      add_button = Button()
      add_button.Text = i18n.get("ConfigFormPublishersAdd")
      add_button.Dock = DockStyle.Fill

      from_tbox = TextBox()
      from_tbox.MaxLength = 50
      from_tbox.Dock = DockStyle.Fill
      to_tbox = TextBox()
      to_tbox.MaxLength = 50
      to_tbox.Dock = DockStyle.Fill

      table = DataGridView()
      table.AllowUserToAddRows = False
      table.AllowUserToResizeRows = False
      table.RowHeadersVisible = False
      table.ReadOnly = True
      table.SelectionMode = DataGridViewSelectionMode.FullRowSelect
      table.MultiSelect = False
      table.Dock = DockStyle.Fill
      table.ColumnHeadersHeightSizeMode = \
         DataGridViewColumnHeadersHeightSizeMode.AutoSize
      table.ColumnCount = 3
      table.Columns[0].Name = i18n.get(from_col_i18n_key)
      table.Columns[0].DefaultCellStyle.Alignment = \
         DataGridViewContentAlignment.MiddleLeft
      table.Columns[0].AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill
      table.Columns[1].Name = i18n.get(to_col_i18n_key)
      table.Columns[1].DefaultCellStyle.Alignment = \
         DataGridViewContentAlignment.MiddleLeft
      table.Columns[1].AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill

      remove_col = DataGridViewButtonColumn()
      remove_col.Text = i18n.get("ConfigFormPublishersRemove")
      remove_col.UseColumnTextForButtonValue = True
      remove_col.Width = guistyle.scale(90, self.__scale_n)
      table.Columns.RemoveAt(2)
      table.Columns.Add(remove_col)

      table.CellContentClick += self.__fired_remove_list_row
      return from_tbox, to_tbox, add_button, table


   # ==========================================================================
   def __fired_remove_list_row(self, sender, args):
      ''' called when the user clicks a "Remove" button in any of the
      search-terms/publisher-aliases/imprints list editors; 'sender' is
      the DataGridView itself, and the Remove button is always its last
      column, regardless of whether the table has 1 or 2 data columns. '''

      if args.RowIndex >= 0 and args.ColumnIndex == sender.ColumnCount - 1:
         sender.Rows.RemoveAt(args.RowIndex)


   # ==========================================================================
   def __fired_add_searchterm(self, sender, args):
      ''' called when the user clicks the "add search term" button; adds
      the combobox's current text to the ignore-list table, unless it's
      blank, not a single alphanumeric word (matching configuration.py's
      own acceptance rule for IGNORE_SEARCHTERM), or already in the
      table. '''

      term_s = self.__searchterm_combobox.Text.strip()
      if not term_s:
         return
      if not term_s.isalnum():
         MessageBox.Show(self, i18n.get("ConfigFormSearchTermsInvalid"),
            i18n.get("ConfigFormInfoTitle"), MessageBoxButtons.OK,
            MessageBoxIcon.Warning)
         return
      term_lower_s = term_s.lower()
      for row in self.__searchterm_table.Rows:
         if sstr(row.Cells[0].Value).lower() == term_lower_s:
            return # already in the list -- don't add a duplicate
      self.__searchterm_table.Rows.Add(term_s, None)
      self.__searchterm_combobox.Text = ""


   # ==========================================================================
   def __fired_add_alias(self, sender, args):
      ''' called when the user clicks the "add publisher alias" button;
      adds the current publisher/alias textbox values as a new row, unless
      either is blank or the publisher is already mapped. '''

      from_s = self.__alias_from_tbox.Text.strip()
      to_s = self.__alias_to_tbox.Text.strip()
      if not from_s or not to_s:
         return
      from_lower_s = from_s.lower()
      for row in self.__alias_table.Rows:
         if sstr(row.Cells[0].Value).lower() == from_lower_s:
            return # already mapped -- don't add a duplicate
      self.__alias_table.Rows.Add(from_s, to_s, None)
      self.__alias_from_tbox.Text = ""
      self.__alias_to_tbox.Text = ""


   # ==========================================================================
   def __fired_add_imprint(self, sender, args):
      ''' called when the user clicks the "add imprint mapping" button;
      adds the current imprint/publisher textbox values as a new row,
      unless either is blank or the imprint is already mapped. '''

      from_s = self.__imprint_from_tbox.Text.strip()
      to_s = self.__imprint_to_tbox.Text.strip()
      if not from_s or not to_s:
         return
      from_lower_s = from_s.lower()
      for row in self.__imprint_table.Rows:
         if sstr(row.Cells[0].Value).lower() == from_lower_s:
            return # already mapped -- don't add a duplicate
      self.__imprint_table.Rows.Add(from_s, to_s, None)
      self.__imprint_from_tbox.Text = ""
      self.__imprint_to_tbox.Text = ""


   # ==========================================================================
   def __build_searchfilterstab(self):
      ''' builds and returns the "Search Filters" Tab for the TabControl '''

      tabpage = TabPage()
      tabpage.Text = i18n.get("ConfigFormSearchFiltersTab")

      table_layout = TableLayoutPanel()
      table_layout.RowCount = 8
      table_layout.ColumnCount = 2
      table_layout.Dock = DockStyle.Fill
      self.__add_scaled_row(table_layout, guistyle.header_row_height)
      self.__add_scaled_row(table_layout, guistyle.label_row_height)
      self.__add_scaled_row(table_layout, guistyle.control_row_height)
      self.__add_scaled_row(table_layout,
         lambda font: guistyle.control_row_height(font) * 4)
      self.__add_scaled_row(table_layout, guistyle.control_row_height)
      self.__add_scaled_row(table_layout, guistyle.control_row_height)
      self.__add_scaled_row(table_layout, guistyle.control_row_height)
      self.__add_scaled_row(table_layout, guistyle.control_row_height)
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Percent, 100))
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Absolute,
         guistyle.scale(90, self.__scale_n)))

      # 1. --- description label + info button
      label = Label()
      label.UseMnemonic = False
      label.AutoSize = False
      label.Dock = DockStyle.Fill
      label.Text = i18n.get("ConfigFormSearchFiltersText")
      info_button = self.__build_info_button("ConfigFormSearchFiltersInfoText")

      # 2. --- ignored search terms section
      terms_label = Label()
      terms_label.UseMnemonic = False
      terms_label.AutoSize = False
      terms_label.Dock = DockStyle.Fill
      terms_label.Text = i18n.get("ConfigFormSearchTermsLabel")

      cbox, add_button, table = \
         self.__build_named_list_editor("ConfigFormSearchTermsCol")
      add_button.Click += self.__fired_add_searchterm
      self.__searchterm_combobox = cbox
      self.__searchterm_table = table

      # 3. --- before/after year, never-ignore threshold, max results
      self.__before_year_cb = CheckBox()
      self.__before_year_cb.FlatStyle = FlatStyle.System
      self.__before_year_cb.Text = i18n.get("ConfigFormIgnoreBeforeYearCB")
      self.__before_year_cb.Dock = DockStyle.Fill
      self.__before_year_cb.CheckedChanged += self.__fired_update_gui
      self.__before_year_nud = NumericUpDown()
      self.__before_year_nud.Minimum = 1
      self.__before_year_nud.Maximum = 9999
      self.__before_year_nud.Dock = DockStyle.Fill

      self.__after_year_cb = CheckBox()
      self.__after_year_cb.FlatStyle = FlatStyle.System
      self.__after_year_cb.Text = i18n.get("ConfigFormIgnoreAfterYearCB")
      self.__after_year_cb.Dock = DockStyle.Fill
      self.__after_year_cb.CheckedChanged += self.__fired_update_gui
      self.__after_year_nud = NumericUpDown()
      self.__after_year_nud.Minimum = 1
      self.__after_year_nud.Maximum = 9999
      self.__after_year_nud.Dock = DockStyle.Fill

      self.__threshold_cb = CheckBox()
      self.__threshold_cb.FlatStyle = FlatStyle.System
      self.__threshold_cb.Text = i18n.get("ConfigFormNeverIgnoreThresholdCB")
      self.__threshold_cb.Dock = DockStyle.Fill
      self.__threshold_cb.CheckedChanged += self.__fired_update_gui
      self.__threshold_nud = NumericUpDown()
      self.__threshold_nud.Minimum = 1
      self.__threshold_nud.Maximum = 999999
      self.__threshold_nud.Dock = DockStyle.Fill

      maxresults_label = Label()
      maxresults_label.UseMnemonic = False
      maxresults_label.AutoSize = False
      maxresults_label.Dock = DockStyle.Fill
      maxresults_label.TextAlign = ContentAlignment.MiddleLeft
      maxresults_label.Text = i18n.get("ConfigFormMaxSearchResultsLabel")
      self.__max_results_nud = NumericUpDown()
      self.__max_results_nud.Minimum = 10
      self.__max_results_nud.Maximum = 5000
      self.__max_results_nud.Dock = DockStyle.Fill

      # 4. --- add 'em all to the tabpage
      table_layout.Controls.Add(label, 0, 0)
      table_layout.Controls.Add(info_button, 1, 0)
      table_layout.Controls.Add(terms_label, 0, 1)
      table_layout.SetColumnSpan(terms_label, 2)
      table_layout.Controls.Add(cbox, 0, 2)
      table_layout.Controls.Add(add_button, 1, 2)
      table_layout.Controls.Add(table, 0, 3)
      table_layout.SetColumnSpan(table, 2)
      table_layout.Controls.Add(self.__before_year_cb, 0, 4)
      table_layout.Controls.Add(self.__before_year_nud, 1, 4)
      table_layout.Controls.Add(self.__after_year_cb, 0, 5)
      table_layout.Controls.Add(self.__after_year_nud, 1, 5)
      table_layout.Controls.Add(self.__threshold_cb, 0, 6)
      table_layout.Controls.Add(self.__threshold_nud, 1, 6)
      table_layout.Controls.Add(maxresults_label, 0, 7)
      table_layout.Controls.Add(self.__max_results_nud, 1, 7)

      tabpage.Controls.Add(table_layout)
      return tabpage


   # ==========================================================================
   def __build_publisheraliasestab(self):
      ''' builds and returns the "Publisher Aliases" Tab for the
      TabControl '''

      tabpage = TabPage()
      tabpage.Text = i18n.get("ConfigFormPublisherAliasesTab")

      label = Label()
      label.UseMnemonic = False
      label.AutoSize = False
      label.Dock = DockStyle.Fill
      label.Text = i18n.get("ConfigFormPublisherAliasesText")

      from_label = Label()
      from_label.UseMnemonic = False
      from_label.AutoSize = False
      from_label.Dock = DockStyle.Fill
      from_label.TextAlign = ContentAlignment.MiddleLeft
      from_label.Text = i18n.get("ConfigFormAliasFromLabel")

      to_label = Label()
      to_label.UseMnemonic = False
      to_label.AutoSize = False
      to_label.Dock = DockStyle.Fill
      to_label.TextAlign = ContentAlignment.MiddleLeft
      to_label.Text = i18n.get("ConfigFormAliasToLabel")

      from_tbox, to_tbox, add_button, table = self.__build_map_list_editor(
         "ConfigFormAliasFromCol", "ConfigFormAliasToCol")
      add_button.Click += self.__fired_add_alias
      self.__alias_from_tbox = from_tbox
      self.__alias_to_tbox = to_tbox
      self.__alias_table = table

      table_layout = TableLayoutPanel()
      table_layout.RowCount = 4
      table_layout.ColumnCount = 3
      table_layout.Dock = DockStyle.Fill
      self.__add_scaled_row(table_layout, guistyle.header_row_height)
      self.__add_scaled_row(table_layout, guistyle.label_row_height)
      self.__add_scaled_row(table_layout, guistyle.control_row_height)
      table_layout.RowStyles.Add(System.Windows.Forms.RowStyle(
         System.Windows.Forms.SizeType.Percent, 100))
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Percent, 50))
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Percent, 50))
      self.__add_scaled_column(table_layout, add_button)

      table_layout.Controls.Add(label, 0, 0)
      table_layout.SetColumnSpan(label, 3)
      table_layout.Controls.Add(from_label, 0, 1)
      table_layout.Controls.Add(to_label, 1, 1)
      table_layout.Controls.Add(from_tbox, 0, 2)
      table_layout.Controls.Add(to_tbox, 1, 2)
      table_layout.Controls.Add(add_button, 2, 2)
      table_layout.Controls.Add(table, 0, 3)
      table_layout.SetColumnSpan(table, 3)

      tabpage.Controls.Add(table_layout)
      return tabpage


   # ==========================================================================
   def __build_appearancetab(self):
      ''' builds and returns the "Appearance" Tab for the TabControl '''

      tabpage = TabPage()
      tabpage.Text = i18n.get("ConfigFormAppearanceTab")

      # 1. --- a description label for this tabpage
      label = Label()
      label.UseMnemonic = False
      label.AutoSize = True
      label.Dock = DockStyle.Fill
      label.Text = i18n.get("ConfigFormAppearanceText")

      # 2. --- the UI scale slider, plus a "NNN%" label showing its value
      slider = TrackBar()
      slider.Minimum = int(Configuration.MIN_UI_SCALE_N * 100)
      slider.Maximum = int(Configuration.MAX_UI_SCALE_N * 100)
      step_n = int(round(Configuration.UI_SCALE_STEP_N * 100))
      slider.TickFrequency = step_n
      slider.SmallChange = step_n
      slider.LargeChange = step_n
      slider.TickStyle = TickStyle.BottomRight
      slider.Dock = DockStyle.Fill
      slider.ValueChanged += self.__fired_scale_changed
      self.__appearance_slider = slider

      pct_label = Label()
      pct_label.UseMnemonic = False
      pct_label.AutoSize = False
      pct_label.TextAlign = ContentAlignment.MiddleCenter
      pct_label.Dock = DockStyle.Fill
      self.__appearance_pct_label = pct_label

      # 3. --- layout
      table_layout = TableLayoutPanel()
      table_layout.RowCount = 2
      table_layout.ColumnCount = 2
      table_layout.Dock = DockStyle.Fill
      self.__add_scaled_row(table_layout, lambda font: guistyle.label_row_height(font) * 2)
      self.__add_scaled_row(table_layout, guistyle.control_row_height)
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Percent, 100))
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Absolute, 60))

      table_layout.Controls.Add(label, 0, 0)
      table_layout.SetColumnSpan(label, 2)
      table_layout.Controls.Add(slider, 0, 1)
      table_layout.Controls.Add(pct_label, 1, 1)

      tabpage.Controls.Add(table_layout)
      return tabpage


   # ==========================================================================
   def __fired_scale_changed(self, sender, args):
      ''' called live, as the user drags the Appearance tab's UI scale
      slider -- immediately re-scales this form's own fonts and rows, as
      a live preview of what every other dialog will look like too. '''
      self.__apply_scale(self.__appearance_slider.Value / 100.0)


   # ==========================================================================
   def __build_advancedtab(self):
      ''' builds and returns the "Advanced" Tab for the TabControl '''

      tabpage = TabPage()
      tabpage.Text = i18n.get("ConfigFormAdvancedTab")

      table_layout = TableLayoutPanel()
      table_layout.RowCount = 15
      table_layout.ColumnCount = 3
      table_layout.Dock = DockStyle.Fill
      self.__add_scaled_row(table_layout, guistyle.header_row_height) # 0
      for _ in range(6):
         self.__add_scaled_row(table_layout, guistyle.control_row_height) # 1-6
      self.__add_scaled_row(table_layout, guistyle.control_row_height) # 7
      self.__add_scaled_row(table_layout, guistyle.label_row_height) # 8
      self.__add_scaled_row(table_layout, guistyle.control_row_height) # 9
      self.__add_scaled_row(table_layout, guistyle.label_row_height) # 10
      self.__add_scaled_row(table_layout, guistyle.header_row_height) # 11
      self.__add_scaled_row(table_layout, guistyle.label_row_height) # 12
      self.__add_scaled_row(table_layout, guistyle.control_row_height) # 13
      self.__add_scaled_row(table_layout,
         lambda font: guistyle.control_row_height(font) * 4) # 14
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Percent, 50))
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Percent, 50))
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Absolute,
         guistyle.scale(90, self.__scale_n)))

      # 1. --- description label + info button
      label = Label()
      label.UseMnemonic = False
      label.AutoSize = False
      label.Dock = DockStyle.Fill
      label.Text = i18n.get("ConfigFormAdvancedText")
      info_button = self.__build_info_button("ConfigFormAdvancedInfoText")

      # 2. --- the six behavior checkboxes
      def build_cb(text_key):
         cb = CheckBox()
         cb.FlatStyle = FlatStyle.System
         cb.Text = i18n.get(text_key)
         cb.Dock = DockStyle.Fill
         cb.CheckedChanged += self.__fired_update_gui
         return cb

      self.__rating_cb = build_cb("ConfigFormRatingCB")
      self.__show_covers_cb = build_cb("ConfigFormShowCoversCB")
      self.__welcome_dialog_cb = build_cb("ConfigFormWelcomeDialogCB")
      self.__ignore_folders_cb = build_cb("ConfigFormIgnoreFoldersCB")
      self.__force_series_art_cb = build_cb("ConfigFormForceSeriesArtCB")
      self.__note_scrape_date_cb = build_cb("ConfigFormNoteScrapeDateCB")

      # 3. --- scrape delay
      scrapedelay_label = Label()
      scrapedelay_label.UseMnemonic = False
      scrapedelay_label.AutoSize = False
      scrapedelay_label.Dock = DockStyle.Fill
      scrapedelay_label.TextAlign = ContentAlignment.MiddleLeft
      scrapedelay_label.Text = i18n.get("ConfigFormScrapeDelayLabel")
      self.__scrape_delay_nud = NumericUpDown()
      self.__scrape_delay_nud.Minimum = 2 # configuration.py enforces this floor
      self.__scrape_delay_nud.Maximum = 3600
      self.__scrape_delay_nud.Dock = DockStyle.Fill

      # 4. --- alternate filename search regex
      altregex_label = Label()
      altregex_label.UseMnemonic = False
      altregex_label.AutoSize = False
      altregex_label.Dock = DockStyle.Fill
      altregex_label.Text = i18n.get("ConfigFormAltRegexLabel")
      self.__alt_regex_tbox = TextBox()
      self.__alt_regex_tbox.Dock = DockStyle.Fill
      self.__alt_regex_tbox.TextChanged += self.__fired_update_gui
      self.__alt_regex_warning_label = Label()
      self.__alt_regex_warning_label.UseMnemonic = False
      self.__alt_regex_warning_label.AutoSize = False
      self.__alt_regex_warning_label.Dock = DockStyle.Fill
      self.__alt_regex_warning_label.ForeColor = Color.Red
      self.__alt_regex_warning_label.Text = i18n.get("ConfigFormAltRegexInvalid")
      self.__alt_regex_warning_label.Visible = False

      # 5. --- imprints
      imprints_label = Label()
      imprints_label.UseMnemonic = False
      imprints_label.AutoSize = False
      imprints_label.Dock = DockStyle.Fill
      imprints_label.Text = i18n.get("ConfigFormImprintsText")

      imprint_from_label = Label()
      imprint_from_label.UseMnemonic = False
      imprint_from_label.AutoSize = False
      imprint_from_label.Dock = DockStyle.Fill
      imprint_from_label.TextAlign = ContentAlignment.MiddleLeft
      imprint_from_label.Text = i18n.get("ConfigFormImprintFromLabel")

      imprint_to_label = Label()
      imprint_to_label.UseMnemonic = False
      imprint_to_label.AutoSize = False
      imprint_to_label.Dock = DockStyle.Fill
      imprint_to_label.TextAlign = ContentAlignment.MiddleLeft
      imprint_to_label.Text = i18n.get("ConfigFormImprintToLabel")

      imprint_from_tbox, imprint_to_tbox, imprint_add_button, imprint_table = \
         self.__build_map_list_editor(
            "ConfigFormImprintFromCol", "ConfigFormImprintToCol")
      imprint_add_button.Click += self.__fired_add_imprint
      self.__imprint_from_tbox = imprint_from_tbox
      self.__imprint_to_tbox = imprint_to_tbox
      self.__imprint_table = imprint_table

      # 6. --- add 'em all to the tabpage
      table_layout.Controls.Add(label, 0, 0)
      table_layout.SetColumnSpan(label, 2)
      table_layout.Controls.Add(info_button, 2, 0)
      table_layout.Controls.Add(self.__rating_cb, 0, 1)
      table_layout.SetColumnSpan(self.__rating_cb, 3)
      table_layout.Controls.Add(self.__show_covers_cb, 0, 2)
      table_layout.SetColumnSpan(self.__show_covers_cb, 3)
      table_layout.Controls.Add(self.__welcome_dialog_cb, 0, 3)
      table_layout.SetColumnSpan(self.__welcome_dialog_cb, 3)
      table_layout.Controls.Add(self.__ignore_folders_cb, 0, 4)
      table_layout.SetColumnSpan(self.__ignore_folders_cb, 3)
      table_layout.Controls.Add(self.__force_series_art_cb, 0, 5)
      table_layout.SetColumnSpan(self.__force_series_art_cb, 3)
      table_layout.Controls.Add(self.__note_scrape_date_cb, 0, 6)
      table_layout.SetColumnSpan(self.__note_scrape_date_cb, 3)
      table_layout.Controls.Add(scrapedelay_label, 0, 7)
      table_layout.SetColumnSpan(scrapedelay_label, 2)
      table_layout.Controls.Add(self.__scrape_delay_nud, 2, 7)
      table_layout.Controls.Add(altregex_label, 0, 8)
      table_layout.SetColumnSpan(altregex_label, 3)
      table_layout.Controls.Add(self.__alt_regex_tbox, 0, 9)
      table_layout.SetColumnSpan(self.__alt_regex_tbox, 3)
      table_layout.Controls.Add(self.__alt_regex_warning_label, 0, 10)
      table_layout.SetColumnSpan(self.__alt_regex_warning_label, 3)
      table_layout.Controls.Add(imprints_label, 0, 11)
      table_layout.SetColumnSpan(imprints_label, 3)
      table_layout.Controls.Add(imprint_from_label, 0, 12)
      table_layout.Controls.Add(imprint_to_label, 1, 12)
      table_layout.Controls.Add(imprint_from_tbox, 0, 13)
      table_layout.Controls.Add(imprint_to_tbox, 1, 13)
      table_layout.Controls.Add(imprint_add_button, 2, 13)
      table_layout.Controls.Add(imprint_table, 0, 14)
      table_layout.SetColumnSpan(imprint_table, 3)

      tabpage.Controls.Add(table_layout)
      return tabpage


   # ==========================================================================
   def __build_manualtab(self):
      ''' builds and returns the "Manual" Tab for the TabControl -- the
      raw advanced-settings textbox, gated behind an "enable manual
      editing" checkbox so it can't be edited by accident. '''

      tabpage = TabPage()
      tabpage.Text = i18n.get("ConfigFormManualTab")

      # 1. --- a description label for this tabpage
      label = Label()
      label.UseMnemonic = False
      label.AutoSize = False
      label.Dock = DockStyle.Fill
      label.Text = i18n.get("ConfigFormManualText")

      # 2. --- the "enable manual editing" checkbox; always starts
      #    unchecked (see __set_configuration), and is never persisted.
      self.__manual_enable_cb = CheckBox()
      self.__manual_enable_cb.FlatStyle = FlatStyle.System
      self.__manual_enable_cb.Text = i18n.get("ConfigFormManualEnableCB")
      self.__manual_enable_cb.Dock = DockStyle.Fill
      self.__manual_enable_cb.CheckedChanged += self.__fired_update_gui

      # 3. --- the raw advanced settings textbox itself
      tbox = RichTextBox()
      tbox.Multiline=True
      tbox.MaxLength=65536
      tbox.WordWrap = True
      tbox.Dock = DockStyle.Fill

      menu = ContextMenu()
      items = menu.MenuItems
      items.Add( MenuItem(i18n.get("TextCut"), lambda s, ea : tbox.Cut() ) )
      items.Add( MenuItem(i18n.get("TextCopy"), lambda s, ea : tbox.Copy() ) )
      items.Add( MenuItem(i18n.get("TextPaste"), lambda s, ea : tbox.Paste() ) )
      tbox.ContextMenu = menu
      self.__advanced_tbox = tbox

      # 4. --- layout: description, enable checkbox, then the textbox
      #    filling the rest of the tab
      table_layout = TableLayoutPanel()
      table_layout.RowCount = 3
      table_layout.ColumnCount = 1
      table_layout.Dock = DockStyle.Fill
      self.__add_scaled_row(table_layout, guistyle.header_row_height)
      self.__add_scaled_row(table_layout, guistyle.control_row_height)
      table_layout.RowStyles.Add(System.Windows.Forms.RowStyle(
         System.Windows.Forms.SizeType.Percent, 100))
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Percent, 100))

      table_layout.Controls.Add(label, 0, 0)
      table_layout.Controls.Add(self.__manual_enable_cb, 0, 1)
      table_layout.Controls.Add(self.__advanced_tbox, 0, 2)

      tabpage.Controls.Add(table_layout)
      return tabpage


   # ==========================================================================
   def show_form(self):
      '''
      Displays this form, blocking until the user closes it.  When it is closed,
      this method will return a Configuration object containing the settings 
      that this dialog was displaying when it was closed (these settings were
      also just saved on the filesystem, so they are also the settings that 
      this dialog will display the next time it is opened.)
      
      If the user clicks 'Cancel' then this method will simply return null. 
      '''
      
      log.debug("opened the settings dialog.")
      # self.__config was already loaded in __init__, so __build_gui()
      # could size itself according to the persisted UI scale up front.
      self.__set_configuration(self.__config)
      self.__switch_to_best_tab()
      dialogAnswer = self.ShowDialog() # blocks
      if dialogAnswer == DialogResult.OK:
         config = self.__get_configuration()
         config.save_defaults()
         log.debug("closed the settings dialog.")
      else:
         config = None
         log.debug("cancelled the settings dialog.")
      return config

  
   # ==========================================================================
   def __switch_to_best_tab(self):
      ''' Chooses the best tab to be displayed, and switch to it. '''
      have_api_key = self.__api_key_tbox.Text.strip()
      if have_api_key:
         for tab in self.__tabcontrol.Controls.Find("details", False):
            self.__tabcontrol.SelectedTab = tab
      else:
         for tab in self.__tabcontrol.Controls.Find("comicvine", False):
            self.__tabcontrol.SelectedTab = tab
      
      
   # ==========================================================================
   def __get_configuration(self):
      '''
      Returns a Configuration object the describes the current state of all the
      gui components on this ConfigForm.
      '''
      
      def is_checked( checkbox ):
         return self.__update_checklist.GetItemChecked( \
            self.__update_checklist.Items.IndexOf(checkbox) )
      
      config = Configuration()
      
      # 1. --- first get the parts from the checklist box (data tab)
      config.update_series_b = is_checked(ConfigForm.__SERIES_CB)
      config.update_number_b = is_checked(ConfigForm.__NUMBER_CB)
      config.update_published_b = is_checked(ConfigForm.__PUBLISHED_CB)
      config.update_released_b = is_checked(ConfigForm.__RELEASED_CB)
      config.update_title_b = is_checked(ConfigForm.__TITLE_CB)
      config.update_crossovers_b = is_checked(ConfigForm.__CROSSOVERS_CB)
      config.update_writer_b = is_checked(ConfigForm.__WRITER_CB)
      config.update_penciller_b = is_checked(ConfigForm.__PENCILLER_CB)
      config.update_inker_b = is_checked(ConfigForm.__INKER_CB)
      config.update_cover_artist_b = is_checked(ConfigForm.__COVER_ARTIST_CB)
      config.update_colorist_b = is_checked(ConfigForm.__COLORIST_CB)
      config.update_letterer_b = is_checked(ConfigForm.__LETTERER_CB)
      config.update_editor_b = is_checked(ConfigForm.__EDITOR_CB)
      config.update_summary_b = is_checked(ConfigForm.__SUMMARY_CB)
      config.update_imprint_b = is_checked(ConfigForm.__IMPRINT_CB)
      config.update_publisher_b = is_checked(ConfigForm.__PUBLISHER_CB)
      config.update_volume_b = is_checked(ConfigForm.__VOLUME_CB)
      config.update_characters_b = is_checked(ConfigForm.__CHARACTERS_CB)
      config.update_teams_b = is_checked(ConfigForm.__TEAMS_CB)
      config.update_locations_b = is_checked(ConfigForm.__LOCATIONS_CB)
      config.update_webpage_b = is_checked(ConfigForm.__WEBPAGE_CB)

      
      # 2. --- then get the parts from the other checkboxes (options tab)
      config.ow_existing_b = self.__ow_existing_cb.Checked
      config.convert_imprints_b = self.__convert_imprints_cb.Checked
      config.autochoose_series_b = self.__autochoose_series_cb.Checked
      config.confirm_issue_b = self.__confirm_issue_cb.Checked
      config.ignore_blanks_b = self.__ignore_blanks_cb.Checked
      config.download_thumbs_b = self.__download_thumbs_cb.Checked
      config.preserve_thumbs_b = self.__preserve_thumbs_cb.Checked
      config.fast_rescrape_b = self.__fast_rescrape_cb.Checked
      config.rescrape_notes_b = self.__rescrape_notes_cb.Checked
      config.rescrape_tags_b = self.__rescrape_tags_cb.Checked
      config.summary_dialog_b = self.__summary_dialog_cb.Checked
      
      # 3. --- then get the string out of the advanced settings textbox
      config.advanced_settings_s = self.__advanced_tbox.Text
      config.api_key_s = self.__api_key_tbox.Text.strip()

      # 4. --- reconcile the ignored-publishers table (publishers tab)
      #    against whatever the advanced textbox parsed out above -- the
      #    table is authoritative for ignored publishers specifically,
      #    while the advanced textbox remains authoritative for every
      #    other advanced setting it may also contain.
      table_publishers_sl = [sstr(row.Cells[0].Value)
         for row in self.__publisher_table.Rows]
      table_publishers_lower_sl = [p.lower() for p in table_publishers_sl]
      for publisher_s in config.ignored_publishers_sl:
         if publisher_s.lower() not in table_publishers_lower_sl:
            config.remove_ignored_publisher(publisher_s)
      for publisher_s in table_publishers_sl:
         config.add_ignored_publisher(publisher_s)

      # 5. --- and the UI scale factor (appearance tab)
      config.ui_scale_n = self.__appearance_slider.Value / 100.0

      # 6. --- reconcile every other dedicated advanced-setting control
      #    against the advanced text set in step 3 -- same "dedicated
      #    control wins" spirit as step 4 above, generalized via
      #    Configuration.replace_advanced_lines(). A control's key is
      #    always (re)written from the control's current value; nothing
      #    here is conditioned on whether that value equals the default.

      # search filters tab
      searchterm_sl = [sstr(row.Cells[0].Value)
         for row in self.__searchterm_table.Rows]
      config.replace_advanced_lines("IGNORE_SEARCHTERM",
         ["IGNORE_SEARCHTERM={0}".format(t) for t in searchterm_sl])

      config.replace_advanced_lines("IGNORE_BEFORE_YEAR",
         ["IGNORE_BEFORE_YEAR={0}".format(int(self.__before_year_nud.Value))]
         if self.__before_year_cb.Checked else [])
      config.replace_advanced_lines("IGNORE_AFTER_YEAR",
         ["IGNORE_AFTER_YEAR={0}".format(int(self.__after_year_nud.Value))]
         if self.__after_year_cb.Checked else [])
      config.replace_advanced_lines("NEVER_IGNORE_THRESHOLD",
         ["NEVER_IGNORE_THRESHOLD={0}".format(int(self.__threshold_nud.Value))]
         if self.__threshold_cb.Checked else [])
      config.replace_advanced_lines("MAX_SEARCH_RESULTS",
         ["MAX_SEARCH_RESULTS={0}".format(int(self.__max_results_nud.Value))])

      # publisher aliases tab
      config.replace_advanced_lines("PUBLISHER_ALIAS",
         ["PUBLISHER_ALIAS={0}-->{1}".format(
            sstr(row.Cells[0].Value), sstr(row.Cells[1].Value))
          for row in self.__alias_table.Rows])

      # advanced tab
      config.replace_advanced_lines("SCRAPE_RATING",
         ["SCRAPE_RATING={0}".format(self.__rating_cb.Checked)])
      config.replace_advanced_lines("SHOW_COVERS",
         ["SHOW_COVERS={0}".format(self.__show_covers_cb.Checked)])
      config.replace_advanced_lines("WELCOME_DIALOG",
         ["WELCOME_DIALOG={0}".format(self.__welcome_dialog_cb.Checked)])
      config.replace_advanced_lines("IGNORE_FOLDERS",
         ["IGNORE_FOLDERS={0}".format(self.__ignore_folders_cb.Checked)])
      config.replace_advanced_lines("FORCE_SERIES_ART",
         ["FORCE_SERIES_ART={0}".format(self.__force_series_art_cb.Checked)])
      config.replace_advanced_lines("NOTE_SCRAPE_DATE",
         ["NOTE_SCRAPE_DATE={0}".format(self.__note_scrape_date_cb.Checked)])
      config.replace_advanced_lines("SCRAPE_DELAY",
         ["SCRAPE_DELAY={0}".format(int(self.__scrape_delay_nud.Value))])

      alt_regex_s = self.__alt_regex_tbox.Text.strip()
      if alt_regex_s:
         try:
            re.compile(alt_regex_s)
            config.replace_advanced_lines("ALT_SEARCH_REGEX",
               ["ALT_SEARCH_REGEX={0}".format(alt_regex_s)])
         except:
            config.replace_advanced_lines("ALT_SEARCH_REGEX", [])
      else:
         config.replace_advanced_lines("ALT_SEARCH_REGEX", [])

      config.replace_advanced_lines("IMPRINT",
         ["IMPRINT={0}-->{1}".format(
            sstr(row.Cells[0].Value), sstr(row.Cells[1].Value))
          for row in self.__imprint_table.Rows])

      return config
 
 
   
   # ==========================================================================
   def __set_configuration(self, config):
      '''
      Sets the state of all the gui components on this ConfigForm to match the 
      contents of the given Configuration object.
      '''
      
      def set_checked( checkbox, checked ):
         self.__update_checklist.SetItemChecked( \
            self.__update_checklist.Items.IndexOf(checkbox), checked )
      
      # 1. --- set get the parts in the checklist box (data tab)
      set_checked(ConfigForm.__SERIES_CB, config.update_series_b)
      set_checked(ConfigForm.__NUMBER_CB, config.update_number_b)
      set_checked(ConfigForm.__PUBLISHED_CB, config.update_published_b)
      set_checked(ConfigForm.__RELEASED_CB, config.update_released_b)
      set_checked(ConfigForm.__TITLE_CB, config.update_title_b)
      set_checked(ConfigForm.__CROSSOVERS_CB, config.update_crossovers_b)
      set_checked(ConfigForm.__WRITER_CB, config.update_writer_b)
      set_checked(ConfigForm.__PENCILLER_CB, config.update_penciller_b)
      set_checked(ConfigForm.__INKER_CB, config.update_inker_b)
      set_checked(ConfigForm.__COVER_ARTIST_CB,config.update_cover_artist_b)
      set_checked(ConfigForm.__COLORIST_CB, config.update_colorist_b)
      set_checked(ConfigForm.__LETTERER_CB, config.update_letterer_b)
      set_checked(ConfigForm.__EDITOR_CB, config.update_editor_b)
      set_checked(ConfigForm.__SUMMARY_CB, config.update_summary_b)
      set_checked(ConfigForm.__IMPRINT_CB, config.update_imprint_b)
      set_checked(ConfigForm.__PUBLISHER_CB, config.update_publisher_b)
      set_checked(ConfigForm.__VOLUME_CB, config.update_volume_b)
      set_checked(ConfigForm.__CHARACTERS_CB, config.update_characters_b)
      set_checked(ConfigForm.__TEAMS_CB, config.update_teams_b)
      set_checked(ConfigForm.__LOCATIONS_CB, config.update_locations_b)
      set_checked(ConfigForm.__WEBPAGE_CB, config.update_webpage_b)
      
      # 2. --- then get the parts in the other checkboxes (options tab)
      self.__ow_existing_cb.Checked = config.ow_existing_b
      self.__convert_imprints_cb.Checked = config.convert_imprints_b
      self.__autochoose_series_cb.Checked = config.autochoose_series_b
      self.__confirm_issue_cb.Checked = config.confirm_issue_b
      self.__ignore_blanks_cb.Checked = config.ignore_blanks_b
      self.__download_thumbs_cb.Checked = config.download_thumbs_b
      self.__preserve_thumbs_cb.Checked = config.preserve_thumbs_b
      self.__fast_rescrape_cb.Checked = config.fast_rescrape_b
      self.__rescrape_notes_cb.Checked = config.rescrape_notes_b
      self.__rescrape_tags_cb.Checked = config.rescrape_tags_b
      self.__summary_dialog_cb.Checked = config.summary_dialog_b
      
      # 3. --- finally, set the contents in the textboxes
      self.__advanced_tbox.Text = config.advanced_settings_s
      self.__api_key_tbox.Text = config.api_key_s.strip()

      # 4. --- populate the ignored-publishers table (publishers tab)
      self.__publisher_table.Rows.Clear()
      for publisher_s in config.get_ignored_publishers_display_sl():
         self.__publisher_table.Rows.Add(publisher_s, None)

      # 5. --- and the UI scale slider (appearance tab)
      self.__apply_scale(config.ui_scale_n)

      # 6. --- populate every other dedicated advanced-setting control
      #    directly from Configuration's already-parsed properties (no
      #    reparsing needed here -- see replace_advanced_lines()).

      # search filters tab
      self.__searchterm_table.Rows.Clear()
      for term_s in sorted(config.ignored_searchterms_sl):
         self.__searchterm_table.Rows.Add(term_s, None)

      self.__before_year_cb.Checked = \
         config.ignored_before_year_n != Configuration.DEFAULT_IGNORED_BEFORE_YEAR
      self.__before_year_nud.Value = max(self.__before_year_nud.Minimum,
         min(self.__before_year_nud.Maximum, config.ignored_before_year_n))
      self.__after_year_cb.Checked = \
         config.ignored_after_year_n != Configuration.DEFAULT_IGNORED_AFTER_YEAR
      self.__after_year_nud.Value = max(self.__after_year_nud.Minimum,
         min(self.__after_year_nud.Maximum, config.ignored_after_year_n))
      self.__threshold_cb.Checked = \
         config.never_ignore_threshold_n != Configuration.DEFAULT_NEVER_IGNORE_THRESHOLD
      self.__threshold_nud.Value = max(self.__threshold_nud.Minimum,
         min(self.__threshold_nud.Maximum, config.never_ignore_threshold_n))
      self.__max_results_nud.Value = max(self.__max_results_nud.Minimum,
         min(self.__max_results_nud.Maximum, config.max_search_results_n))

      # publisher aliases tab
      self.__alias_table.Rows.Clear()
      for pub_s in sorted(config.publisher_aliases_sm.keys()):
         self.__alias_table.Rows.Add(
            pub_s, config.publisher_aliases_sm[pub_s], None)

      # advanced tab
      self.__rating_cb.Checked = config.update_rating_b
      self.__show_covers_cb.Checked = config.show_covers_b
      self.__welcome_dialog_cb.Checked = config.welcome_dialog_b
      self.__ignore_folders_cb.Checked = config.ignore_folders_b
      self.__force_series_art_cb.Checked = config.force_series_art_b
      self.__note_scrape_date_cb.Checked = config.note_scrape_date_b
      self.__scrape_delay_nud.Value = max(self.__scrape_delay_nud.Minimum,
         min(self.__scrape_delay_nud.Maximum, config.scrape_delay_n))
      self.__alt_regex_tbox.Text = config.alt_search_regex_s

      self.__imprint_table.Rows.Clear()
      for imprint_s in sorted(config.user_imprints_sm.keys()):
         self.__imprint_table.Rows.Add(
            imprint_s, config.user_imprints_sm[imprint_s], None)

      # manual tab -- always starts locked, regardless of Configuration;
      # this is a transient GUI safety catch, never a stored preference.
      self.__manual_enable_cb.Checked = False

      self.__fired_update_gui()
      
      
      
   # ==========================================================================
   def __fired_restore_defaults(self, sender, args):
      ''' called when the user clicks the "restore defaults"  button '''
      
      api_key_s = self.__api_key_tbox.Text # preserve API key
      self.__set_configuration(Configuration())
      self.__api_key_tbox.Text = api_key_s
      log.debug("all settings were restored to their default values")
      self.__fired_update_gui()
      
      
      
   # ==========================================================================
   def __fired_update_gui(self, sender = None, args = None):
      ''' called anytime the gui for this form should be updated '''
      self.__ignore_blanks_cb.Enabled = self.__ow_existing_cb.Checked
      self.__preserve_thumbs_cb.Enabled = self.__download_thumbs_cb.Checked
      if self.__confirm_issue_cb.Checked:
         self.__autochoose_series_cb.Checked = False
      if self.__autochoose_series_cb.Checked:
         self.__confirm_issue_cb.Checked = False
      self.__confirm_issue_cb.Enabled = not self.__autochoose_series_cb.Checked
      self.__autochoose_series_cb.Enabled = not self.__confirm_issue_cb.Checked

      # search filters tab -- each NumericUpDown is only usable once its
      # "enable" checkbox is checked (unchecked means "use the default,
      # i.e. don't filter on this")
      self.__before_year_nud.Enabled = self.__before_year_cb.Checked
      self.__after_year_nud.Enabled = self.__after_year_cb.Checked
      self.__threshold_nud.Enabled = self.__threshold_cb.Checked

      # advanced tab -- show a warning under the alt search regex textbox
      # if its current text doesn't compile (it would simply be ignored
      # on Save, same as configuration.py's own silent-ignore behavior)
      alt_regex_s = self.__alt_regex_tbox.Text.strip()
      if alt_regex_s:
         try:
            re.compile(alt_regex_s)
            self.__alt_regex_warning_label.Visible = False
         except:
            self.__alt_regex_warning_label.Visible = True
      else:
         self.__alt_regex_warning_label.Visible = False

      # manual tab -- the raw textbox stays read-only until the user
      # explicitly opts in, so it can't be edited by accident
      self.__advanced_tbox.ReadOnly = not self.__manual_enable_cb.Checked

      # ok button is disabled if we have no API key
      self.__ok_button.Enabled = self.__api_key_tbox.Text.strip()
       
              
   # ==========================================================================
   def __fired_linkclicked(self, sender, args):
      ''' called when the user clicks the api key linklabel '''
      System.Diagnostics.Process.Start("https://www.comicvine.gamespot.com/api");
   
   # ==========================================================================
   def __fired_checkall(self, sender, args):
      ''' called when the user clicks the "select all" button '''
      for i in range(self.__update_checklist.Items.Count):
      
         self.__update_checklist.SetItemChecked(i, True)
   
   
   # ==========================================================================
   def __fired_uncheckall(self, sender, args):
      ''' called when the user clicks the "select none" button '''
      for i in range(self.__update_checklist.Items.Count):
         self.__update_checklist.SetItemChecked(i, False)
