'''
This module contains the ConfigForm class (a popup dialog).

@author: Cory Banack
'''
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
    FlatStyle, Label, MenuItem, RichTextBox, SelectionMode, TabControl, \
    TabPage, TextBox, LinkLabel, TableLayoutPanel, TrackBar, TickStyle

clr.AddReference('System.Drawing')
from System.Drawing import Point, Size, ContentAlignment

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
      tabcontrol.Controls.Add( self.__build_appearancetab() )
      tabcontrol.Controls.Add( self.__build_advancedtab() )
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
      
      
      # 1. --- a description label for this tabpage
      label = Label()
      label.UseMnemonic = False
      label.AutoSize = True
      label.Location = Point(14, 25)
      label.Size = Size(299, 17)
      label.Text = i18n.get("ConfigFormAdvancedText")
      
      
      # 2. --- build the update checklist (contains all the 'data' checkboxes)
      tbox = RichTextBox()
      tbox.Multiline=True
      tbox.MaxLength=65536
      tbox.WordWrap = True
      tbox.Location = Point(15, 50)
      tbox.Size = Size(355, 200)
      
      menu = ContextMenu()
      items = menu.MenuItems
      items.Add( MenuItem(i18n.get("TextCut"), lambda s, ea : tbox.Cut() ) )
      items.Add( MenuItem(i18n.get("TextCopy"), lambda s, ea : tbox.Copy() ) )
      items.Add( MenuItem(i18n.get("TextPaste"), lambda s, ea : tbox.Paste() ) )
      tbox.ContextMenu = menu
      self.__advanced_tbox = tbox
      
      # 3. --- add 'em all to the tabpage 
      tabpage.Controls.Add(label)
      tabpage.Controls.Add(self.__advanced_tbox)
      
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
