'''
This module defines the shared visual sizing helpers used across all of
this plugin's GUI forms (button/row heights, fonts), and how those sizes
scale according to the user's configured UI scale factor (see
Configuration.ui_scale_n, adjustable via a slider on the ConfigForm's
"Appearance" tab).

Row/button heights are computed FROM THE ACTUAL FONT (via Font.Height,
which is already in pixels and already reflects the current scale --
see scaled_font()), plus a fixed padding allowance for borders/chrome,
rather than from an independent baseline pixel constant multiplied by
the scale factor. A flat "36px at 100%, scaled" button height can drift
out of sync with what the font actually needs to render without
clipping (border/padding overhead doesn't shrink or grow linearly with
font size the same way text does); deriving the height from the font
itself guarantees the text always fits, at any scale.

Forms should use this module instead of hard-coding their own pixel
values for buttons, rows, and other chrome, so that every dialog in the
plugin shares a consistent, uniformly-scalable look.

@author: Cory Banack's ComicRackCE fork contributors
'''

import clr
clr.AddReference('System.Drawing')
from System.Drawing import Font
clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import TextRenderer


#==============================================================================
def scale(base_n, scale_n):
   '''
   Returns 'base_n' multiplied by 'scale_n', rounded to the nearest whole
   pixel. Use this for incidental pixel measurements (padding, small
   fixed-size icons, etc) that aren't primarily about fitting rendered
   text -- for anything that needs to fit a control's own text (buttons,
   checkboxes, labels, filter textboxes), use the row-height functions
   below instead, since they're derived from the font itself.
   '''
   return int(round(base_n * scale_n))


#==============================================================================
def scaled_font(font, scale_n):
   '''
   Returns a new Font, matching the given one, but with its point size
   multiplied by 'scale_n'. Assign the result to a Form's own Font
   property to scale every child control's text at once (WinForms
   controls inherit their parent's Font unless they set their own).
   '''
   return Font(font.FontFamily, font.Size * scale_n, font.Style)


#==============================================================================
def button_row_height(font):
   '''
   Returns a row height (px) that comfortably fits a button's text in
   the given font, plus standard button chrome (borders, padding).
   '''
   return font.Height + 20


#==============================================================================
def control_row_height(font):
   '''
   Returns a row height (px) for a row containing a single labeled
   control (checkbox, textbox, combobox, etc) in the given font.
   '''
   return font.Height + 16


#==============================================================================
def filter_row_height(font):
   '''
   Returns a row height (px) for the compact filter-textbox row shown
   above a results table, in the given font.
   '''
   return font.Height + 12


#==============================================================================
def label_row_height(font):
   '''
   Returns a row height (px) for a row containing only a single-line
   plain description label, in the given font.
   '''
   return font.Height + 10


#==============================================================================
def button_column_width(text_s, font):
   '''
   Returns a column width (px) that comfortably fits a button showing
   'text_s' in the given font on a SINGLE line, plus standard button
   chrome (borders, padding). Measures the text directly instead of
   relying on TableLayoutPanel's own SizeType.AutoSize columns or a
   Button's PreferredSize, both of which can under-measure a
   Dock=DockStyle.Fill button and let its text silently wrap onto a
   second, invisible line (the row height only ever reserves room for
   one line).
   '''
   return TextRenderer.MeasureText(text_s, font).Width + 24


#==============================================================================
def header_row_height(font):
   '''
   Returns a taller row height (px) for a header that may hold
   wrapped/multi-line descriptive text (e.g. "found N series matching
   'X'"), in the given font.
   '''
   return (font.Height * 2) + 20
