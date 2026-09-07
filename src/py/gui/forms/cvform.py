'''
This module contains the CVForm class.

@author: Cory Banack
'''

import clr
import log

clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')

from System.Windows.Forms import FormBorderStyle, Keys, TableLayoutPanel
from System.Drawing import Color, SolidBrush
from persistentform import PersistentForm

#==============================================================================
class CVForm(PersistentForm):
   '''
   This class is the direct superclass of all Comic Vine Scraper forms.
   It contains functionality and default configuration that is common to
   all forms in this application.
   '''

   # dev-only: Ctrl+Shift+G tints every TableLayoutPanel cell by nesting
   # depth, cycling through this palette (translucent so text/controls
   # underneath stay legible).
   __GRID_DEBUG_DEPTH_COLORS = [
      Color.FromArgb(60, 255, 0, 255),   # depth 0: magenta
      Color.FromArgb(60, 0, 160, 255),   # depth 1: blue
      Color.FromArgb(60, 0, 200, 0),     # depth 2: green
      Color.FromArgb(60, 255, 140, 0),   # depth 3: orange
   ]

   #===========================================================================
   def __init__(self, owner, persist_loc_key_s = "", persist_size_key_s = "" ):
      ''' 
      Constructs a new CVForm.
      Requires an owner parameter, which is the Form that will own this Form.
      The other two parameters are passed up to the PersistentForm superclass.
      '''
      super(CVForm, self).__init__( persist_loc_key_s, persist_size_key_s )
      
      # these are the default properties of all CVForms.
      self.Owner = owner 
      self.Modal = False
      self.MaximizeBox = False                                                
      self.MinimizeBox = False                                                
      self.ShowIcon = False                                                   
      self.ShowInTaskbar = False
      # every CVForm is resizable by default, for a consistent feel across
      # the whole plugin -- individual forms should NOT override this.
      self.FormBorderStyle = FormBorderStyle.Sizable

      # dev-only grid debug overlay state; see __toggle_grid_debug()
      self.__grid_debug_b = False
      self.__grid_debug_depths = None

      
   #===========================================================================
   def ShowDialog(self, owner=None):
      ''' Overidden to make the ShowDialog method behave more sensibly when 
          an Owner is already set on the form; i.e. now you don't have to 
          re-specify that owner. '''
      if owner:
         return super(CVForm, self).ShowDialog(owner)
      elif self.Owner:
         return super(CVForm, self).ShowDialog(self.Owner)
      else:
         return super(CVForm, self).ShowDialog()         
         
   #===========================================================================
   def __enter__(self):
      ''' Called automatically if you use this form in a python "with" block.'''
      return self
   
   
   #===========================================================================
   def __exit__(self, type, value, traceback): 
      ''' Called automatically if you use this form in a python "with" block.'''
      
      # ensure that the form is closed and disposed in a timely manner.
      # this probably isn't strictly necessary, but it doesn't hurt.
      self.Close()
      self.Dispose()


   #===========================================================================
   def ProcessCmdKey(self, msg, keys):
      ''' Called anytime the user presses a key while this form has focus. '''
      
      # overidden to allow various "application wide" hotkeys
      if keys == Keys.Escape:
         # ensure that all CVForms close themselves if you press the escape key. 
         self.Close()
      elif keys == Keys.Control|Keys.Shift|Keys.L:
         # ensure that the use can manually save out an application log
         log.save()
      elif keys == Keys.Control|Keys.Shift|Keys.G:
         # dev-only: toggle the grid debug overlay (see __toggle_grid_debug)
         self.__toggle_grid_debug()
      else:
         super(CVForm, self).ProcessCmdKey(msg, keys)


   #===========================================================================
   def __toggle_grid_debug(self):
      ''' Dev-only: toggles an overlay that tints every TableLayoutPanel's
          cells by nesting depth, so layouts can be discussed precisely
          ("row 2, column 1, the blue grid") without guesswork. '''

      if self.__grid_debug_depths is None:
         self.__grid_debug_depths = dict(self.__find_table_layouts(self))
         for panel in self.__grid_debug_depths:
            panel.CellPaint += self.__grid_debug_cell_paint

      self.__grid_debug_b = not self.__grid_debug_b
      for panel in self.__grid_debug_depths:
         panel.Invalidate()


   #===========================================================================
   def __find_table_layouts(self, control, depth=0, out=None):
      ''' Recursively finds every TableLayoutPanel under the given control,
          returning a list of (panel, depth) pairs. Depth only increases when
          descending into a TableLayoutPanel's own children -- a plain
          container (Panel, GroupBox, etc) in between doesn't add a level. '''

      if out is None:
         out = []
      is_grid_b = isinstance(control, TableLayoutPanel)
      if is_grid_b:
         out.append((control, depth))
      child_depth = depth + 1 if is_grid_b else depth
      for child in control.Controls:
         self.__find_table_layouts(child, child_depth, out)
      return out


   #===========================================================================
   def __grid_debug_cell_paint(self, sender, args):
      ''' CellPaint handler that tints one cell by its panel's nesting depth,
          while the grid debug overlay is toggled on. '''

      if not self.__grid_debug_b:
         return
      depth_n = self.__grid_debug_depths.get(sender, 0)
      colors = self.__GRID_DEBUG_DEPTH_COLORS
      color = colors[depth_n % len(colors)]
      args.Graphics.FillRectangle(SolidBrush(color), args.CellBounds)
