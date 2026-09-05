'''
This module is home to the WelcomeForm class.

@author: Cory Banack
'''

import clr
import i18n
from resources import Resources
from cvform import CVForm
from System.Windows.Forms import FormBorderStyle, DockStyle
from configform import ConfigForm
from configuration import Configuration
import guistyle
import System

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import AutoScaleMode, Button, CheckBox, \
    DialogResult, FlatStyle, Label, TableLayoutPanel

clr.AddReference('System.Drawing')
from System.Drawing import Point, Size

# =============================================================================
class WelcomeForm(CVForm):
   '''
   This is the first modal popup dialog that you see when you run the scraper.
   It welcomes you to the program, and offers you the ability to change
   script settings before continuing.
   '''
   
   #===========================================================================
   def __init__(self, scraper, books):
      '''
      Initializes this form.
      
      'scraper' -> this the ScrapeEngine that we are running as part of.
      'books' -> a list of all the comic books being scraped.
      '''
      
      self.__config = scraper.config

      # the "don't show this dialog again" checkbox; always starts
      # unchecked (this dialog is only ever shown when WELCOME_DIALOG is
      # currently true -- see the note in show_form()).
      self.__dont_show_cb = None

      CVForm.__init__(self, scraper.comicrack.MainWindow,
         "welcomeformLocation", "welcomeformSize")
      self.__build_gui(books);


   # ==========================================================================
   def __build_gui(self, books):
      '''
       Constructs and initializes the gui for this form.
      'books' -> a list of all the comic books being scraped.
      '''

      # 1. --- build each gui component
      label = self.__build_label(books)
      dont_show_cb = self.__build_dontshowcheckbox()
      ok = self.__build_okbutton()
      settings = self.__build_settingsbutton()
      cancel = self.__build_cancelbutton()

      # 2. --- configure this form, and add all the gui components to it
      scale_n = self.__config.ui_scale_n
      self.AcceptButton = ok
      self.CancelButton = cancel
      self.AutoScaleMode = AutoScaleMode.Font
      self.Font = guistyle.scaled_font(self.Font, scale_n)
      self.Text = Resources.SCRIPT_FULLNAME
      # the "don't show again" checkbox's text is long enough to wrap onto
      # two lines, so it gets a double-height row (and the window grows to
      # match) instead of the usual single-line control_row_height.
      dont_show_row_height_n = guistyle.control_row_height(self.Font) * 2
      self.ClientSize = Size(500, 200 + dont_show_row_height_n)
      self.MinimumSize = Size(400, 160 + dont_show_row_height_n)

          # 2. --- create and configure the TableLayoutPanel
      table_layout = TableLayoutPanel()
      table_layout.RowCount = 3
      table_layout.ColumnCount = 1
      table_layout.Dock = DockStyle.Fill

      table_layout.RowStyles.Add(System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100))
      table_layout.RowStyles.Add(System.Windows.Forms.RowStyle(
         System.Windows.Forms.SizeType.Absolute, dont_show_row_height_n))
      table_layout.RowStyles.Add(System.Windows.Forms.RowStyle(
         System.Windows.Forms.SizeType.Absolute,
         guistyle.button_row_height(self.Font)))
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Percent, 100))
      self.Controls.Add(table_layout)

      # buttons sublayout, isolated from the label's column above. each
      # button's column is measured directly from its own text at the
      # current font -- SizeType.AutoSize columns combined with a
      # Dock=Fill button can under-measure the needed width and let the
      # text silently wrap onto a second, invisible line (the row only
      # ever reserves room for one).
      buttons_layout = TableLayoutPanel()
      buttons_layout.ColumnCount = 4
      buttons_layout.RowCount = 1
      # without an explicit RowStyle, this row defaults to AutoSize (fits
      # the buttons' own natural height) instead of filling the scaled
      # height given to it by the outer row -- force it to fill instead.
      buttons_layout.RowStyles.Add(System.Windows.Forms.RowStyle(
         System.Windows.Forms.SizeType.Percent, 100))
      for btn in (ok, cancel, settings):
         buttons_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
            System.Windows.Forms.SizeType.Absolute,
            guistyle.button_column_width(btn.Text, self.Font)))
      # trailing spacer column absorbs any leftover width, so the actual
      # button columns stay at their measured (not stretched) size.
      buttons_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(
         System.Windows.Forms.SizeType.Percent, 100))
      buttons_layout.Dock = DockStyle.Fill
      buttons_layout.Controls.Add(ok, 0, 0)
      buttons_layout.Controls.Add(cancel, 1, 0)
      buttons_layout.Controls.Add(settings, 2, 0)

      table_layout.Controls.Add(label, 0, 0)
      table_layout.Controls.Add(dont_show_cb, 0, 1)
      table_layout.Controls.Add(buttons_layout, 0, 2)

      # 3. --- define the keyboard focus tab traversal ordering
      ok.TabIndex = 0
      cancel.TabIndex = 1
      label.TabIndex = 2
      settings.TabIndex = 3
      dont_show_cb.TabIndex = 4
      
      
   # ==========================================================================
   def __build_label(self, books):
      ''' 
      Builds and returns the Label for this form.
      'books' -> a list of all the comic books being scraped. 
      '''

      plural = len(books) != 1
      
      label = Label()
      label.UseMnemonic = False
      label.AutoSize = True
      label.Location = Point(9, 10)
      label.Size = Size(319, 13)
      label.Text = i18n.get("WelcomeFormTextPlural").format(len(books)) \
         if plural else i18n.get("WelcomeFormTextSingle")
      label.Dock = DockStyle.Fill
      return label

   
   # ==========================================================================
   def __build_dontshowcheckbox(self):
      '''
      Builds and returns the "don't show this dialog again" checkbox.
      Always starts unchecked -- see the note in show_form() for why.
      '''

      checkbox = CheckBox()
      checkbox.FlatStyle = FlatStyle.System
      checkbox.AutoSize = False # let its row's height wrap the long text
      checkbox.Text = i18n.get("WelcomeFormDontShowCB")
      checkbox.Dock = DockStyle.Fill
      self.__dont_show_cb = checkbox
      return checkbox


   # ==========================================================================
   def __build_okbutton(self):
      ''' Builds and returns the ok button for this form. '''

      button = Button()
      button.DialogResult = DialogResult.OK
      button.Location = Point(10, 68)
      button.Size = Size(145, 23)
      button.Text = i18n.get("WelcomeFormStart")
      button.UseVisualStyleBackColor = True
      button.Dock = DockStyle.Fill
      return button
   
   
   # ==========================================================================
   def __build_settingsbutton(self):
      ''' Builds and returns the settings button for this form. '''
     
      button = Button()
      button.Click += self.__show_configform
      button.Location = Point(208, 68)
      button.Size = Size(100, 23)
      button.Text = i18n.get("WelcomeFormSettings")
      button.UseVisualStyleBackColor = True
      button.Dock = DockStyle.Fill
      return button

   
   # ==========================================================================
   def __build_cancelbutton(self):
      ''' Builds and returns the cancel button for this form. '''
      
      button = Button()
      button.DialogResult = DialogResult.Cancel
      button.Location = Point(314, 68)
      button.Size = Size(90, 23)
      button.Text = i18n.get("WelcomeFormCancel")
      button.UseVisualStyleBackColor = True
      button.Dock = DockStyle.Fill
      return button

      
   # ==========================================================================
   def show_form(self):
      '''
      Displays this form, blocking until the user closes it.  Returns a boolean
      indicating whether the user cancelled the dialog and scrape operation
      (False) or whether the user clicked ok to continue (True).
      '''

      dialogAnswer = self.ShowDialog(self.Owner) # blocks
      if dialogAnswer == DialogResult.OK and self.__dont_show_cb.Checked:
         # this dialog is only ever shown when WELCOME_DIALOG is currently
         # true (see scrapeengine.py), so there's nothing to reconcile --
         # just turn it off. Reload a fresh Configuration from disk first
         # (rather than reusing/saving self.__config, which may now be
         # stale if the user also opened Settings via that button below)
         # so we don't clobber any changes they made there.
         fresh_config = Configuration()
         fresh_config.load_defaults()
         fresh_config.replace_advanced_lines("WELCOME_DIALOG",
            ["WELCOME_DIALOG=False"])
         fresh_config.save_defaults()
      return dialogAnswer == DialogResult.OK;
      
   # ==========================================================================
   def __show_configform(self, sender, args):
      '''
      Displays the configform, blocking until the user closes it.   Changes made
      to the settings in that form will be saved in the user's profile, where
      they can be loaded when needed.
      '''
      
      with ConfigForm(self) as config_form:
         config_form.show_form() # blocks
   