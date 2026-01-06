import sqlite3
import os
from datetime import datetime
from gi.repository import Gtk, Adw
from database import calculate_age

def apply_margins(widget, amount=18):
    widget.set_margin_start(amount); widget.set_margin_end(amount)
    widget.set_margin_top(amount); widget.set_margin_bottom(amount)

def create_button_box(parent_dialog, action_label, action_callback, is_suggested=True):
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    box.set_halign(Gtk.Align.END)
    cancel_btn = Gtk.Button(label="Cancel")
    cancel_btn.connect("clicked", lambda _: parent_dialog.close())
    action_btn = Gtk.Button(label=action_label)
    if is_suggested: action_btn.add_css_class("suggested-action")
    action_btn.connect("clicked", action_callback)
    box.append(cancel_btn); box.append(action_btn)
    return box

class AddTaskDialog(Adw.Window):
    def __init__(self, parent, callback):
        super().__init__(transient_for=parent, modal=True, title="New Task")
        self.callback = callback
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12); apply_margins(content)
        group = Adw.PreferencesGroup()
        self.desc_entry = Adw.EntryRow(title="Description")
        group.add(self.desc_entry)
        content.append(group); content.append(create_button_box(self, "Add Task", self.on_add))
        self.set_content(content)
    def on_add(self, _):
        desc = self.desc_entry.get_text().strip()
        if desc:
            conn = sqlite3.connect('flora.db')
            conn.execute("INSERT INTO tasks (description, due_date) VALUES (?, date('now'))", (desc,))
            conn.commit(); conn.close(); self.callback(); self.close()

class AddPlantDialog(Adw.Window):
    def __init__(self, parent, callback):
        super().__init__(transient_for=parent, modal=True, title="Add New Plant")
        self.callback = callback
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12); apply_margins(content)
        group = Adw.PreferencesGroup(); self.name_entry = Adw.EntryRow(title="Nickname")
        self.guide_ids, self.guide_model = [0], Gtk.StringList.new(["Manual Entry"])
        conn = sqlite3.connect('flora.db')
        for gid, spec in conn.execute("SELECT id, species FROM care_guides ORDER BY species"):
            self.guide_ids.append(gid); self.guide_model.append(spec)
        self.guide_row = Adw.ComboRow(title="Species", model=self.guide_model)
        self.guide_row.connect("notify::selected", self.on_guide_selected)
        self.interval_adj = Gtk.Adjustment(value=7, lower=1, upper=60, step_increment=1)
        self.interval_spin = Gtk.SpinButton(adjustment=self.interval_adj, valign=Gtk.Align.CENTER)
        self.interval_row = Adw.ActionRow(title="Watering Interval (Days)")
        self.interval_row.add_suffix(self.interval_spin)
        self.sun_model = Gtk.StringList.new(["Full Sun", "Partial Shade", "Full Shade"])
        self.sun_row = Adw.ComboRow(title="Sunlight", model=self.sun_model)
        self.garden_ids, self.garden_model = [None], Gtk.StringList.new(["Unassigned"])
        for gid, name in conn.execute("SELECT id, name FROM gardens"):
            self.garden_ids.append(gid); self.garden_model.append(name)
        conn.close(); self.garden_row = Adw.ComboRow(title="Location", model=self.garden_model)
        group.add(self.name_entry); group.add(self.guide_row); group.add(self.interval_row); group.add(self.sun_row); group.add(self.garden_row)
        content.append(group); content.append(create_button_box(self, "Add Plant", self.on_add)); self.set_content(content)
    
    def on_guide_selected(self, *args):
        idx = self.guide_row.get_selected(); guide_id = self.guide_ids[idx]
        if guide_id == 0: return
        conn = sqlite3.connect('flora.db'); res = conn.execute("SELECT sunlight, interval FROM care_guides WHERE id=?", (guide_id,)).fetchone(); conn.close()
        if res:
            self.interval_spin.set_value(res[1])
            for i, s in enumerate(["Full Sun", "Partial Shade", "Full Shade"]):
                if s == res[0]: self.sun_row.set_selected(i)

    def on_add(self, _):
        if self.name_entry.get_text():
            gid = self.garden_ids[self.garden_row.get_selected()]; sun = self.sun_model.get_string(self.sun_row.get_selected())
            iv = int(self.interval_spin.get_value()); spec_id = self.guide_ids[self.guide_row.get_selected()]
            local_today = datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect('flora.db')
            conn.execute("INSERT INTO plants (name, garden_id, planting_date, sunlight, water_interval, species_id) VALUES (?, ?, ?, ?, ?, ?)", 
                         (self.name_entry.get_text(), gid, local_today, sun, iv, spec_id))
            conn.commit(); conn.close(); self.callback(); self.close()

# Note: Additional dialogs (EditPlantDialog, AddGardenDialog, etc.) should also be moved here.
