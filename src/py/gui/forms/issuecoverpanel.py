# -*- coding: utf-8 -*-
''' 
This module is home to the IssueCoverPanel class.
 
@author: Cory Banack
'''
import clr
from dbmodels import IssueRef, SeriesRef
from dbpicturebox import DBPictureBox
from scheduler import Scheduler
import utils
from utils import sstr
import db
import guistyle
import i18n

clr.AddReference('System.Drawing')
from System.Drawing import ContentAlignment, Font, FontStyle, Point, Size

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import Button, Label, Panel, LinkLabel, TextBox, \
   HorizontalAlignment, Keys, ToolTip




#==============================================================================
class IssueCoverPanel(Panel): 
   '''
   This panel is a compound gui component for displaying a comic book's issue 
   or series cover art (in a DBPictureBox), along with a few extra decorations.  
   (Layout adaptado para redimensionar y usar todo el espacio disponible.)
   '''
   
   COMIC_WIDTH_HEIGHT_RATIO = 0.65  # approx (width / height) for a comic cover
   
   #===========================================================================
   def __init__(self, config, issue_num_hint_s=None, editable_hint_b=False):
      '''
      'editable_hint_b' -> when True, this panel also shows a small textbox
      below the cover (pre-filled with issue_num_hint_s) that lets the user
      type/edit an issue number; pressing Enter or leaving the textbox
      re-runs the cover search for that number, within whichever SeriesRef
      is currently selected (see set_issue_num_hint()).
      '''
      self.__config = config
      self.__issue_num_hint_s = issue_num_hint_s
      # the hint this panel was originally built with (before any editing);
      # used by get_issue_num_override_s() to tell whether the user has
      # actually changed it, versus it still being the auto-detected value.
      self.__original_issue_num_hint_s = issue_num_hint_s
      self.__editable_hint_b = editable_hint_b
      self.__coverpanel = None
      self.__label = None
      self.__link_callback = None
      self.__nextbutton = None
      self.__prevbutton = None
      self.__hint_textbox = None
      self.__hint_search_button = None
      self.__hint_label = None
      self.__ref = None
      # the last SeriesRef passed to set_ref(), if any -- remembered so that
      # set_issue_num_hint() can re-trigger the search against it later.
      self.__series_ref = None
      self.__button_cache = {}
      self.__series_cache = {}
      self.__finder_scheduler = Scheduler()
      self.__setter_scheduler = Scheduler()
      self.__alt_cover_choice = None
      Panel.__init__(self)
      self.__build_gui()
      # manejar redimensionamiento dinámico
      self.Resize += self.__on_resize
      self.PerformLayout()

   # ==========================================================================
   def __build_gui(self):
      self.__coverpanel = self.__build_coverimage()
      self.__label = self.__build_label()
      self.__nextbutton = self.__build_nextbutton()
      self.__prevbutton = self.__build_prevbutton()
      # tamaño inicial (será reajustado)
      self.Size = Size(195, 405 if self.__editable_hint_b else 360)
      self.Controls.Add(self.__coverpanel)
      self.Controls.Add(self.__prevbutton)
      self.Controls.Add(self.__label)
      self.Controls.Add(self.__nextbutton)
      if self.__editable_hint_b:
         self.__hint_textbox, self.__hint_search_button = \
            self.__build_hint_row()
         self.__hint_label = self.__build_hint_label()
         self.Controls.Add(self.__hint_textbox)
         self.Controls.Add(self.__hint_search_button)
         self.Controls.Add(self.__hint_label)
      self.set_ref(None)
      self.__do_layout()

   # ==========================================================================
   def __build_hint_row(self):
      '''
      Builds and returns the (textbox, button) pair that make up the
      editable "issue number hint" row: a textbox to type/edit an issue
      number, and a search button next to it -- pressing Enter in the
      textbox also works, but the button makes the feature discoverable
      for anyone who wouldn't think to try Enter.
      '''
      tbox = TextBox()
      tbox.Visible = self.__config.show_covers_b
      tbox.TextAlign = HorizontalAlignment.Center
      if utils.is_string(self.__issue_num_hint_s):
         tbox.Text = self.__issue_num_hint_s
      tip = ToolTip()
      tip.SetToolTip(tbox, i18n.get("IssueCoverPanelHintTooltip"))
      def commit_hint():
         self.set_issue_num_hint(tbox.Text)
      def key_down(sender, args):
         if args.KeyCode == Keys.Enter:
            args.SuppressKeyPress = True # avoid the 'ding' sound
            commit_hint()
      def lost_focus(sender, args):
         commit_hint()
      tbox.KeyDown += key_down
      tbox.Leave += lost_focus

      button = Button()
      button.Visible = self.__config.show_covers_b
      button.Text = i18n.get("IssueCoverPanelHintSearch")
      button.UseVisualStyleBackColor = True
      tip.SetToolTip(button, i18n.get("IssueCoverPanelHintTooltip"))
      def search_clicked(sender, args):
         commit_hint()
      button.Click += search_clicked

      return tbox, button

   # ==========================================================================
   def __build_hint_label(self):
      ''' builds and returns the small caption label shown below the
      issue-number hint textbox+button, explaining what they're for. '''
      label = Label()
      label.Visible = self.__config.show_covers_b
      label.UseMnemonic = False
      label.TextAlign = ContentAlignment.MiddleCenter
      label.Text = i18n.get("IssueCoverPanelHintLabel")
      return label

   # ==========================================================================
   def __build_coverimage(self):
      cover = DBPictureBox()
      cover.Location = Point(0, 0)
      cover.Size = Size(195, 320)
      cover.Visible = self.__config.show_covers_b
      return cover
   
   # ==========================================================================
   def __build_label(self):
      label = LinkLabel()
      label.UseMnemonic = False
      label.Visible = self.__config.show_covers_b
      label.Location = Point(18, 326)
      label.Size = Size(155,36)
      label.TextAlign = ContentAlignment.MiddleCenter
      def link_clicked(sender, args):
         if self.__link_callback:
            self.__link_callback()
      label.LinkClicked += link_clicked
      return label
   
   # ==========================================================================
   def __build_nextbutton(self):
      button = Button()
      button.Location = Point(173, 332)
      button.Size = Size(20, 24)
      button.Text = '>'
      button.Font = Font(button.Font, FontStyle.Bold)
      button.UseVisualStyleBackColor = True
      button.Click += self.__button_click_fired
      return button
   
   # ==========================================================================
   def __build_prevbutton(self):
      button = Button()
      button.Location = Point(2, 332)
      button.Size = Size(20, 24)
      button.Text = '<'
      button.Font = Font(button.Font, FontStyle.Bold)
      button.UseVisualStyleBackColor = True
      button.Click += self.__button_click_fired
      return button

   # ==========================================================================
   def __on_resize(self, sender, args):
      self.__do_layout()

   # ==========================================================================
   def __do_layout(self):
      if not self.__config.show_covers_b:
         return
      try:
         scale_n = self.__config.ui_scale_n
         padding = guistyle.scale(4, scale_n)
         label_height = guistyle.scale(36, scale_n)
         btn_h = guistyle.scale(26, scale_n)
         btn_w = guistyle.scale(32, scale_n)
         hint_h = guistyle.scale(24, scale_n) if self.__editable_hint_b else 0
         hint_label_h = guistyle.scale(18, scale_n) if self.__editable_hint_b else 0
         w = self.ClientSize.Width
         h = self.ClientSize.Height
         if w <= 0 or h <= 0:
            return
         # espacio disponible para la imagen (restando label/botones/hint)
         hint_block_h = (hint_h + hint_label_h + padding*2) if hint_h else 0
         reserved_h = btn_h + padding*2 + hint_block_h
         avail_height = max(10, h - reserved_h)
         avail_width = w
         # mantener aspect ratio W/H ~ 0.65 => H = W / 0.65
         desired_height_from_width = int(avail_width / self.COMIC_WIDTH_HEIGHT_RATIO)
         if desired_height_from_width > avail_height:
            # limitar por altura
            cover_height = avail_height
            cover_width = int(cover_height * self.COMIC_WIDTH_HEIGHT_RATIO)
         else:
            cover_width = avail_width
            cover_height = desired_height_from_width
         # centrar horizontalmente
         cover_x = (w - cover_width)//2
         self.__coverpanel.Location = Point(cover_x, 0)
         self.__coverpanel.Size = Size(cover_width, cover_height)
         # posicionar botones y label debajo ajustando ancho label
         btn_y = cover_height + padding
         self.__prevbutton.Size = Size(btn_w, btn_h)
         self.__nextbutton.Size = Size(btn_w, btn_h)
         self.__prevbutton.Location = Point(padding, btn_y)
         self.__nextbutton.Location = Point(w - btn_w - padding, btn_y)
         label_x = self.__prevbutton.Right + padding
         label_w = max(20, self.__nextbutton.Left - padding - label_x)
         self.__label.Location = Point(label_x, btn_y)
         self.__label.Size = Size(label_w, btn_h)
         if self.__editable_hint_b and self.__hint_textbox is not None:
            hint_y = btn_y + btn_h + padding
            # size the button to whatever its own text/font actually need
            # (plus a little breathing room), instead of a fixed pixel cap
            # that doesn't necessarily fit "Search" at every font size.
            min_btn_w = guistyle.scale(36, scale_n)
            preferred_btn_w = self.__hint_search_button.PreferredSize.Width \
               + guistyle.scale(8, scale_n)
            search_btn_w = max(min_btn_w, min(preferred_btn_w, int(w * 0.5)))
            hint_tbox_w = max(20, w - padding*3 - search_btn_w)
            self.__hint_textbox.Location = Point(padding, hint_y)
            self.__hint_textbox.Size = Size(hint_tbox_w, hint_h)
            self.__hint_search_button.Location = \
               Point(padding*2 + hint_tbox_w, hint_y)
            self.__hint_search_button.Size = Size(search_btn_w, hint_h)
            if self.__hint_label is not None:
               label_y = hint_y + hint_h + padding
               self.__hint_label.Location = Point(padding, label_y)
               self.__hint_label.Size = \
                  Size(max(20, w - padding*2), hint_label_h)
      except Exception:
         pass
      
   # ==========================================================================
   def free(self): 
      if type(self.__ref) == IssueRef:
         issue_ref = self.__ref
         button_model = self.__button_cache[issue_ref]
         if button_model and button_model.can_decrement():
            image_ref = button_model.get_current_ref()
            if utils.is_string(image_ref):
               self.__alt_cover_choice = (issue_ref, image_ref)
      self.__finder_scheduler.shutdown(False)
      self.__setter_scheduler.shutdown(False)
      self.set_ref(None)
      self.__coverpanel.free()
      self.__prevbutton = None
      self.__nextbutton = None
      self.__label = None
      self.__hint_textbox = None
      self.__hint_search_button = None
      self.__hint_label = None
      self.Dispose()

   # ==========================================================================
   def set_ref(self, ref):
      if type(ref) == SeriesRef:
         # remember this, so set_issue_num_hint() can re-search it later
         self.__series_ref = ref
      run_in_background = type(ref) == SeriesRef and self.__issue_num_hint_s
      if run_in_background:
         def maybe_convert_seriesref_to_issue_ref(ref):
            if not ref in self.__series_cache:
               issue_ref = db.query_issue_ref(ref, self.__issue_num_hint_s)
               self.__series_cache[ref] = issue_ref if issue_ref else ref
            def change_ref():
               self.__ref = self.__series_cache[ref]
               self.__update()
            utils.invoke(self.__coverpanel, change_ref, True)
         def dummy():
            maybe_convert_seriesref_to_issue_ref(ref)
         self.__setter_scheduler.submit(dummy)
      else:
         self.__ref = ref
         self.__update()

   # ==========================================================================
   def set_issue_num_hint(self, hint_s):
      '''
      Updates the issue number that this panel tries to find a cover for
      (within whichever SeriesRef was most recently passed to set_ref(),
      if any), and immediately re-triggers that search using the new value.
      Has no effect if this panel wasn't built with editable_hint_b=True,
      or if there's no SeriesRef currently selected.
      '''
      hint_s = hint_s.strip() if utils.is_string(hint_s) else ''
      hint_s = hint_s if hint_s else None
      if hint_s == self.__issue_num_hint_s:
         return
      self.__issue_num_hint_s = hint_s
      if self.__series_ref is not None:
         # forget any previously cached (stale) resolution for this series,
         # so that set_ref() below is forced to search again
         if self.__series_ref in self.__series_cache:
            del self.__series_cache[self.__series_ref]
         self.set_ref(self.__series_ref)

   # ==========================================================================
   def get_issue_num_override_s(self):
      '''
      Returns the issue number currently shown in the (editable) hint
      textbox, but ONLY if the user has actually changed it away from the
      value this panel was originally built with (i.e. away from the
      auto-detected issue number). Returns None if this panel wasn't built
      with editable_hint_b=True, or if the hint hasn't been changed --
      callers should fall back to their own default (e.g. the book's
      auto-detected issue number) in that case.
      '''
      if not self.__editable_hint_b:
         return None
      if self.__issue_num_hint_s == self.__original_issue_num_hint_s:
         return None
      return self.__issue_num_hint_s

   # ==========================================================================
   def get_alt_issue_cover_choice(self):
      return self.__alt_cover_choice

   # ==========================================================================
   def __update(self):
      ref = self.__ref
      cache = self.__button_cache
      cover_image = self.__coverpanel
      nextbutton = self.__nextbutton
      prevbutton = self.__prevbutton
      label = self.__label
      scheduler = self.__finder_scheduler
      if ref is None or cache is None:
         cover_image.set_image_ref(None)
         nextbutton.Visible = False
         prevbutton.Visible = False
         label.Text = ''
      else:
         if not cache.has_key(ref):
            cache[ref] = _ButtonModel(ref, 'searched' if type(ref) == SeriesRef else 'not-searched')
         bmodel = cache[ref]
         cover_image.set_image_ref( bmodel.get_current_ref() )
         nextbutton.Visible = cover_image.Visible and bmodel.can_increment()
         prevbutton.Visible = cover_image.Visible and bmodel.can_decrement()
         label.Links.Clear()
         self.__link_callback = None
         issue_num_s = ref.issue_num_s if type(ref) == IssueRef else ''
         if bmodel.get_status() == 'searched':
            if issue_num_s:
               if len(bmodel) > 1:
                  label.Text = i18n.get("IssueCoverPanelPlural").format(sstr(issue_num_s), sstr(bmodel.get_position()+1), sstr(len(bmodel)))
               else:
                  label.Text = i18n.get("IssueCoverPanelSingle").format(sstr(issue_num_s))
            else:
               label.Text = i18n.get("IssueCoverPanelSeries")
         elif bmodel.get_status() == 'searching': 
            label.Text = i18n.get("IssueCoverPanelSearching").format(sstr(issue_num_s))
         elif bmodel.get_status() == 'not-searched':
            label.Text = i18n.get("IssueCoverPanelSearchable").format(sstr(issue_num_s))
            start = label.Text.find('(')
            end = label.Text.find(')', start) if start > -1 else -1
            if start >= 0 and end >= start:
               label.Links.Add(start+1, end)
               def link_callback():
                  bmodel.set_status("searching")
                  self.__update()
               self.__link_callback = link_callback 
         else:
            raise Exception()
         if cache[ref].get_status()=='searching':
            def update_cache():
               issue = db.query_issue(ref, True) if type(ref) == IssueRef else None 
               def update_bmodel():
                  bmodel = cache[ref]
                  if issue and len(issue.image_urls_sl) > 1:
                     for i in range(1, len(issue.image_urls_sl)):
                        bmodel.add_new_ref(issue.image_urls_sl[i])
                  bmodel.set_status('searched')
                  self.__update()
               utils.invoke(self, update_bmodel, True)
            scheduler.submit(update_cache)
      self.__do_layout()

   # ==========================================================================
   def __button_click_fired(self, sender, args):
      bmodel = self.__button_cache[self.__ref]
      if sender == self.__nextbutton:
         bmodel.increment()
      else:
         bmodel.decrement()
      self.__update()

# =============================================================================     
class _ButtonModel(object):
   def __init__(self, ref, status="not-searched"):
      self.__image_refs = []
      self.__status = None
      self.set_status(status)
      self.__pos_n = 0
      self.add_new_ref(ref)
   def add_new_ref(self, image_ref):
      if image_ref and image_ref not in self.__image_refs:
         self.__image_refs.append(image_ref)
   def get_current_ref(self):
      return self.__image_refs[self.__pos_n] if self.__image_refs else None
   def increment(self):
      self.__pos_n = min(len(self.__image_refs)-1, self.__pos_n + 1)
   def can_increment(self):
      return self.__pos_n < len(self.__image_refs)-1
   def decrement(self):
      self.__pos_n = max(0, self.__pos_n - 1)
   def can_decrement(self):
      return self.__pos_n > 0
   def set_status(self, status):
      if status in ('not-searched','searching','searched'):
         self.__status = status
      else:
         raise Exception("bad status received: ", sstr(status))
   def get_status(self):
      return self.__status
   def get_position(self):
      return self.__pos_n
   def __len__(self):
      return len(self.__image_refs)
