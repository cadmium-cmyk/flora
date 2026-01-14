import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

class JournalView:
    def __init__(self, window, db, builder):
        self.window = window
        self.db = db

        # --- UI References ---
        # Note: builder.journal_text_view is gone now
        self.stack = builder.journal_stack
        self.list_box = builder.journal_list
        self.new_btn = builder.journal_new_btn
        self.empty_btn = builder.journal_empty_add_btn

        # --- Connect Signals ---
        self.new_btn.connect("clicked", self._on_new_entry_clicked)
        self.empty_btn.connect("clicked", self._on_new_entry_clicked)

    def refresh(self):
        """Reloads the journal list from the database."""
        self._clear_list()
        entries = self.db.get_journal_entries()
        
        if not entries:
            self.stack.set_visible_child_name("empty")
        else:
            self.stack.set_visible_child_name("list")
            for j_id, title, content, date_str in entries:
                display_title = title if title else date_str
                row = Adw.ActionRow(title=display_title)
                
                # Date Label
                date_lbl = Gtk.Label(label=date_str)
                date_lbl.add_css_class("dim-label")
                row.add_suffix(date_lbl)
                
                # Edit button
                edit_btn = Gtk.Button(icon_name="document-edit-symbolic", valign=Gtk.Align.CENTER)
                edit_btn.add_css_class("flat")
                edit_btn.connect("clicked", lambda b, jid=j_id, t=title, c=content: self.window.open_journal_editor(jid, t, c))
                row.add_suffix(edit_btn)
                
                # Delete button
                del_btn = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER)
                del_btn.add_css_class("flat")
                del_btn.connect("clicked", lambda b, jid=j_id, r=row: self._remove_entry(jid, r))
                
                row.add_suffix(del_btn)
                self.list_box.append(row)

    def _on_new_entry_clicked(self, btn):
        self.window.open_journal_editor()

    def _remove_entry(self, j_id, row):
        if self.db.delete_journal_entry(j_id):
            self.list_box.remove(row)
            if self.list_box.get_first_child() is None:
                self.stack.set_visible_child_name("empty")
            self.window.show_toast("Journal entry deleted")

    def _clear_list(self):
        while child := self.list_box.get_first_child():
            self.list_box.remove(child)
