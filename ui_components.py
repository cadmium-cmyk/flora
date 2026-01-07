import sqlite3
import os
from datetime import datetime
from gi.repository import Gtk, Adw
from database import get_db_path

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
            conn = sqlite3.connect(get_db_path())
            conn.execute("INSERT INTO tasks (description, due_date) VALUES (?, date('now'))", (desc,))
            conn.commit(); conn.close(); self.callback(); self.close()

class AddGuideDialog(Adw.Window):
    def __init__(self, parent, callback):
        super().__init__(transient_for=parent, modal=True, title="New Care Guide")
        self.callback = callback
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12); apply_margins(content)
        group = Adw.PreferencesGroup()
        self.species_entry = Adw.EntryRow(title="Species Name")
        self.sun_model = Gtk.StringList.new(["Full Sun", "Partial Shade", "Full Shade"])
        self.sun_row = Adw.ComboRow(title="Ideal Sunlight", model=self.sun_model)
        self.interval_row = Adw.ActionRow(title="Watering Interval (Days)")
        self.interval_adj = Gtk.Adjustment(value=7, lower=1, upper=60, step_increment=1)
        self.interval_spin = Gtk.SpinButton(adjustment=self.interval_adj, valign=Gtk.Align.CENTER)
        self.interval_row.add_suffix(self.interval_spin)
        group.add(self.species_entry); group.add(self.sun_row); group.add(self.interval_row)
        content.append(group); content.append(create_button_box(self, "Create Guide", self.on_add))
        self.set_content(content)
    def on_add(self, _):
        species = self.species_entry.get_text().strip()
        if species:
            sun = self.sun_model.get_string(self.sun_row.get_selected())
            iv = int(self.interval_spin.get_value())
            conn = sqlite3.connect(get_db_path())
            conn.execute("INSERT INTO care_guides (species, sunlight, interval) VALUES (?, ?, ?)", (species, sun, iv))
            conn.commit(); conn.close(); self.callback(); self.close()

class AddPlantDialog(Adw.Window):
    def __init__(self, parent, callback):
        super().__init__(transient_for=parent, modal=True, title="Add New Plant")
        self.callback = callback
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12); apply_margins(content)
        group = Adw.PreferencesGroup(); self.name_entry = Adw.EntryRow(title="Nickname")
        self.guide_ids, self.guide_model = [0], Gtk.StringList.new(["Manual Entry"])
        conn = sqlite3.connect(get_db_path())
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
        conn = sqlite3.connect(get_db_path()); res = conn.execute("SELECT sunlight, interval FROM care_guides WHERE id=?", (guide_id,)).fetchone(); conn.close()
        if res:
            self.interval_spin.set_value(res[1])
            for i, s in enumerate(["Full Sun", "Partial Shade", "Full Shade"]):
                if s == res[0]: self.sun_row.set_selected(i)
    def on_add(self, _):
        if self.name_entry.get_text():
            gid = self.garden_ids[self.garden_row.get_selected()]; sun = self.sun_model.get_string(self.sun_row.get_selected())
            iv = int(self.interval_spin.get_value()); spec_id = self.guide_ids[self.guide_row.get_selected()]
            local_today = datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect(get_db_path())
            conn.execute("INSERT INTO plants (name, garden_id, planting_date, sunlight, water_interval, species_id) VALUES (?, ?, ?, ?, ?, ?)", 
                         (self.name_entry.get_text(), gid, local_today, sun, iv, spec_id))
            conn.commit(); conn.close(); self.callback(); self.close()

class EditPlantDialog(Adw.Window):
    def __init__(self, parent, plant_id, callback):
        super().__init__(transient_for=parent, modal=True, title="Edit Plant")
        self.plant_id, self.callback = plant_id, callback
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12); apply_margins(content)
        group = Adw.PreferencesGroup()
        conn = sqlite3.connect(get_db_path())
        curr = conn.execute("SELECT name, garden_id, sunlight, water_interval FROM plants WHERE id=?", (plant_id,)).fetchone()
        self.name_entry = Adw.EntryRow(title="Plant Name"); self.name_entry.set_text(curr[0])
        self.interval_adj = Gtk.Adjustment(value=curr[3], lower=1, upper=60, step_increment=1)
        self.interval_spin = Gtk.SpinButton(adjustment=self.interval_adj, valign=Gtk.Align.CENTER)
        self.interval_row = Adw.ActionRow(title="Watering Interval (Days)")
        self.interval_row.add_suffix(self.interval_spin)
        self.sun_model = Gtk.StringList.new(["Full Sun", "Partial Shade", "Full Shade"])
        self.sun_row = Adw.ComboRow(title="Sunlight", model=self.sun_model)
        for i, s in enumerate(["Full Sun", "Partial Shade", "Full Shade"]):
            if s == curr[2]: self.sun_row.set_selected(i)
        self.garden_ids, self.garden_model = [None], Gtk.StringList.new(["Unassigned"])
        selected_idx = 0
        for gid, name in conn.execute("SELECT id, name FROM gardens"):
            self.garden_ids.append(gid); self.garden_model.append(name)
            if gid == curr[1]: selected_idx = len(self.garden_ids) - 1
        self.garden_row = Adw.ComboRow(title="Location", model=self.garden_model); self.garden_row.set_selected(selected_idx)
        conn.close()
        group.add(self.name_entry); group.add(self.interval_row); group.add(self.sun_row); group.add(self.garden_row)
        content.append(group); content.append(create_button_box(self, "Save Changes", self.on_save)); self.set_content(content)
    def on_save(self, _):
        gid = self.garden_ids[self.garden_row.get_selected()]
        sun = self.sun_model.get_string(self.sun_row.get_selected())
        iv = int(self.interval_spin.get_value())
        conn = sqlite3.connect(get_db_path())
        conn.execute("UPDATE plants SET name=?, garden_id=?, sunlight=?, water_interval=? WHERE id=?", 
                     (self.name_entry.get_text(), gid, sun, iv, self.plant_id))
        conn.commit(); conn.close(); self.callback(); self.close()

class AddGardenDialog(Adw.Window):
    def __init__(self, parent, callback):
        super().__init__(transient_for=parent, modal=True, title="New Garden")
        self.callback = callback
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12); apply_margins(content)
        group = Adw.PreferencesGroup(); self.name_entry = Adw.EntryRow(title="Garden Name")
        group.add(self.name_entry); content.append(group); content.append(create_button_box(self, "Create", self.on_add)); self.set_content(content)
    def on_add(self, _):
        if self.name_entry.get_text():
            conn = sqlite3.connect(get_db_path()); conn.execute("INSERT INTO gardens (name) VALUES (?)", (self.name_entry.get_text(),)); conn.commit(); conn.close(); self.callback(); self.close()

class AddJournalDialog(Adw.Window):
    def __init__(self, parent, plant_id, callback):
        super().__init__(transient_for=parent, modal=True, title="New Journal Entry")
        self.plant_id, self.callback, self.photo_path = plant_id, callback, None
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12); apply_margins(content)
        group = Adw.PreferencesGroup(); self.note_entry = Adw.EntryRow(title="Note"); group.add(self.note_entry)
        self.photo_row = Adw.ActionRow(title="Attach Photo", subtitle="No photo selected")
        photo_btn = Gtk.Button(icon_name="camera-photo-symbolic", css_classes=["flat"], valign=Gtk.Align.CENTER)
        photo_btn.connect("clicked", self.on_pick_photo); self.photo_row.add_suffix(photo_btn); group.add(self.photo_row)
        content.append(group); content.append(create_button_box(self, "Save Entry", self.on_save)); self.set_content(content)
    def on_pick_photo(self, _):
        dialog = Gtk.FileChooserNative(title="Select Photo", transient_for=self, action=Gtk.FileChooserAction.OPEN)
        dialog.connect("response", self.on_file_response); dialog.show()
    def on_file_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file(); self.photo_path = file.get_path(); self.photo_row.set_subtitle(file.get_basename())
        dialog.destroy()
    def on_save(self, _):
        conn = sqlite3.connect(get_db_path()); conn.execute("INSERT INTO journal_entries (plant_id, entry_date, note, status, photo) VALUES (?, date('now'), ?, 'Note', ?)", (self.plant_id, self.note_entry.get_text(), self.photo_path))
        conn.commit(); conn.close(); self.callback(); self.close()

class EditJournalDialog(Adw.Window):
    def __init__(self, parent, entry_id, note, photo, callback):
        super().__init__(transient_for=parent, modal=True, title="Edit Journal Entry")
        self.entry_id, self.callback, self.photo_path = entry_id, callback, photo
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12); apply_margins(content)
        group = Adw.PreferencesGroup()
        self.note_entry = Adw.EntryRow(title="Note"); self.note_entry.set_text(note); group.add(self.note_entry)
        subtitle = os.path.basename(photo) if photo else "No photo selected"
        self.photo_row = Adw.ActionRow(title="Update Photo", subtitle=subtitle)
        photo_btn = Gtk.Button(icon_name="camera-photo-symbolic", css_classes=["flat"], valign=Gtk.Align.CENTER)
        photo_btn.connect("clicked", self.on_pick_photo); self.photo_row.add_suffix(photo_btn); group.add(self.photo_row)
        content.append(group); content.append(create_button_box(self, "Save Changes", self.on_save)); self.set_content(content)
    def on_pick_photo(self, _):
        dialog = Gtk.FileChooserNative(title="Select Photo", transient_for=self, action=Gtk.FileChooserAction.OPEN)
        dialog.connect("response", self.on_file_response); dialog.show()
    def on_file_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file(); self.photo_path = file.get_path(); self.photo_row.set_subtitle(file.get_basename())
        dialog.destroy()
    def on_save(self, _):
        conn = sqlite3.connect(get_db_path())
        conn.execute("UPDATE journal_entries SET note=?, photo=? WHERE id=?", (self.note_entry.get_text(), self.photo_path, self.entry_id))
        conn.commit(); conn.close(); self.callback(); self.close()

class PerenualSearchDialog(Adw.Window):
    def __init__(self, parent, callback):
        super().__init__(transient_for=parent, modal=True)
        self.set_default_size(450, 500)
        self.set_title("Search Online Guides")
        self.callback = callback
        self.api_key = "sk-W61x695e11741408a14221" # Get from perenual.com

        view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        view.add_top_bar(header)

        # Search Box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        search_entry = Gtk.SearchEntry(placeholder_text="Search common plant name...")
        search_entry.connect("activate", self.on_search)
        vbox.append(search_entry)

        # Results List
        self.list_box = Gtk.ListBox(css_classes=["boxed-list"])
        scrolled = Gtk.ScrolledWindow(propagate_natural_height=True, vexpand=True)
        scrolled.set_child(self.list_box)
        vbox.append(scrolled)

        view.set_content(vbox)
        self.set_content(view)

    def on_search(self, entry):
        query = entry.get_text()
        if not query: return
        # Clear list
        while (c := self.list_box.get_first_child()): self.list_box.remove(c)
        
        # Run API call in a thread to keep UI responsive
        Thread(target=self.fetch_results, args=(query,), daemon=True).start()

    def fetch_results(self, query):
        url = f"https://perenual.com/api/v2/species-list?key={self.api_key}&q={query}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json().get('data', [])
                # Schedule UI update on main thread
                GObject.idle_add(self.update_ui, data)
        except Exception as e:
            print(f"API Error: {e}")

    def update_ui(self, data):
        for item in data:
            row = Adw.ActionRow(title=item.get('common_name', 'Unknown'), subtitle=item.get('scientific_name', [''])[0])
            add_btn = Gtk.Button(icon_name="list-add-symbolic", css_classes=["flat"])
            row.add_suffix(add_btn)
            add_btn.connect("clicked", lambda b, i=item: self.select_plant(i))
            self.list_box.append(row)

    def select_plant(self, item):
        # Map Perenual data to our schema
        sun = ", ".join(item.get('sunlight', []))
        # Default interval logic based on watering string
        water_map = {"Frequent": 3, "Average": 7, "Minimum": 14}
        interval = water_map.get(item.get('watering'), 7)
        
        self.callback(item.get('common_name'), sun, interval)
        self.destroy()
