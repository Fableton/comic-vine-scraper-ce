# -*- coding: utf-8 -*-
''' 
This module is home to the IssueCoverPanel class.
 
@author: Cory Banack
'''
import clr
import log
from dbmodels import IssueRef, SeriesRef
from dbpicturebox import DBPictureBox
from scheduler import Scheduler
import utils
from utils import sstr
import db
import imagehash
import guistyle
import i18n

clr.AddReference('System.Drawing')
from System.Drawing import ContentAlignment, Font, FontStyle

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import Button, CheckBox, Label, NumericUpDown, \
   Panel, LinkLabel, TextBox, HorizontalAlignment, Keys, Timer, ToolTip, \
   TableLayoutPanel, RowStyle, ColumnStyle, SizeType, DockStyle




#==============================================================================
class IssueCoverPanel(Panel): 
   '''
   This panel is a compound gui component for displaying a comic book's issue
   or series cover art (in a DBPictureBox), along with a few extra decorations.
   Laid out as a single-column grid (see __build_grid) so it resizes cleanly.
   '''
   
   # default value for the auto-accept threshold numeric input (the user
   # can change it per-session via the input itself; see
   # __build_auto_accept_threshold_nud)
   __DEFAULT_AUTO_ACCEPT_THRESHOLD_N = 85

   # how many seconds the auto-accept/skip countdown runs before firing
   __AUTO_ACCEPT_SECONDS_N = 5

   #===========================================================================
   def __init__(self, config, issue_num_hint_s=None, editable_hint_b=False,
         book=None, on_auto_accept=None, on_auto_skip=None):
      '''
      'editable_hint_b' -> when True, this panel also shows a small textbox
      below the cover (pre-filled with issue_num_hint_s) that lets the user
      type/edit an issue number; pressing Enter or leaving the textbox
      re-runs the cover search for that number, within whichever SeriesRef
      is currently selected (see set_issue_num_hint()).

      'book' -> if given, the local ComicBook being scraped. when present,
      this panel compares that book's own (local) cover against whichever
      remote cover is currently displayed, and shows a match percentage
      below it, plus an "Auto-accept" checkbox + threshold input: once
      checked, every time a match result becomes known for the cover
      currently on screen, a countdown starts that ends by calling
      'on_auto_accept' (if the match met the threshold) or 'on_auto_skip'
      (if it didn't) -- unless cancelled first (by picking a different
      issue, unchecking the box, or clicking the countdown's "Cancel"
      link). Both callbacks take no arguments. If 'book' is None, none of
      this (percentage, checkbox, or callbacks) is ever shown/used.
      '''
      self.__config = config
      self.__issue_num_hint_s = issue_num_hint_s
      # the hint this panel was originally built with (before any editing);
      # used by get_issue_num_override_s() to tell whether the user has
      # actually changed it, versus it still being the auto-detected value.
      self.__original_issue_num_hint_s = issue_num_hint_s
      self.__editable_hint_b = editable_hint_b
      self.__book = book
      self.__on_auto_accept = on_auto_accept
      self.__on_auto_skip = on_auto_skip
      self.__coverpanel = None
      self.__label = None
      self.__match_label = None
      self.__auto_accept_checkbox = None
      self.__auto_accept_threshold_nud = None
      self.__auto_accept_status_label = None
      # ref this panel is currently counting down for, or None -- lets a
      # spurious re-trigger of the SAME ref (e.g. "(more covers)" finishing
      # its search) avoid resetting an already-running countdown
      self.__auto_accept_active_ref = None
      # what the current countdown will do once it reaches 0: True to
      # click OK, False to click Skip
      self.__auto_accept_will_accept_b = False
      self.__auto_accept_seconds_left_n = 0
      self.__auto_accept_timer = Timer()
      self.__auto_accept_timer.Interval = 1000
      self.__auto_accept_timer.Tick += self.__auto_accept_tick_fired
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
      # the local book's own cover-image hash, computed once in the
      # background (see __compute_local_hash). __local_hash_ready_b is False
      # until that computation finishes -- __local_hash itself may still be
      # None even once ready_b is True, if the hash genuinely couldn't be
      # computed (e.g. no readable first page); that's a permanent result,
      # distinct from "still computing", so it doesn't get retried forever.
      self.__local_hash = None
      self.__local_hash_ready_b = False
      # ref -> match percentage (int, or None if it couldn't be determined),
      # so re-showing a previously-compared cover (e.g. clicking back and
      # forth between alt covers) doesn't require recomputing it.
      self.__match_cache = {}
      self.__finder_scheduler = Scheduler()
      self.__setter_scheduler = Scheduler()
      # a Scheduler only ever runs its most recently submitted task, silently
      # dropping whatever was queued before it -- so the one-time local-hash
      # computation gets its OWN scheduler, separate from __match_scheduler
      # (which submits a new per-cover task every time the shown cover
      # changes). sharing one scheduler between them let a per-cover match
      # task submitted right after startup permanently evict the not-yet-
      # started local-hash task, leaving the match label stuck on
      # "Comparing covers..." forever.
      self.__local_hash_scheduler = Scheduler()
      self.__match_scheduler = Scheduler()
      self.__alt_cover_choice = None
      Panel.__init__(self)
      self.__build_gui()
      if self.__book is not None:
         self.__compute_local_hash()

   # ==========================================================================
   def __build_gui(self):
      self.__coverpanel = self.__build_coverimage()
      self.__label = self.__build_label()
      self.__nextbutton = self.__build_nextbutton()
      self.__prevbutton = self.__build_prevbutton()
      if self.__book is not None:
         self.__match_label = self.__build_match_label()
         self.__auto_accept_checkbox = self.__build_auto_accept_checkbox()
         self.__auto_accept_threshold_nud = self.__build_auto_accept_threshold_nud()
         self.__auto_accept_status_label = self.__build_auto_accept_status_label()
      if self.__editable_hint_b:
         self.__hint_textbox, self.__hint_search_button = \
            self.__build_hint_row()
         self.__hint_label = self.__build_hint_label()
      # rows whose height (or, for the hint search button's column, width)
      # depends on self.Font -- built using whatever font is available now
      # (which, before this panel is parented, is the WRONG, unscaled
      # default), then corrected once FontChanged fires with the real one.
      self.__dynamic_styles = []
      self.__build_grid()
      self.FontChanged += self.__on_font_changed
      self.set_ref(None)

   # ==========================================================================
   def __build_grid(self):
      ''' Builds the outer grid stacking (top to bottom): the cover image
      (filling all remaining space), the prev/caption/next row, and, if
      applicable, the match-percent label, auto-accept row, auto-accept
      status label, and editable issue-number hint row + its caption. '''
      grid = TableLayoutPanel()
      grid.Dock = DockStyle.Fill
      grid.ColumnCount = 1
      grid.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100))
      row_n = 0

      grid.RowStyles.Add(RowStyle(SizeType.Percent, 100))
      grid.Controls.Add(self.__coverpanel, 0, row_n)
      row_n += 1

      nav_style = RowStyle(SizeType.Absolute, guistyle.button_row_height(self.Font))
      grid.RowStyles.Add(nav_style)
      self.__dynamic_styles.append((nav_style, 'button_row'))
      grid.Controls.Add(self.__build_nav_row(), 0, row_n)
      row_n += 1

      if self.__book is not None:
         match_style = RowStyle(SizeType.Absolute,
            guistyle.label_row_height(self.Font) * 2)
         grid.RowStyles.Add(match_style)
         self.__dynamic_styles.append((match_style, 'label2_row'))
         grid.Controls.Add(self.__match_label, 0, row_n)
         row_n += 1

         auto_style = RowStyle(SizeType.Absolute,
            guistyle.control_row_height(self.Font))
         grid.RowStyles.Add(auto_style)
         self.__dynamic_styles.append((auto_style, 'control_row'))
         grid.Controls.Add(self.__build_auto_accept_row(), 0, row_n)
         row_n += 1

         status_style = RowStyle(SizeType.Absolute,
            guistyle.label_row_height(self.Font) * 2)
         grid.RowStyles.Add(status_style)
         self.__dynamic_styles.append((status_style, 'label2_row'))
         grid.Controls.Add(self.__auto_accept_status_label, 0, row_n)
         row_n += 1

      if self.__editable_hint_b:
         hint_style = RowStyle(SizeType.Absolute,
            guistyle.control_row_height(self.Font))
         grid.RowStyles.Add(hint_style)
         self.__dynamic_styles.append((hint_style, 'control_row'))
         grid.Controls.Add(self.__build_hint_row_panel(), 0, row_n)
         row_n += 1

         hint_label_style = RowStyle(SizeType.Absolute,
            guistyle.label_row_height(self.Font))
         grid.RowStyles.Add(hint_label_style)
         self.__dynamic_styles.append((hint_label_style, 'label1_row'))
         grid.Controls.Add(self.__hint_label, 0, row_n)
         row_n += 1

      grid.RowCount = row_n
      self.Controls.Add(grid)

   # ==========================================================================
   def __build_nav_row(self):
      ''' Builds the small grid holding the prev button, caption label, and
      next button side by side. '''
      row = TableLayoutPanel()
      row.Dock = DockStyle.Fill
      row.RowCount = 1
      row.ColumnCount = 3
      row.RowStyles.Add(RowStyle(SizeType.Percent, 100))
      btn_w = guistyle.scale(32, self.__config.ui_scale_n)
      row.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, btn_w))
      row.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100))
      row.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, btn_w))
      row.Controls.Add(self.__prevbutton, 0, 0)
      row.Controls.Add(self.__label, 1, 0)
      row.Controls.Add(self.__nextbutton, 2, 0)
      return row

   # ==========================================================================
   def __build_auto_accept_row(self):
      ''' Builds the small grid holding the auto-accept checkbox and its
      threshold input side by side. '''
      row = TableLayoutPanel()
      row.Dock = DockStyle.Fill
      row.RowCount = 1
      row.ColumnCount = 2
      row.RowStyles.Add(RowStyle(SizeType.Percent, 100))
      nud_w = guistyle.scale(50, self.__config.ui_scale_n)
      row.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100))
      row.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, nud_w))
      row.Controls.Add(self.__auto_accept_checkbox, 0, 0)
      row.Controls.Add(self.__auto_accept_threshold_nud, 1, 0)
      return row

   # ==========================================================================
   def __build_hint_row_panel(self):
      ''' Builds the small grid holding the issue-number hint textbox and
      its search button side by side. '''
      row = TableLayoutPanel()
      row.Dock = DockStyle.Fill
      row.RowCount = 1
      row.ColumnCount = 2
      row.RowStyles.Add(RowStyle(SizeType.Percent, 100))
      row.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100))
      btn_col_style = ColumnStyle(SizeType.Absolute,
         guistyle.button_column_width(self.__hint_search_button.Text, self.Font))
      row.ColumnStyles.Add(btn_col_style)
      self.__dynamic_styles.append((btn_col_style, 'hint_btn_col'))
      row.Controls.Add(self.__hint_textbox, 0, 0)
      row.Controls.Add(self.__hint_search_button, 1, 0)
      return row

   # ==========================================================================
   def __update_dynamic_sizes(self):
      ''' Recomputes every row height/column width in __dynamic_styles
      against the current (real) self.Font. '''
      font = self.Font
      for style_obj, kind_s in self.__dynamic_styles:
         if kind_s == 'button_row':
            style_obj.Height = guistyle.button_row_height(font)
         elif kind_s == 'control_row':
            style_obj.Height = guistyle.control_row_height(font)
         elif kind_s == 'label1_row':
            style_obj.Height = guistyle.label_row_height(font)
         elif kind_s == 'label2_row':
            style_obj.Height = guistyle.label_row_height(font) * 2
         elif kind_s == 'hint_btn_col':
            style_obj.Width = guistyle.button_column_width(
               self.__hint_search_button.Text, font)

   # ==========================================================================
   def __on_font_changed(self, sender, args):
      ''' self.Font at __build_grid() time is whatever default font this
      panel has BEFORE it's parented -- not the real, scaled font it ends
      up with. Once that real font is known (this fires when it changes),
      fix up the row/column sizes that were computed from it. '''
      self.__update_dynamic_sizes()

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
      tbox.Dock = DockStyle.Fill
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
      button.Dock = DockStyle.Fill
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
      label.Dock = DockStyle.Fill
      label.UseMnemonic = False
      label.TextAlign = ContentAlignment.MiddleCenter
      label.Text = i18n.get("IssueCoverPanelHintLabel")
      return label

   # ==========================================================================
   def __build_coverimage(self):
      cover = DBPictureBox()
      cover.Dock = DockStyle.Fill
      cover.Visible = self.__config.show_covers_b
      return cover

   # ==========================================================================
   def __build_label(self):
      label = LinkLabel()
      label.UseMnemonic = False
      label.Visible = self.__config.show_covers_b
      label.Dock = DockStyle.Fill
      label.TextAlign = ContentAlignment.MiddleCenter
      def link_clicked(sender, args):
         if self.__link_callback:
            self.__link_callback()
      label.LinkClicked += link_clicked
      return label
   
   # ==========================================================================
   def __build_match_label(self):
      ''' builds and returns the small label (shown only when this panel was
      built with a 'book') that displays the currently shown cover's match
      percentage against that book's own (local) cover. '''
      label = Label()
      label.UseMnemonic = False
      label.AutoSize = False
      label.Visible = self.__config.show_covers_b
      label.Dock = DockStyle.Fill
      label.TextAlign = ContentAlignment.MiddleCenter
      return label

   # ==========================================================================
   def __build_auto_accept_checkbox(self):
      ''' builds and returns the "auto-accept" checkbox. its checked state
      is remembered in the config's session_data_map, so it stays set
      across every book in this scrape session (not just this one
      dialog), but resets the next time ComicRack is restarted. '''
      checkbox = CheckBox()
      # AutoSize=True silently ignores Dock=Fill (the checkbox would just
      # size itself to its own text); this row needs it to fill its cell.
      checkbox.AutoSize = False
      checkbox.Dock = DockStyle.Fill
      checkbox.TextAlign = ContentAlignment.MiddleLeft
      checkbox.Visible = self.__config.show_covers_b
      checkbox.Text = i18n.get("IssueCoverPanelAutoAcceptCheckbox")
      checkbox.Checked = bool(self.__config.session_data_map.get(
         'auto_accept_high_matches_b', False))
      checkbox.CheckedChanged += self.__auto_accept_checkbox_changed_fired
      tip = ToolTip()
      tip.SetToolTip(checkbox, i18n.get("IssueCoverPanelAutoAcceptTooltip"))
      return checkbox

   # ==========================================================================
   def __build_auto_accept_threshold_nud(self):
      ''' builds and returns the auto-accept match-percentage threshold
      input. its value is remembered the same way (and for the same
      reason) as the auto-accept checkbox's checked state, above. '''
      nud = NumericUpDown()
      nud.Dock = DockStyle.Fill
      nud.Visible = self.__config.show_covers_b
      nud.Minimum = 1
      nud.Maximum = 100
      nud.Value = max(nud.Minimum, min(nud.Maximum, int(
         self.__config.session_data_map.get('auto_accept_threshold_n',
            self.__DEFAULT_AUTO_ACCEPT_THRESHOLD_N))))
      nud.ValueChanged += self.__auto_accept_threshold_changed_fired
      tip = ToolTip()
      tip.SetToolTip(nud, i18n.get("IssueCoverPanelAutoAcceptTooltip"))
      return nud

   # ==========================================================================
   def __build_auto_accept_status_label(self):
      ''' builds and returns the label that shows the auto-accept/skip
      countdown (with a clickable "Cancel" link to stop it); empty (and
      inert) whenever no countdown is running. '''
      label = LinkLabel()
      label.UseMnemonic = False
      label.AutoSize = False
      label.Visible = self.__config.show_covers_b
      label.Dock = DockStyle.Fill
      label.TextAlign = ContentAlignment.MiddleCenter
      label.LinkClicked += self.__auto_accept_cancel_clicked_fired
      return label

   # ==========================================================================
   def __build_nextbutton(self):
      button = Button()
      button.Dock = DockStyle.Fill
      button.Text = '>'
      button.Font = Font(button.Font, FontStyle.Bold)
      button.UseVisualStyleBackColor = True
      button.Click += self.__button_click_fired
      return button

   # ==========================================================================
   def __build_prevbutton(self):
      button = Button()
      button.Dock = DockStyle.Fill
      button.Text = '<'
      button.Font = Font(button.Font, FontStyle.Bold)
      button.UseVisualStyleBackColor = True
      button.Click += self.__button_click_fired
      return button

   # ==========================================================================
   def free(self):
      if self.__book is not None:
         log.debug('IssueCoverPanel[%s]: closing (local hash ready=%s, '
            'value=%s)' % (sstr(getattr(self.__book, 'path_s', None)),
               self.__local_hash_ready_b, sstr(self.__local_hash)))
      if type(self.__ref) == IssueRef:
         issue_ref = self.__ref
         button_model = self.__button_cache[issue_ref]
         if button_model and button_model.can_decrement():
            image_ref = button_model.get_current_ref()
            if utils.is_string(image_ref):
               self.__alt_cover_choice = (issue_ref, image_ref)
      self.__finder_scheduler.shutdown(False)
      self.__setter_scheduler.shutdown(False)
      self.__local_hash_scheduler.shutdown(False)
      self.__match_scheduler.shutdown(False)
      self.set_ref(None)
      self.__auto_accept_timer.Stop()
      self.__auto_accept_timer.Dispose()
      self.__coverpanel.free()
      self.__prevbutton = None
      self.__nextbutton = None
      self.__label = None
      self.__match_label = None
      self.__auto_accept_checkbox = None
      self.__auto_accept_threshold_nud = None
      self.__auto_accept_status_label = None
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
         self.__trigger_match_update(None)
      else:
         if not cache.has_key(ref):
            cache[ref] = _ButtonModel(ref, 'searched' if type(ref) == SeriesRef else 'not-searched')
         bmodel = cache[ref]
         cover_image.set_image_ref( bmodel.get_current_ref() )
         nextbutton.Visible = cover_image.Visible and bmodel.can_increment()
         prevbutton.Visible = cover_image.Visible and bmodel.can_decrement()
         self.__trigger_match_update(bmodel.get_current_ref())
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

   # ==========================================================================
   def __compute_local_hash(self):
      ''' Computes (in the background) the image hash of self.__book's own
      cover, i.e. the first page of the comic being scraped -- this is
      compared against remote covers as they're shown, to produce a match
      percentage (see __trigger_match_update). Has no effect if this panel
      wasn't built with a 'book'. '''
      book = self.__book
      path_s = sstr(getattr(book, 'path_s', None)) if book else '?'
      log.debug('IssueCoverPanel[%s]: local hash computation queued' % path_s)
      def task():
         hash_val = None
         try:
            image = book.create_image_of_page(0) if book else None
            if not image:
               log.debug('IssueCoverPanel[%s]: no page-0 image to hash' % path_s)
            else:
               try:
                  image = utils.strip_back_cover(image)
                  hash_val = imagehash.hash(image)
                  log.debug('IssueCoverPanel[%s]: local hash computed -> %s'
                     % (path_s, sstr(hash_val)))
               finally:
                  image.Dispose()
         except Exception:
            log.debug_exc('IssueCoverPanel[%s]: local hash computation failed'
               % path_s)
         def apply():
            self.__local_hash = hash_val
            self.__local_hash_ready_b = True
            log.debug('IssueCoverPanel[%s]: local hash ready (value=%s) '
               '-- refreshing whatever cover is on screen'
               % (path_s, sstr(hash_val)))
            # any match % computed while this was still pending was never
            # cached (see __trigger_match_update) -- now that we finally
            # know the local hash (or that it's unavailable), re-check
            # whatever cover is currently on screen.
            if self.__ref is not None and self.__button_cache.has_key(self.__ref):
               self.__trigger_match_update(
                  self.__button_cache[self.__ref].get_current_ref())
         utils.invoke(self, apply, False)
      self.__local_hash_scheduler.submit(task)

   # ==========================================================================
   def __trigger_match_update(self, ref):
      ''' Updates (computing in the background if needed) the match-percent
      label to reflect how similar the local book's cover is to the remote
      cover identified by 'ref' (None clears the label). Has no effect if
      this panel wasn't built with a 'book'. '''
      if self.__match_label is None:
         return
      if ref is None:
         self.__set_match_text(None)
         self.__cancel_auto_accept()
         return
      if ref in self.__match_cache:
         log.debug('IssueCoverPanel: match cache hit for %s -> %s%%'
            % (sstr(ref), sstr(self.__match_cache[ref])))
         self.__set_match_text(self.__match_cache[ref])
         self.__evaluate_auto_accept(ref, self.__match_cache[ref])
         return
      # a genuinely new (uncached) cover is about to be evaluated -- any
      # countdown still running belongs to whatever was shown before it
      self.__cancel_auto_accept()
      log.debug('IssueCoverPanel: match compute queued for %s '
         '(local hash ready=%s)' % (sstr(ref), self.__local_hash_ready_b))
      self.__match_label.Text = i18n.get("IssueCoverPanelMatchComputing")
      def compute():
         pct_n = None
         ready_b = self.__local_hash_ready_b
         local_hash = self.__local_hash
         try:
            if ready_b and local_hash is not None:
               image = db.query_image(ref)
               if not image:
                  log.debug('IssueCoverPanel: no remote image for %s' % sstr(ref))
               else:
                  try:
                     remote_hash = imagehash.hash(image)
                     pct_n = int(round(
                        imagehash.similarity(local_hash, remote_hash) * 100))
                  finally:
                     image.Dispose()
         except Exception:
            log.debug_exc('IssueCoverPanel: match compute failed for %s'
               % sstr(ref))
         def apply():
            if not ready_b:
               # the local hash wasn't ready yet when this task started --
               # leave the "comparing" text as-is (don't cache anything
               # either), and wait for __compute_local_hash to retrigger
               # this once it's ready, instead of getting stuck showing
               # "comparing" forever.
               log.debug('IssueCoverPanel: local hash still not ready -- '
                  'leaving "%s" showing for %s'
                  % (self.__match_label.Text if self.__match_label else '?',
                     sstr(ref)))
               return
            self.__match_cache[ref] = pct_n
            log.debug('IssueCoverPanel: match result for %s = %s'
               % (sstr(ref), sstr(pct_n)))
            current_ref = self.__button_cache[self.__ref].get_current_ref() \
               if self.__ref is not None \
               and self.__button_cache.has_key(self.__ref) else None
            if current_ref == ref:
               self.__set_match_text(pct_n)
               self.__evaluate_auto_accept(ref, pct_n)
            else:
               log.debug('IssueCoverPanel: match for %s arrived after the '
                  'cover moved on (now showing %s) -- not displayed'
                  % (sstr(ref), sstr(current_ref)))
         utils.invoke(self, apply, False)
      self.__match_scheduler.submit(compute)

   # ==========================================================================
   def __set_match_text(self, pct_n):
      ''' Shows the given match percentage (an int, or None if unavailable)
      in the match-percent label. '''
      if self.__match_label is None:
         return
      self.__match_label.Text = i18n.get("IssueCoverPanelMatchPercent") \
         .format(sstr(pct_n)) if pct_n is not None else ''

   # ==========================================================================
   def __evaluate_auto_accept(self, ref, pct_n):
      ''' Called whenever a real match result (pct_n, possibly None if it
      couldn't be determined) is settled for 'ref', which must be the
      cover currently on screen. If the auto-accept checkbox is checked,
      (re)starts the countdown -- towards accepting if pct_n meets the
      threshold, towards skipping otherwise. Does nothing if the checkbox
      is unchecked, or if a countdown for this same ref is already
      running (so a spurious re-trigger, e.g. "(more covers)" finishing
      its search, doesn't reset an in-progress countdown). '''
      if self.__auto_accept_checkbox is None or \
            not self.__auto_accept_checkbox.Checked:
         return
      if self.__auto_accept_timer.Enabled and \
            self.__auto_accept_active_ref == ref:
         return
      threshold_n = int(self.__auto_accept_threshold_nud.Value)
      accept_b = pct_n is not None and pct_n >= threshold_n
      log.debug('IssueCoverPanel: auto-%s countdown starting for %s '
         '(match=%s, threshold=%s)' % ('accept' if accept_b else 'skip',
            sstr(ref), sstr(pct_n), threshold_n))
      self.__auto_accept_active_ref = ref
      self.__start_auto_accept(accept_b)

   # ==========================================================================
   def __start_auto_accept(self, accept_b):
      ''' (re)starts the auto-accept/skip countdown from
      __AUTO_ACCEPT_SECONDS_N, ending in an accept if 'accept_b', a skip
      otherwise. '''
      self.__auto_accept_timer.Stop()
      self.__auto_accept_will_accept_b = accept_b
      self.__auto_accept_seconds_left_n = self.__AUTO_ACCEPT_SECONDS_N
      self.__update_auto_accept_label()
      self.__auto_accept_timer.Start()

   # ==========================================================================
   def __cancel_auto_accept(self):
      ''' Stops the auto-accept/skip countdown (if running) and clears its
      status label; harmless to call when it isn't running. '''
      self.__auto_accept_timer.Stop()
      self.__auto_accept_active_ref = None
      if self.__auto_accept_status_label is not None:
         self.__auto_accept_status_label.Links.Clear()
         self.__auto_accept_status_label.Text = ''

   # ==========================================================================
   def __auto_accept_tick_fired(self, sender, args):
      ''' Called once per second while the auto-accept/skip countdown
      runs. '''
      self.__auto_accept_seconds_left_n -= 1
      if self.__auto_accept_seconds_left_n <= 0:
         accept_b = self.__auto_accept_will_accept_b
         self.__cancel_auto_accept()
         callback = self.__on_auto_accept if accept_b else self.__on_auto_skip
         if callback:
            callback()
      else:
         self.__update_auto_accept_label()

   # ==========================================================================
   def __update_auto_accept_label(self):
      ''' Refreshes the status label to show the current countdown value
      (accepting or skipping, whichever this countdown will end in), with
      a clickable "Cancel" link appended to it. '''
      label = self.__auto_accept_status_label
      if label is None:
         return
      key = "IssueCoverPanelAutoAcceptCountdownAccept" \
         if self.__auto_accept_will_accept_b \
         else "IssueCoverPanelAutoAcceptCountdownSkip"
      countdown_s = i18n.get(key).format(self.__auto_accept_seconds_left_n)
      cancel_s = i18n.get("IssueCoverPanelAutoAcceptCancel")
      label.Text = countdown_s + "  " + cancel_s
      label.Links.Clear()
      label.Links.Add(len(countdown_s) + 2, len(cancel_s))

   # ==========================================================================
   def __auto_accept_cancel_clicked_fired(self, sender, args):
      ''' Called when the user clicks the "Cancel" link in the countdown. '''
      self.__cancel_auto_accept()

   # ==========================================================================
   def __auto_accept_checkbox_changed_fired(self, sender, args):
      ''' Called whenever the user (un)checks the auto-accept checkbox. '''
      checked_b = self.__auto_accept_checkbox.Checked
      self.__config.session_data_map['auto_accept_high_matches_b'] = checked_b
      if not checked_b:
         self.__cancel_auto_accept()

   # ==========================================================================
   def __auto_accept_threshold_changed_fired(self, sender, args):
      ''' Called whenever the user changes the auto-accept threshold. '''
      self.__config.session_data_map['auto_accept_threshold_n'] = \
         int(self.__auto_accept_threshold_nud.Value)

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
