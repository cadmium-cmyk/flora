import sqlite3
import os
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw
from ui_components import AddJournalDialog, EditJournalDialog
from database import get_db_path, get_all_journal_entries

class PlantDetailView(Adw.NavigationPage):
    def __init__(self, plant_id, plant_name):
        super().__init__(title=plant_name); self.plant_id = plant_id
        view = Adw.ToolbarView(); view.add_top_bar(Adw.HeaderBar())
        pref = Adw.PreferencesPage()
        wrapper_group = Adw.PreferencesGroup()
        self.journal_stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        self.list_box = Gtk.ListBox(css_classes=["boxed-list"])
        journal_group = Adw.PreferencesGroup(title="Journal Entries")
        journal_group.add(self.list_box)
        add_btn = Gtk.Button(icon_name="list-add-symbolic", css_classes=["flat"])
        add_btn.connect("clicked", lambda _: AddJournalDialog(self.get_native(), self.plant_id, self.refresh).present())
        journal_group.set_header_suffix(add_btn)
        self.journal_stack.add_named(journal_group, "list")
        self.journal_empty = Adw.StatusPage(title="No Journal Entries", icon_name="edit-paste-symbolic", description="Start tracking growth by adding notes.")
        empty_add = Gtk.Button(label="Add Entry", halign=Gtk.Align.CENTER, css_classes=["suggested-action", "pill"])
        empty_add.connect("clicked", lambda _: AddJournalDialog(self.get_native(), self.plant_id, self.refresh).present())
        self.journal_empty.set_child(empty_add); self.journal_stack.add_named(self.journal_empty, "empty")
        wrapper_group.add(self.journal_stack); pref.add(wrapper_group); view.set_content(pref); self.set_child(view); self.refresh()

    def refresh(self):
        while (c := self.list_box.get_first_child()): self.list_box.remove(c)
        conn = sqlite3.connect(get_db_path()); count = 0
        for eid, date, note, status, photo in conn.execute("SELECT id, entry_date, note, status, photo FROM journal_entries WHERE plant_id = ? ORDER BY id DESC", (self.plant_id,)):
            count += 1
            row = Adw.ActionRow(title=note, subtitle=date, activatable=True)
            row.connect("activated", lambda r, e=eid, n=note, p=photo: EditJournalDialog(self.get_native(), e, n, p, self.refresh).present())
            if photo and os.path.exists(photo):
                img = Gtk.Image.new_from_file(photo); img.set_pixel_size(60); img.set_margin_end(12); row.add_prefix(img)
            del_btn = Gtk.Button(icon_name="user-trash-symbolic", css_classes=["flat", "error"], valign=Gtk.Align.CENTER)
            del_btn.connect("clicked", lambda b, i=eid: self.delete_entry(i))
            row.add_suffix(del_btn); self.list_box.append(row)
        conn.close(); self.journal_stack.set_visible_child_name("list" if count > 0 else "empty")

    def delete_entry(self, eid):
        conn = sqlite3.connect(get_db_path()); conn.execute("DELETE FROM journal_entries WHERE id=?", (eid,)); conn.commit(); conn.close(); self.refresh()

# class GlobalJournalView(Adw.Bin):
    # def __init__(self):
        # super().__init__()
        # self.list_box = Gtk.ListBox(css_classes=["boxed-list"])
        
        # pref_page = Adw.PreferencesPage()
        # group = Adw.PreferencesGroup(title="Garden History")
        # group.add(self.list_box)
        # pref_page.add(group)
        
        # self.set_child(pref_page)

    # def refresh(self):
        # # Clear existing rows
        # while (c := self.list_box.get_first_child()):
            # self.list_box.remove(c)
            
        # entries = get_all_journal_entries()
        # for eid, date, note, p_name, photo in entries:
            # row = Adw.ActionRow(title=note, subtitle=f"{p_name} — {date}")
            
            # if photo and os.path.exists(photo):
                # img = Gtk.Image.new_from_file(photo)
                # img.set_pixel_size(40)
                # img.set_margin_end(12)
                # row.add_prefix(img)
            # self.list_box.append(row)

# class GlobalJournalView(Adw.Bin):
    # def __init__(self, main_stack):
        # super().__init__()
        # self.main_stack = main_stack
        
        # # Stack to switch between the list and the empty state
        # self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        
        # # 1. Setup the List View
        # self.list_box = Gtk.ListBox(css_classes=["boxed-list"])
        # pref_page = Adw.PreferencesPage()
        # group = Adw.PreferencesGroup(title="Garden History")
        # group.add(self.list_box)
        # pref_page.add(group)
        # self.stack.add_named(pref_page, "list")
        
        # # 2. Setup the Empty State
        # self.empty_page = Adw.StatusPage(
            # title="No History Yet",
            # icon_name="view-list-bullet-symbolic",
            # description="Your garden journal entries will appear here."
        # )
        
        # # Call to Action: Jump to the 'lib' page defined in main.py
        # action_btn = Gtk.Button(
            # label="View My Plants",
            # halign=Gtk.Align.CENTER,
            # css_classes=["suggested-action", "pill"]
        # )
        # action_btn.connect("clicked", self.on_jump_to_plants)
        
        # self.empty_page.set_child(action_btn)
        # self.stack.add_named(self.empty_page, "empty")
        
        # self.set_child(self.stack)

    # def on_jump_to_plants(self, button):
        # # Switches the main stack to the 'lib' page
        # self.main_stack.set_visible_child_name("lib")

    # def refresh(self):
        # # Clear rows
        # while (c := self.list_box.get_first_child()):
            # self.list_box.remove(c)
            
        # entries = get_all_journal_entries()
        # count = len(entries)
        
        # for eid, date, note, p_name, photo in entries:
            # row = Adw.ActionRow(title=note, subtitle=f"{p_name} — {date}")
            
            # if photo and os.path.exists(photo):
                # img = Gtk.Image.new_from_file(photo)
                # img.set_pixel_size(40)
                # img.set_margin_end(12)
                # row.add_prefix(img)
            # self.list_box.append(row)
            
        # # Switch visible child based on content
        # self.stack.set_visible_child_name("list" if count > 0 else "empty")
class GlobalJournalView(Adw.Bin):
    def __init__(self, main_stack):
        super().__init__()
        self.main_stack = main_stack
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        
        # List State
        self.list_box = Gtk.ListBox(css_classes=["boxed-list"])
        pref_page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Garden History")
        group.add(self.list_box)
        pref_page.add(group)
        self.stack.add_named(pref_page, "list")
        
        # Empty State
        self.empty_page = Adw.StatusPage(
            title="No History Yet", 
            icon_name="view-list-bullet-symbolic",
            description="Your garden journal entries will appear here."
        )
        action_btn = Gtk.Button(label="View My Plants", halign=Gtk.Align.CENTER, css_classes=["suggested-action", "pill"])
        action_btn.connect("clicked", lambda _: self.main_stack.set_visible_child_name("lib"))
        self.empty_page.set_child(action_btn)
        self.stack.add_named(self.empty_page, "empty")
        
        self.set_child(self.stack)

    def refresh(self):
        while (c := self.list_box.get_first_child()): self.list_box.remove(c)
        entries = get_all_journal_entries()
        for eid, date, note, p_name, photo in entries:
            row = Adw.ActionRow(title=note, subtitle=f"{p_name} — {date}")
            self.list_box.append(row)
        self.stack.set_visible_child_name("list" if len(entries) > 0 else "empty")
