'''
This module contains the ProgressBarForm class.

@author: Cory Banack
'''

import clr
from cvform import CVForm
import guistyle

clr.AddReference('IronPython')
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')

from System.Windows.Forms import DockStyle, ProgressBar
from System.Drawing import Size

# =============================================================================
class ProgressBarForm(CVForm): 
   '''
   A simple CVForm that displays a ProgressBar, which callers can access and
   manipulate via the 'pb' variable.   The intention is that this form will be
   briefly displayed during the time that a ProgressBar needs to be visible,
   and then it will disappear as soon as the ProgressBar isn't needed anymore.
   
   Note that if the user manually closes this Form, the __scrape_engine given in the
   __init__ method will be cancelled. 
   '''

   # ==========================================================================
   def __init__(self, owner, scrape_engine):
      '''
      Initializes this ProgressBarForm with the given owner window, and the
      given ScrapeEngine object, which will be cancelled if the user closes 
      this Form manually.
      '''
      
      CVForm.__init__(self, owner, "pbformLocation", "pbformSize")

      scale_n = scrape_engine.config.ui_scale_n
      self.Font = guistyle.scaled_font(self.Font, scale_n)

      pb = ProgressBar()
      pb.Minimum = 0
      pb.Maximum = 1
      pb.Step = 1
      pb.Value = 0
      pb.Dock = DockStyle.Fill

      self.Height = guistyle.scale(45, scale_n)
      self.Width = 400
      self.MinimumSize = Size(200, 40)
      self.Controls.Add(pb)
      
      self.pb = pb
      self.__scrape_engine = scrape_engine
      self.__cancel_on_close_b = True

      
   #===========================================================================
   def show_form(self):
      ''' Call this method in order to display this ProgressBarForm '''
      self.Show(self.Owner)


   #===========================================================================      
   def OnClosed(self, args):
      ''' Called when this Form is closed '''
      
      if self.__cancel_on_close_b:
         # this close is a result of the user explicitly closing this form.
         # that means we should flip the scrapeengine's cancel switch, i.e.
         # we should cancel the entire operation.
         self.__scrape_engine.cancel()
                  
      CVForm.OnClosed(self, args)
      
        
   #===========================================================================
   def __enter__(self):
      ''' Enables this object to be used with python's "with" keyword. '''
      return self
   
   
   #===========================================================================
   def __exit__(self, type, value, traceback):
      ''' Enables this object to be used with python's "with" keyword. '''
      self.__cancel_on_close_b = False  # not explicity cancelled by user!
      self.Close()
      

