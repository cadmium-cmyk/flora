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

        # --- Connect Signals ---
        self.new_btn.connect("clicked", self._on_new_entry_clicked)

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
                row.set_subtitle(content)
                
                # Delete button
                del_btn = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER)
                del_btn.add_css_class("flat")
                del_btn.connect("clicked", lambda b, jid=j_id, r=row: self._remove_entry(jid, r))
                
                row.add_suffix(del_btn)
                self.list_box.append(row)

    def _on_new_entry_clicked(self, btn):
        # Create the dialog
        dialog = Adw.MessageDialog(
            transient_for=self.window,
            heading="New Journal Entry"
        )
        
        # Create a text view for input
        text_view = Gtk.TextView()
        text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        text_view.set_size_request(-1, 150)
        text_view.add_css_class("card")
        
        # Put it in a scrolled window
        scroller = Gtk.ScrolledWindow()
        scroller.set_child(text_view)
        scroller.set_min_content_height(150)
        scroller.set_propagate_natural_height(True)
        
        dialog.set_extra_child(scroller)
        
        # Add buttons
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        
        # Handle response
        dialog.connect("response", lambda d, r: self._on_dialog_response(d, r, text_view))
        dialog.present()

    def _on_dialog_response(self, dialog, response, text_view):
        if response == "save":
            buf = text_view.get_buffer()
            text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
            
            if text.strip():
                # Generate a simple title from the content
                title = text.split('\n')[0][:30]
                if len(title) < len(text.split('\n')[0]):
                    title += "..."
                    
                if self.db.add_journal_entry(title, text):
                    self.refresh()
                    self.window.show_toast("Journal entry saved!")
                else:
                    self.window.show_toast("Error saving entry")
            else:
                self.window.show_toast("Entry cannot be empty")
                
        dialog.close()

    def _remove_entry(self, j_id, row):
        if self.db.delete_journal_entry(j_id):
            self.list_box.remove(row)
            if self.list_box.get_first_child() is None:
                self.stack.set_visible_child_name("empty")
            self.window.show_toast("Journal entry deleted")

    def _clear_list(self):
        while child := self.list_box.get_first_child():
            self.list_box.remove(child)
