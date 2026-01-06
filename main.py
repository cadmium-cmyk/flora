import sys
import os
import sqlite3
import gi
from datetime import datetime
from database import get_db_path

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GObject, Gdk
from database import init_db, calculate_age
from ui_components import (
    apply_margins, AddTaskDialog, AddGuideDialog, 
    EditPlantDialog, AddPlantDialog, AddGardenDialog
)
from views import PlantDetailView

class FloraWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_default_size(950, 700); self.set_title("Flora")
        self.nav_view = Adw.NavigationView(); self.stack = Adw.ViewStack(); self.split_view = Adw.NavigationSplitView()
        self.filter_garden_ids, self.filter_model = [None], Gtk.StringList.new(["All Gardens"])
        self.create_dashboard(); self.create_tasks_ui(); self.create_gardens_ui(); self.create_library_ui(); self.create_guides_ui(); self.create_sidebar()
        content_toolbar = Adw.ToolbarView(); content_toolbar.add_top_bar(Adw.HeaderBar()); content_toolbar.set_content(self.stack)
        self.nav_view.push(Adw.NavigationPage.new(content_toolbar, "Flora"))
        self.split_view.set_content(Adw.NavigationPage.new(self.nav_view, "NavWrapper"))
        self.set_content(self.split_view); self.refresh_all()

    def create_sidebar(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); self.sidebar_list = Gtk.ListBox(css_classes=["navigation-sidebar"])
        items = [("dash", "Home", "user-home-symbolic"), ("tasks", "Tasks", "org.gnome.Calendar.Devel-symbolic"), ("gardens", "Gardens", "location-services-active-symbolic"), ("lib", "My Plants", "emoji-nature-symbolic"), ("guides", "Care Guides", "emblem-favorite-symbolic")]
        for tid, label, icon in items:
            row = Adw.ActionRow(title=label, activatable=True); row.add_prefix(Gtk.Image.new_from_icon_name(icon)); row.target_id = tid; self.sidebar_list.append(row)
        self.sidebar_list.connect("row-activated", self.on_sidebar_row_activated)
        box.append(self.sidebar_list); self.split_view.set_sidebar(Adw.NavigationPage.new(box, "Menu"))
        self.theme_btn = Gtk.Button(icon_name="display-brightness-symbolic", css_classes=["circular", "flat"]); self.theme_btn.connect("clicked", self.on_theme_toggle_clicked)
        box.append(Gtk.Box(vexpand=True)); box.append(self.theme_btn)

    def create_dashboard(self):
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        status = Adw.StatusPage(title="Flora", icon_name="emoji-nature-symbolic", description="Ready to grow.")
        page_box.append(status)
        pref_page = Adw.PreferencesPage(); self.thirsty_group = Adw.PreferencesGroup(title="Needs Water"); self.thirsty_list = Gtk.ListBox(css_classes=["boxed-list"])
        self.thirsty_group.add(self.thirsty_list); pref_page.add(self.thirsty_group); page_box.append(pref_page); self.stack.add_named(page_box, "dash")

    def create_tasks_ui(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); apply_margins(bar, 12)
        label = Gtk.Label(label="", xalign=0, css_classes=["title-4"], hexpand=True)
        add_btn = Gtk.Button(icon_name="list-add-symbolic", css_classes=["flat"]); add_btn.connect("clicked", lambda _: AddTaskDialog(self, self.refresh_tasks).present())
        bar.append(label); bar.append(add_btn); page.append(bar)
        self.tasks_stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        pref = Adw.PreferencesPage(); self.tasks_list = Gtk.ListBox(css_classes=["boxed-list"]); group = Adw.PreferencesGroup(); group.add(self.tasks_list); pref.add(group)
        self.tasks_stack.add_named(pref, "list")
        self.tasks_empty = Adw.StatusPage(title="All Caught Up", icon_name="view-list-bullet-symbolic", description="No pending tasks.")
        empty_add = Gtk.Button(label="Add Task", halign=Gtk.Align.CENTER, css_classes=["suggested-action", "pill"])
        empty_add.connect("clicked", lambda _: AddTaskDialog(self, self.refresh_tasks).present())
        self.tasks_empty.set_child(empty_add); self.tasks_stack.add_named(self.tasks_empty, "empty"); page.append(self.tasks_stack); self.stack.add_named(page, "tasks")

    def create_gardens_ui(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); apply_margins(bar, 12)
        self.garden_search = Gtk.SearchEntry(placeholder_text="Search gardens...", hexpand=True); self.garden_search.connect("search-changed", lambda *_: self.refresh_gardens())
        add_btn = Gtk.Button(icon_name="list-add-symbolic", css_classes=["flat"]); add_btn.connect("clicked", lambda _: AddGardenDialog(self, self.refresh_gardens).present())
        bar.append(self.garden_search); bar.append(add_btn); page.append(bar)
        self.garden_stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        pref = Adw.PreferencesPage(); self.garden_list = Gtk.ListBox(css_classes=["boxed-list"])
        group = Adw.PreferencesGroup(title="Garden Locations"); group.add(self.garden_list); pref.add(group); self.garden_stack.add_named(pref, "list")
        self.garden_empty = Adw.StatusPage(title="No Gardens Found", icon_name="emoji-nature-symbolic", description="Add a garden to categorize your plants.")
        self.garden_stack.add_named(self.garden_empty, "empty"); page.append(self.garden_stack); self.stack.add_named(page, "gardens")

    def create_library_ui(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); apply_margins(bar, 12)
        self.lib_search = Gtk.SearchEntry(placeholder_text="Search plants...", hexpand=True); self.lib_search.connect("search-changed", lambda *_: self.refresh_library())
        add_btn = Gtk.Button(icon_name="list-add-symbolic", css_classes=["flat"]); add_btn.connect("clicked", lambda _: AddPlantDialog(self, self.refresh_all).present())
        bar.append(self.lib_search); bar.append(add_btn); page.append(bar)
        self.lib_stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        pref = Adw.PreferencesPage(); self.filter_row = Adw.ComboRow(title="Filter Garden", model=self.filter_model); self.filter_row.connect("notify::selected", lambda *_: self.refresh_library())
        g1 = Adw.PreferencesGroup(); g1.add(self.filter_row); pref.add(g1)
        self.lib_list = Gtk.ListBox(css_classes=["boxed-list"]); g2 = Adw.PreferencesGroup(title="Collection"); g2.add(self.lib_list); pref.add(g2); self.lib_stack.add_named(pref, "list")
        self.lib_empty = Adw.StatusPage(title="No Plants Found", icon_name="emoji-nature-symbolic", description="Add your first plant to get started.")
        self.lib_stack.add_named(self.lib_empty, "empty"); page.append(self.lib_stack); self.stack.add_named(page, "lib")

    def create_guides_ui(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); apply_margins(bar, 12)
        self.guide_search = Gtk.SearchEntry(placeholder_text="Search guides...", hexpand=True); self.guide_search.connect("search-changed", lambda *_: self.refresh_guides())
        add_btn = Gtk.Button(icon_name="list-add-symbolic", css_classes=["flat"]); add_btn.connect("clicked", lambda _: AddGuideDialog(self, self.refresh_guides).present())
        bar.append(self.guide_search); bar.append(add_btn); page.append(bar)
        pref = Adw.PreferencesPage(); self.guides_list = Gtk.ListBox(css_classes=["boxed-list"])
        group = Adw.PreferencesGroup(title="Care Guides"); group.add(self.guides_list); pref.add(group); page.append(pref); self.stack.add_named(page, "guides")

    def refresh_all(self):
        self.refresh_gardens(); self.refresh_library(); self.refresh_dashboard(); self.refresh_guides(); self.refresh_tasks()

    def refresh_tasks(self):
        while (c := self.tasks_list.get_first_child()): self.tasks_list.remove(c)
        conn = sqlite3.connect(get_db_path()); count = 0
        for tid, desc, due in conn.execute("SELECT id, description, due_date FROM tasks WHERE completed=0 ORDER BY id DESC"):
            count += 1; row = Adw.ActionRow(title=desc, subtitle=f"Added: {due}")
            done_btn = Gtk.Button(icon_name="object-select-symbolic", css_classes=["flat", "success"], valign=Gtk.Align.CENTER); done_btn.connect("clicked", lambda b, i=tid: self.complete_task(i))
            del_btn = Gtk.Button(icon_name="user-trash-symbolic", css_classes=["flat", "error"], valign=Gtk.Align.CENTER); del_btn.connect("clicked", lambda b, i=tid: self.delete_task(i))
            row.add_suffix(done_btn); row.add_suffix(del_btn); self.tasks_list.append(row)
        conn.close(); self.tasks_stack.set_visible_child_name("list" if count > 0 else "empty")

    def complete_task(self, tid):
        conn = sqlite3.connect(get_db_path()); conn.execute("UPDATE tasks SET completed=1 WHERE id=?", (tid,)); conn.commit(); conn.close(); self.refresh_tasks()

    def delete_task(self, tid):
        conn = sqlite3.connect(get_db_path()); conn.execute("DELETE FROM tasks WHERE id=?", (tid,)); conn.commit(); conn.close(); self.refresh_tasks()

    def refresh_dashboard(self):
        while (c := self.thirsty_list.get_first_child()): self.thirsty_list.remove(c)
        conn = sqlite3.connect(get_db_path()); query = "SELECT p.id, p.name, p.water_interval, (SELECT entry_date FROM journal_entries WHERE plant_id = p.id AND status = 'Watering' ORDER BY id DESC LIMIT 1) as last_water FROM plants p"
        thirsty_count = 0
        for pid, name, interval, last_water in conn.execute(query):
            needs_water = False
            if last_water:
                last_dt = datetime.strptime(last_water, "%Y-%m-%d"); diff = (datetime.now() - last_dt).days
                if diff >= interval: needs_water = True
            else: needs_water = True
            if needs_water:
                thirsty_count += 1; row = Adw.ActionRow(title=name, subtitle="Needs water!")
                w_btn = Gtk.Button(icon_name="weather-showers-symbolic", css_classes=["suggested-action", "pill"], valign=Gtk.Align.CENTER); w_btn.connect("clicked", lambda b, i=pid: self.quick_water(i)); row.add_suffix(w_btn); self.thirsty_list.append(row)
        self.thirsty_group.set_visible(thirsty_count > 0); conn.close()

    def refresh_library(self):
        while (c := self.lib_list.get_first_child()): self.lib_list.remove(c)
        s = self.lib_search.get_text().strip(); idx = self.filter_row.get_selected(); gid = self.filter_garden_ids[idx] if idx < len(self.filter_garden_ids) else None
        conn = sqlite3.connect(get_db_path()); query = "SELECT p.id, p.name, g.name, p.planting_date, p.water_interval FROM plants p LEFT JOIN gardens g ON p.garden_id = g.id"
        conditions = []
        if gid: conditions.append(f"p.garden_id = {gid}")
        if s: conditions.append(f"p.name LIKE '%{s}%'")
        if conditions: query += " WHERE " + " AND ".join(conditions)
        count = 0
        for pid, name, gname, bday, interval in conn.execute(query):
            count += 1; row = Adw.ActionRow(title=f"{name} ({gname or 'Unassigned'})", subtitle=f"Age: {calculate_age(bday)}", activatable=True)
            row.connect("activated", lambda r, i=pid, n=name: self.nav_view.push(PlantDetailView(i, n)))
            e_btn = Gtk.Button(icon_name="document-edit-symbolic", css_classes=["flat"], valign=Gtk.Align.CENTER); e_btn.connect("clicked", lambda b, i=pid: EditPlantDialog(self, i, self.refresh_all).present())
            d_btn = Gtk.Button(icon_name="user-trash-symbolic", css_classes=["flat", "error"], valign=Gtk.Align.CENTER); d_btn.connect("clicked", lambda b, i=pid: self.on_delete_plant(i))
            row.add_suffix(e_btn); row.add_suffix(d_btn); self.lib_list.append(row)
        conn.close(); self.lib_stack.set_visible_child_name("list" if count > 0 else "empty")

    def refresh_gardens(self):
        while (c := self.garden_list.get_first_child()): self.garden_list.remove(c)
        s = self.garden_search.get_text().strip(); self.filter_garden_ids = [None]; self.filter_model.splice(1, self.filter_model.get_n_items() - 1, [])
        conn = sqlite3.connect(get_db_path()); query = "SELECT g.id, g.name, COUNT(p.id) FROM gardens g LEFT JOIN plants p ON g.id = p.garden_id"
        if s: query += f" WHERE g.name LIKE '%{s}%'"
        query += " GROUP BY g.id"
        count = 0
        for gid, name, pcount in conn.execute(query):
            count += 1; row = Adw.ActionRow(title=name); badge = Gtk.Label(label=str(pcount), css_classes=["pill", "caption"]); row.add_suffix(badge)
            d_btn = Gtk.Button(icon_name="user-trash-symbolic", css_classes=["flat", "error"], valign=Gtk.Align.CENTER); d_btn.connect("clicked", lambda b, i=gid: self.on_delete_garden(i)); row.add_suffix(d_btn)
            self.garden_list.append(row); self.filter_garden_ids.append(gid); self.filter_model.append(name)
        conn.close(); self.garden_stack.set_visible_child_name("list" if count > 0 else "empty")

    def refresh_guides(self):
        while (c := self.guides_list.get_first_child()): self.guides_list.remove(c)
        s = self.guide_search.get_text().strip(); conn = sqlite3.connect(get_db_path()); query = "SELECT id, species, sunlight, interval FROM care_guides"
        if s: query += f" WHERE species LIKE '%{s}%'"
        for gid, spec, sun, iv in conn.execute(query + " ORDER BY species"):
            row = Adw.ActionRow(title=spec, subtitle=f"Sun: {sun} | Water: {iv}d"); row.add_prefix(Gtk.Image.new_from_icon_name("help-about-symbolic"))
            d_btn = Gtk.Button(icon_name="user-trash-symbolic", css_classes=["flat", "error"], valign=Gtk.Align.CENTER); d_btn.connect("clicked", lambda b, i=gid: self.on_delete_guide(i)); row.add_suffix(d_btn); self.guides_list.append(row)
        conn.close()

    def quick_water(self, pid):
        conn = sqlite3.connect(get_db_path()); conn.execute("INSERT INTO journal_entries (plant_id, entry_date, note, status) VALUES (?, date('now'), 'Watered', 'Watering')", (pid,)); conn.commit(); conn.close(); self.refresh_all()

    def on_delete_plant(self, pid):
        conn = sqlite3.connect(get_db_path()); conn.execute("DELETE FROM plants WHERE id=?", (pid,)); conn.commit(); conn.close(); self.refresh_all()

    def on_delete_garden(self, gid):
        conn = sqlite3.connect(get_db_path()); conn.execute("DELETE FROM gardens WHERE id=?", (gid,)); conn.commit(); conn.close(); self.refresh_all()

    def on_delete_guide(self, gid):
        conn = sqlite3.connect(get_db_path()); conn.execute("DELETE FROM care_guides WHERE id=?", (gid,)); conn.commit(); conn.close(); self.refresh_guides()

    def on_sidebar_row_activated(self, _, row): self.stack.set_visible_child_name(row.target_id)
    def on_theme_toggle_clicked(self, btn):
        sm = Adw.StyleManager.get_default(); sm.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT if sm.get_dark() else Adw.ColorScheme.FORCE_DARK)

if __name__ == "__main__":
    init_db()
    display = Gdk.Display.get_default()
    if display:
        icon_theme = Gtk.IconTheme.get_for_display(display)
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data/icons"))
        if os.path.exists(icon_path): icon_theme.add_search_path(icon_path)
    app = Adw.Application(application_id='com.github.cadmiumcmyk.Flora')
    app.connect('activate', lambda a: FloraWindow(application=a).present())
    app.run(sys.argv)
    
    #https://github.com/cadmium-cmyk/flora
