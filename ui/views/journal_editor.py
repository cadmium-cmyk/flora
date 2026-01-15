import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Pango

class JournalEditorView:
    def __init__(self, window, db, builder):
        self.window = window
        self.db = db
        
        # --- UI References ---
        self.back_btn = builder.editor_back_btn
        self.save_btn = builder.editor_save_btn
        self.title_entry = builder.editor_title_entry
        self.text_view = builder.editor_text_view
        
        # Toolbar buttons
        self.bold_btn = builder.editor_bold_btn
        self.italic_btn = builder.editor_italic_btn
        self.underline_btn = builder.editor_underline_btn
        
        self.align_left_btn = builder.editor_align_left_btn
        self.align_center_btn = builder.editor_align_center_btn
        self.align_right_btn = builder.editor_align_right_btn
        self.align_fill_btn = builder.editor_align_fill_btn
        
        # Internal State
        self.current_entry_id = None
        self.active_tags = set()
        self.ignore_mark_set = False
        
        # --- Connect Signals ---
        self.back_btn.connect("clicked", self._on_cancel_clicked)
        self.save_btn.connect("clicked", self._on_save_clicked)
        
        self.bold_btn.connect("clicked", lambda b: self._apply_tag("bold"))
        self.italic_btn.connect("clicked", lambda b: self._apply_tag("italic"))
        self.underline_btn.connect("clicked", lambda b: self._apply_tag("underline"))
        
        self.align_left_btn.connect("clicked", lambda b: self._apply_alignment(Gtk.Justification.LEFT))
        self.align_center_btn.connect("clicked", lambda b: self._apply_alignment(Gtk.Justification.CENTER))
        self.align_right_btn.connect("clicked", lambda b: self._apply_alignment(Gtk.Justification.RIGHT))
        self.align_fill_btn.connect("clicked", lambda b: self._apply_alignment(Gtk.Justification.FILL))

        self._setup_formatting()

    def _setup_formatting(self):
        buf = self.text_view.get_buffer()
        buf.connect("mark-set", self._on_mark_set)
        buf.connect("insert-text", self._on_insert_text_before)
        buf.connect_after("insert-text", self._on_insert_text_after)
        
        # Create tags
        if not buf.get_tag_table().lookup("bold"):
            tag = buf.create_tag("bold", weight=Pango.Weight.BOLD)
        if not buf.get_tag_table().lookup("italic"):
            tag = buf.create_tag("italic", style=Pango.Style.ITALIC)
        if not buf.get_tag_table().lookup("underline"):
            tag = buf.create_tag("underline", underline=Pango.Underline.SINGLE)
        
        # Alignment tags
        if not buf.get_tag_table().lookup("align_left"):
            buf.create_tag("align_left", justification=Gtk.Justification.LEFT)
        if not buf.get_tag_table().lookup("align_center"):
            buf.create_tag("align_center", justification=Gtk.Justification.CENTER)
        if not buf.get_tag_table().lookup("align_right"):
            buf.create_tag("align_right", justification=Gtk.Justification.RIGHT)
        if not buf.get_tag_table().lookup("align_fill"):
            buf.create_tag("align_fill", justification=Gtk.Justification.FILL)

    def open_entry(self, entry_id=None, title="", content=""):
        self.current_entry_id = entry_id
        
        # Set content
        self.title_entry.set_text(title if title else "")
        buf = self.text_view.get_buffer()
        buf.set_text(content if content else "")
        
        # Focus title if new, else text
        if not entry_id:
            self.title_entry.grab_focus()
        else:
            self.text_view.grab_focus()

    def _apply_tag(self, tag_name):
        buf = self.text_view.get_buffer()
        if buf.get_has_selection():
            start, end = buf.get_selection_bounds()
            
            # Check if tag is present on selection
            # Iterate through selection to check presence? Or just assume toggle logic based on start?
            # Standard toggling: If range has tag anywhere or fully?
            # Let's check first char.
            has_tag = start.has_tag(buf.get_tag_table().lookup(tag_name))
            
            if has_tag:
                buf.remove_tag_by_name(tag_name, start, end)
                if tag_name in self.active_tags:
                    self.active_tags.remove(tag_name)
            else:
                buf.apply_tag_by_name(tag_name, start, end)
                self.active_tags.add(tag_name)
        else:
            # Toggle active state for typing
            if tag_name in self.active_tags:
                self.active_tags.remove(tag_name)
                # self.window.show_toast(f"{tag_name} off")
            else:
                self.active_tags.add(tag_name)
                # self.window.show_toast(f"{tag_name} on")

    def _update_active_tags_from_cursor(self):
        buf = self.text_view.get_buffer()
        cursor = buf.get_iter_at_mark(buf.get_insert())
        
        # Tags at cursor
        tags = cursor.get_tags()
        tag_names = [t.get_property("name") for t in tags]
        
        # Update active_tags to match cursor context
        # Only for formatting tags
        for t in ["bold", "italic", "underline"]:
            if t in tag_names:
                self.active_tags.add(t)
            else:
                if t in self.active_tags:
                    self.active_tags.remove(t)

    def _on_mark_set(self, buf, iter, mark):
        if self.ignore_mark_set:
            return
        if mark.get_name() == "insert":
            self._update_active_tags_from_cursor()

    def _on_insert_text_before(self, buf, location, text, length):
        self.ignore_mark_set = True

    def _on_insert_text_after(self, buf, location, text, length):
        # location points to end of inserted text
        end = location
        start = end.copy()
        start.backward_chars(length)
        
        for tag in self.active_tags:
            buf.apply_tag_by_name(tag, start, end)
            
        self.ignore_mark_set = False
        # No need to update active tags from cursor here as we want to keep what we had
        # But if we moved cursor implicitly, we might want to check? 
        # Actually, we enforced active tags on the new text, so cursor (at end) will have them.
        # So updating is safe.
        self._update_active_tags_from_cursor()

    def _apply_alignment(self, justification):
        buf = self.text_view.get_buffer()
        
        # Determine tag name
        tag_name = "align_left"
        if justification == Gtk.Justification.CENTER:
            tag_name = "align_center"
        elif justification == Gtk.Justification.RIGHT:
            tag_name = "align_right"
        elif justification == Gtk.Justification.FILL:
            tag_name = "align_fill"
            
        # Apply to current line(s)
        # Even if no selection, we want to align the current paragraph
        
        if buf.get_has_selection():
            start, end = buf.get_selection_bounds()
        else:
            # Get current line
            cursor = buf.get_insert()
            iter_at = buf.get_iter_at_mark(cursor)
            start = iter_at.copy()
            start.set_line_offset(0)
            end = iter_at.copy()
            if not end.ends_line():
                end.forward_to_line_end()
        
        # Remove existing alignment tags
        for t in ["align_left", "align_center", "align_right", "align_fill"]:
            buf.remove_tag_by_name(t, start, end)
            
        buf.apply_tag_by_name(tag_name, start, end)

    def _on_save_clicked(self, btn):
        buf = self.text_view.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        title = self.title_entry.get_text().strip()
        
        if not title:
            self.window.show_toast("Title is required")
            return

        if text.strip() or title:
            success = False
            if self.current_entry_id:
                success = self.db.update_journal_entry(self.current_entry_id, title, text)
            else:
                success = self.db.add_journal_entry(title, text)
                
            if success:
                self.window.close_journal_editor(saved=True)
                self.window.show_toast("Journal entry saved!")
            else:
                self.window.show_toast("Error saving entry")
        else:
            self.window.show_toast("Entry cannot be empty")

    def _on_cancel_clicked(self, btn):
        self.window.close_journal_editor(saved=False)
