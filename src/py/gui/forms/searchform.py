''' 
This module is home to the SearchForm class.

@author: Cory Banack
'''

import clr
import i18n
from cvform import CVForm
from resources import Resources
import utils
import guistyle

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import AutoScaleMode, Button, \
    DialogResult, Keys, Label, ComboBox, ComboBoxStyle, ContextMenu, \
    MenuItem, Clipboard, TableLayoutPanel, DockStyle, FormBorderStyle
import System # for ColumnStyle/RowStyle/Padding

clr.AddReference('System.Drawing')
from System.Drawing import Size, Font

#==============================================================================
class SearchForm(CVForm):
   '''
   This class is a popup, modal dialog with a text field that asks the user to 
   specify search terms for a search query on the Comic Vine database.  It may
   also display an error message describing previous search terms that failed.
   '''
   
   #===========================================================================
   def __init__(self, scraper, initial_search_s, failed_search_s=""):
      '''
      Initializes this form.
      
      'scraper' -> the currently running ScrapeEngine
      'initial_search_s' -> the initial value in this form's text field.
      'failed_search_s' -> (optional) the failed search terms associated with
         this SearchForm.  If this is NOT empty, the search dialog will display
         an error message about the failed search terms couldn't be found
      ''' 
      # the text label for this form (displays regular message)
      self.__label = None
      
      # the fail label for this form (display 'search failed' message)
      self.__fail_label = None
      
      # whether or not the fail label should be visible
      self.__fail_label_is_visible = failed_search_s and failed_search_s.strip()
      
      # the search button (i.e. the 'ok' button) for this form
      self.__search_button = None
            
      # true when the user is pressing the control key, false otherwise
      self.__pressing_controlkey = False;
      
      # the skip button for this form
      self.__skip_button = None
      
      # the cancel button for this form
      self.__cancel_button = None
      
      # the (editable) search combobox for this form
      self.__combobox = None

      self.__config = scraper.config

      CVForm.__init__(self, scraper.comicrack.MainWindow,
         "searchformLocation", "searchformSize")
      scraper.cancel_listeners.append(self.Close)
      self.__build_gui(initial_search_s, failed_search_s)
      

   #===========================================================================      
   def __build_gui(self, initial_search_s, failed_search_s):
      ''' Constructs and initializes the gui for this form. '''
      
      # build each gui component.
      self.__fail_label = self.__build_fail_label(failed_search_s)
      self.__label = self.__build_label()
      self.__search_button = self.__build_searchbutton()
      self.__skip_button = self.__build_skipbutton()
      self.__cancel_button = self.__build_cancelbutton()
      self.__combobox = self.__build_combobox(
         failed_search_s if failed_search_s else initial_search_s,
         self.__search_button, self.__cancel_button)

      # configure this form, and add all gui components to it
      scale_n = self.__config.ui_scale_n
      self.AutoScaleMode = AutoScaleMode.Font
      self.Font = guistyle.scaled_font(self.Font, scale_n)
      self.ClientSize = Size(450, 280 if self.__fail_label_is_visible else 170)
      self.MinimumSize = Size(350, 180)
      self.Text = i18n.get("SeriesSearchFailedTitle") \
         if self.__fail_label_is_visible else i18n.get("SearchFormTitle")
      self.KeyDown += self.__key_was_pressed
      self.KeyUp += self.__key_was_released
      self.__combobox.KeyDown += self.__key_was_pressed
      self.__combobox.KeyUp += self.__key_was_released
      self.Deactivate += self.__was_deactivated

      # responsive layout using a docked TableLayoutPanel, so every
      # component stretches/repositions itself as the window is resized,
      # instead of sitting at fixed coordinates.
      main_layout = TableLayoutPanel()
      main_layout.ColumnCount = 1
      main_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Percent, 100))
      main_layout.RowCount = 5
      main_layout.RowStyles.Add(System.Windows.Forms.RowStyle(
         System.Windows.Forms.SizeType.Absolute,
         guistyle.scale(100, scale_n) if self.__fail_label_is_visible else 0))
      main_layout.RowStyles.Add(System.Windows.Forms.RowStyle(
         System.Windows.Forms.SizeType.Absolute,
         guistyle.label_row_height(self.Font)))
      main_layout.RowStyles.Add(System.Windows.Forms.RowStyle(
         System.Windows.Forms.SizeType.Absolute,
         guistyle.control_row_height(self.__combobox.Font))) # bigger combo font
      main_layout.RowStyles.Add(System.Windows.Forms.RowStyle(
         System.Windows.Forms.SizeType.Percent, 100)) # spacer, absorbs resize
      main_layout.RowStyles.Add(System.Windows.Forms.RowStyle(
         System.Windows.Forms.SizeType.Absolute,
         guistyle.button_row_height(self.Font)))
      main_layout.Dock = DockStyle.Fill
      main_layout.Padding = System.Windows.Forms.Padding(10)

      # buttons sublayout; each button's column is measured directly from
      # its own text at the current font -- SizeType.AutoSize columns
      # combined with a Dock=Fill button can under-measure the needed
      # width and let the text silently wrap onto a second, invisible
      # line (the row only ever reserves room for one).
      buttons_layout = TableLayoutPanel()
      buttons_layout.ColumnCount = 4
      buttons_layout.RowCount = 1
      # without an explicit RowStyle, this row defaults to AutoSize (fits
      # the buttons' own natural height) instead of filling the scaled
      # height given to it by the outer row -- force it to fill instead.
      buttons_layout.RowStyles.Add(System.Windows.Forms.RowStyle(
         System.Windows.Forms.SizeType.Percent, 100))
      for btn in (self.__search_button, self.__skip_button, self.__cancel_button):
         buttons_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
            System.Windows.Forms.SizeType.Absolute,
            guistyle.button_column_width(btn.Text, self.Font)))
      # trailing spacer column absorbs any leftover width, so the actual
      # button columns stay at their measured (not stretched) size.
      buttons_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Percent, 100))
      buttons_layout.Dock = DockStyle.Fill
      self.__search_button.Dock = DockStyle.Fill
      self.__skip_button.Dock = DockStyle.Fill
      self.__cancel_button.Dock = DockStyle.Fill
      buttons_layout.Controls.Add(self.__search_button, 0, 0)
      buttons_layout.Controls.Add(self.__skip_button, 1, 0)
      buttons_layout.Controls.Add(self.__cancel_button, 2, 0)

      main_layout.Controls.Add(self.__fail_label, 0, 0)
      main_layout.Controls.Add(self.__label, 0, 1)
      main_layout.Controls.Add(self.__combobox, 0, 2)
      main_layout.Controls.Add(buttons_layout, 0, 4)

      self.Controls.Add(main_layout)

      # define the keyboard focus tab traversal ordering
      self.__combobox.TabIndex = 0
      self.__search_button.TabIndex = 1
      self.__skip_button.TabIndex = 2
      self.__cancel_button.TabIndex = 3


   #===========================================================================      
   def __build_fail_label(self, failed_search_s):
      ''' builds and returns the 'search failed' text label for this form.
          if there is no failed search terms, this returns None. '''

      label = Label()
      label.UseMnemonic = False
      label.Dock = DockStyle.Fill
      label.Visible = self.__fail_label_is_visible
      if self.__fail_label_is_visible:
         label.Text = i18n.get("SeriesSearchFailedText").format(failed_search_s)

      return label

   
   #===========================================================================      
   def __build_label(self):
      ''' builds and returns the text label for this form '''

      label = Label()
      label.UseMnemonic = False
      label.Dock = DockStyle.Fill
      label.Text = i18n.get("SearchFormText")
      return label

         
   #===========================================================================      
   def __build_searchbutton(self):
      ''' builds and returns the search button for this form '''
      
      button = Button()
      button.DialogResult = DialogResult.OK
      button.Text = i18n.get("SearchFormSearch")
      button.UseVisualStyleBackColor = True
      return button
   
   
   #===========================================================================      
   def __build_skipbutton(self):
      ''' builds and returns the skip button for this form '''

      button = Button()
      button.DialogResult = DialogResult.Ignore
      button.Text = i18n.get("SearchFormSkip")
      button.UseVisualStyleBackColor = True
      return button
   
   
   #===========================================================================      
   def __build_cancelbutton(self):
      ''' builds and returns the cancel button for this form '''
      
      button = Button()
      button.DialogResult = DialogResult.Cancel
      button.Text = i18n.get("SearchFormCancel")
      button.UseVisualStyleBackColor = True
      return button
   
   
   #===========================================================================
   def __build_combobox(self, initial_text_s, searchbutton, cancelbutton):
      '''
      Builds and returns the (editable) search combobox for this form.
      Besides letting the user type any freeform text (like the old textbox
      did), this combobox's dropdown list shows the last 20 unique search
      terms that were previously used (most recent first); picking one just
      fills in the text, which can still be edited before pressing Search.

      initial_text_s -> the starting text for the combobox
      searchbutton -> the 'search' button from the containing Form
      cancelbutton -> the 'cancel' button from the containing Form
      '''

      # make a special subclass of ComboBox in order to...
      class SearchComboBox(ComboBox):
         # ... capture ESCAPE and ENTER keypresses
         def OnKeyPress(self, args):
            if args.KeyChar == chr(13):
               searchbutton.PerformClick()
               args.Handled = True
            elif args.KeyChar == chr(27):
               cancelbutton.PerformClick()
               args.Handled = True
            else:
               ComboBox.OnKeyPress(self, args)

         # ... disable the Search button if the combobox's text is empty
         def OnTextChanged(self, args):
            searchbutton.Enabled = bool(self.Text.strip())

      cbox = SearchComboBox()
      cbox.DropDownStyle = ComboBoxStyle.DropDown # editable text + dropdown
      cbox.Dock = DockStyle.Fill
      cbox.Font = Font(cbox.Font.FontFamily,
         12.0 * self.__config.ui_scale_n, cbox.Font.Style)
      for term_s in self.__load_search_history():
         cbox.Items.Add(term_s)
      if initial_text_s:
         cbox.Text = initial_text_s
      cbox.Select(0, len(cbox.Text) if cbox.Text else 0)
      utils.fix_ctrl_backspace(cbox)

      # ComboBox doesn't have TextBox's Cut()/Copy()/Paste() convenience
      # methods, so implement the same context menu items by hand.
      def do_copy():
         if cbox.SelectionLength > 0:
            Clipboard.SetText(cbox.SelectedText)
      def do_cut():
         if cbox.SelectionLength > 0:
            Clipboard.SetText(cbox.SelectedText)
            start_n = cbox.SelectionStart
            text_s = cbox.Text
            cbox.Text = text_s[:start_n] + text_s[start_n + cbox.SelectionLength:]
            cbox.Select(start_n, 0)
      def do_paste():
         if Clipboard.ContainsText():
            paste_s = Clipboard.GetText()
            start_n = cbox.SelectionStart
            text_s = cbox.Text
            cbox.Text = text_s[:start_n] + paste_s + \
               text_s[start_n + cbox.SelectionLength:]
            cbox.Select(start_n + len(paste_s), 0)

      menu = ContextMenu()
      items = menu.MenuItems
      items.Add( MenuItem(i18n.get("TextCut"), lambda s, ea : do_cut() ) )
      items.Add( MenuItem(i18n.get("TextCopy"), lambda s, ea : do_copy() ) )
      items.Add( MenuItem(i18n.get("TextPaste"), lambda s, ea : do_paste() ) )
      cbox.ContextMenu = menu
      return cbox


   #===========================================================================
   def __load_search_history(self):
      '''
      Returns a list of up to the 20 most recently used search terms (as
      strings), ordered most-recent-first.  Returns [] if there is no
      history yet, or if it can't be loaded for any reason.
      '''
      contents_s = utils.load_string(Resources.SEARCH_HISTORY_FILE)
      if not contents_s:
         return []
      return [line.strip() for line in contents_s.split("\n") if line.strip()]


   #===========================================================================
   def __save_search_history(self, search_terms_s):
      '''
      Adds the given (non-empty) search terms to the front of the persisted
      search history, removing any existing case-insensitive duplicate of
      it first, and keeping only the 20 most recent entries.
      '''
      history_sl = self.__load_search_history()
      history_sl = [t for t in history_sl if t.lower() != search_terms_s.lower()]
      history_sl.insert(0, search_terms_s)
      utils.persist_string(
         "\n".join(history_sl[:20]), Resources.SEARCH_HISTORY_FILE)



   #===========================================================================      
   def show_form(self):
      '''
      Displays this form, blocking until the user closes it.  When it is closed, 
      a SearchFormResult will be returned indicating what the user chose.
      '''
      
      dialogAnswer = self.ShowDialog( self.Owner ) # blocks
      if dialogAnswer == DialogResult.OK:
         search_terms_s = self.__combobox.Text.strip()
         if search_terms_s:
            self.__save_search_history(search_terms_s)
            return SearchFormResult("SEARCH", search_terms_s)
         else:
            return SearchFormResult("CANCEL")
      elif dialogAnswer == DialogResult.Ignore:
         if self.ModifierKeys == Keys.Control:
            return SearchFormResult("PERMSKIP")
         else:
            return SearchFormResult("SKIP")
      else:
         return SearchFormResult("CANCEL")
 
 
   #===========================================================================         
   def __key_was_pressed(self, sender, args):
      ''' Called whenever the user presses any key on this form. '''
      
      # highlight the skip button whenever the user presses control key
      if args.KeyCode == Keys.ControlKey and not self.__pressing_controlkey:
         self.__pressing_controlkey = True;
         self.__skip_button.Text = "- " + i18n.get("SearchFormSkip") + " -"
   
         
   #===========================================================================         
   def __key_was_released(self, sender, args):
      ''' Called whenever the user releases any key on this form. '''
      
      # unhighlight the skip button bold whenever the user releases control key
      if args.KeyCode == Keys.ControlKey:
         self.__pressing_controlkey = False;
         self.__skip_button.Text = i18n.get("SearchFormSkip")
         
   #===========================================================================         
   def __was_deactivated(self, sender, args):
      ''' Called whenever this form gets deactivated, for any reason '''
      
      # unhighlight the skip button bold whenever we deactivate
      if self.__pressing_controlkey:
         self.__pressing_controlkey = False;
         self.__skip_button.Text = i18n.get("SearchFormSkip")
      
      
#===========================================================================      
class SearchFormResult(object):
   ''' Results that can be returned from the SearchForm.show_form() method. '''
   
   CANCEL = "cancel"
   SKIP = "skip"
   PERMSKIP = "permskip"
   
   def __init__(self, id, search_terms_s=""):
      '''
      Creates a new SearchFormResult object with the given ID.
      
      id -> the result ID.  Must be one of "SEARCH" (proceed with search), 
            "CANCEL" (cancel entire scrape operation), "SKIP" (skip this book) 
            or "PERMSKIP" (permanently skip this book)
            
      search_terms_s -> the search terms to search on when our ID is "SEARCH". 
            This value should be empty for all other IDs.
      '''
      if id != "SEARCH" and id != "CANCEL" and \
            id != "SKIP" and id != "PERMSKIP":
         raise Exception()
      
      search_terms_s = search_terms_s.strip()
      if id=="SEARCH" and not search_terms_s:
         raise Exception()
      
      self.__id = id
      self.__search_terms_s = search_terms_s \
          if id=="SEARCH" and utils.is_string(search_terms_s) else ""
      
      
   #===========================================================================         
   def equals(self, id):
      ''' 
      Returns True iff this SearchFormResult has the given ID (i.e. one of 
      "SEARCH", "CANCEL", "SKIP", or "PERMSKIP".)
      '''
      return self.__id == id

  
   #===========================================================================         
   def get_search_terms_s(self):
      '''
      Get the series search terms for this SearchFormResult. This value will be
      non-empty if our id is "SEARCH", and it will be empty ("") otherwise.  
      '''
      return self.__search_terms_s
   
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
         return "SEARCH using: '" + self.get_search_terms_s() + "'"
      else:
         raise Exception()  
      