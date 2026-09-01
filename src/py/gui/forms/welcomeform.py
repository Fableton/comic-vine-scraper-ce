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
import System

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import AutoScaleMode, Button, DialogResult, Label, TableLayoutPanel

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
      
      CVForm.__init__(self, scraper.comicrack.MainWindow, "welcomeformLocation")
      self.__build_gui(books);

      
   # ==========================================================================
   def __build_gui(self, books):
      '''
       Constructs and initializes the gui for this form.
      'books' -> a list of all the comic books being scraped.
      '''
      
      # 1. --- build each gui component
      label = self.__build_label(books)
      ok = self.__build_okbutton()
      settings = self.__build_settingsbutton()
      cancel = self.__build_cancelbutton()
   
      # 2. --- configure this form, and add all the gui components to it
      self.AcceptButton = ok
      self.CancelButton = cancel
      self.AutoScaleMode = AutoScaleMode.Font
      self.Text = Resources.SCRIPT_FULLNAME
      self.ClientSize = Size(500, 200)
      self.FormBorderStyle = FormBorderStyle.Sizable

          # 2. --- create and configure the TableLayoutPanel
      table_layout = TableLayoutPanel()
      table_layout.RowCount = 2
      table_layout.ColumnCount = 3
      table_layout.Dock = DockStyle.Fill

      table_layout.RowStyles.Add(System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100))
      table_layout.RowStyles.Add(System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 64))

      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 33.33))
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 33.33))
      table_layout.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 33.33))
      self.Controls.Add(table_layout)

      table_layout.Controls.Add(label, 0, 0)
      table_layout.SetColumnSpan(label, 3)
      table_layout.Controls.Add(ok,0,1)
      table_layout.Controls.Add(cancel,1,1)
      table_layout.Controls.Add(settings,2,1)
      
      # 3. --- define the keyboard focus tab traversal ordering
      ok.TabIndex = 0
      cancel.TabIndex = 1
      label.TabIndex = 2
      settings.TabIndex = 3
      
      
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
   