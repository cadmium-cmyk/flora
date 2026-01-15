import threading
import os
import hashlib
from gi.repository import Gtk, Adw, Gio, GLib, Pango, Gdk

class CollectionsView:
    def __init__(self, window, db, builder):
        self.window = window
        self.db = db
        self.builder = builder
        
        self.stack = builder.layouts_stack
        self.list_box = builder.layouts_list
        self.add_btn = builder.layouts_add_btn
        self.empty_add_btn = builder.layouts_empty_add_btn
        
        self.add_btn.connect("clicked", self._on_add_clicked)
        self.empty_add_btn.connect("clicked", self._on_add_clicked)
        self.list_box.connect("row-activated", self._on_row_activated)

    def refresh(self):
        # Clear list
        while child := self.list_box.get_row_at_index(0):
            self.list_box.remove(child)
            
        layouts = self.db.get_layouts()
        if not layouts:
            self.stack.set_visible_child_name("empty")
        else:
            self.stack.set_visible_child_name("list")
            for l_id, name, l_type, date in layouts:
                row = Adw.ExpanderRow(title=name, subtitle=f"{l_type} • Created {date}")
                row.layout_id = l_id
                row.layout_name = name
                row.layout_type = l_type
                
                # Add Edit Button Suffix
                edit_btn = Gtk.Button(icon_name="document-edit-symbolic")
                edit_btn.add_css_class("flat")
                edit_btn.set_tooltip_text("Edit Collection")
                edit_btn.connect("clicked", lambda b, _lid=l_id, _n=name, _t=l_type: self._on_edit_collection(b, _lid, _n, _t))
                row.add_action(edit_btn)

                # Add Delete Button Suffix
                delete_btn = Gtk.Button(icon_name="user-trash-symbolic")
                delete_btn.add_css_class("flat")
                delete_btn.add_css_class("destructive-action")
                delete_btn.set_tooltip_text("Delete Collection")
                # Using lambda with explicit arguments to capture values correctly in loop
                delete_btn.connect("clicked", lambda b, _lid=l_id: self._on_delete_collection(b, _lid))
                row.add_action(delete_btn)

                # Show assigned plants in expanded list
                items = self.db.get_layout_items(l_id)
                if items:
                    for item in items:
                        # item: id, plant_id, common_name, image_url
                        p_name = item[2]
                        plant_row = Adw.ActionRow(title=p_name)
                        
                        # Just an icon, no heavy image loading as requested
                        icon = Gtk.Image(icon_name="emoji-nature-symbolic")
                        plant_row.add_prefix(icon)
                        
                        row.add_row(plant_row)
                else:
                    empty_row = Adw.ActionRow(title="No plants assigned")
                    empty_row.set_sensitive(False)
                    row.add_row(empty_row)
                
                self.list_box.append(row)

    def _on_add_clicked(self, btn):
        dialog = Adw.AlertDialog(heading="New Garden")
        
        group = Adw.PreferencesGroup()
        
        name_entry = Adw.EntryRow(title="Name")
        type_entry = Adw.ComboRow(title="Type")
        
        types = ["Indoor Garden", "Raised Bed", "In-Ground Bed", "Container Garden"]
        model = Gtk.StringList.new(types)
        type_entry.set_model(model)
        type_entry.set_selected(0)
        
        group.add(name_entry)
        group.add(type_entry)
        
        dialog.set_extra_child(group)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("create", "Create")
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
        
        def callback(source, result):
            response = source.choose_finish(result)
            if response == "create":
                name = name_entry.get_text().strip()
                if not name:
                    self.window.show_toast("Name is required")
                    return
                
                selected_idx = type_entry.get_selected()
                l_type = types[selected_idx]
                
                l_id = self.db.create_layout(name, l_type)
                # Instead of opening editor, just refresh the list
                self.refresh()
                self.window.show_toast(f"Created garden '{name}'")
                
        dialog.choose(self.window, None, callback)

    def _on_edit_collection(self, btn, l_id, current_name, current_type):
        dialog = Adw.AlertDialog(heading="Edit Garden")
        
        group = Adw.PreferencesGroup()
        
        name_entry = Adw.EntryRow(title="Name")
        name_entry.set_text(current_name)
        
        type_entry = Adw.ComboRow(title="Type")
        
        types = ["Indoor Garden", "Raised Bed", "In-Ground Bed", "Container Garden"]
        model = Gtk.StringList.new(types)
        type_entry.set_model(model)
        
        # Set selection
        try:
            idx = types.index(current_type)
            type_entry.set_selected(idx)
        except ValueError:
            type_entry.set_selected(0)
        
        group.add(name_entry)
        group.add(type_entry)
        
        dialog.set_extra_child(group)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        
        def callback(source, result):
            response = source.choose_finish(result)
            if response == "save":
                name = name_entry.get_text().strip()
                if not name:
                    self.window.show_toast("Name is required")
                    return
                
                selected_idx = type_entry.get_selected()
                l_type = types[selected_idx]
                
                self.db.update_layout(l_id, name, l_type)
                self.refresh()
                self.window.show_toast("Collection updated")
                
        dialog.choose(self.window, None, callback)

    def _on_delete_collection(self, btn, l_id):
        dialog = Adw.AlertDialog(
            heading="Delete Collection?",
            body="Are you sure you want to delete this collection? This action cannot be undone."
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        
        def callback(source, result):
            response = source.choose_finish(result)
            if response == "delete":
                self.db.delete_layout(l_id)
                self.refresh()
                self.window.show_toast("Collection deleted")
                
        dialog.choose(self.window, None, callback)

    def _on_row_activated(self, box, row):
        pass


class CollectionEditorView:
    def __init__(self, window, db, builder):
        self.window = window
        self.db = db
        
        self.flowbox = builder.layout_flowbox
        self.title_widget = builder.layout_editor_title
        self.back_btn = builder.layout_editor_back_btn
        self.edit_btn = builder.layout_editor_edit_btn
        self.add_btn = builder.layout_editor_add_btn
        
        self.back_btn.connect("clicked", self._on_back_clicked)
        self.edit_btn.connect("clicked", self._on_edit_clicked)
        self.add_btn.connect("clicked", self._on_add_plant_clicked)
        
        self.current_layout_id = None
        self.current_layout_name = ""
        self.current_layout_type = ""
        
        self.plants_cache = []

    def load_layout(self, l_id, name, l_type):
        self.current_layout_id = l_id
        self.current_layout_name = name
        self.current_layout_type = l_type
        self.title_widget.set_title(name)
        
        # Load plants cache for selector
        self._refresh_plants_cache()
        
        self._load_items()

    def _refresh_plants_cache(self):
        # Fetch all favorites to populate the picker
        self.db.cursor.execute("SELECT id, common_name FROM favorites ORDER BY common_name")
        self.plants_cache = self.db.cursor.fetchall()

    def _load_items(self):
        # Clear existing
        while child := self.flowbox.get_child_at_index(0):
            self.flowbox.remove(child)

        items = self.db.get_layout_items(self.current_layout_id)
        # items: id, plant_id, common_name, image_url
        
        for item in items:
            p_id, name, img_url = item[1], item[2], item[3]
            self._add_plant_card(p_id, name, img_url)

    def _add_plant_card(self, plant_id, name, img_url=None):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.add_css_class("card")
        card.set_size_request(120, 140)
        card.set_margin_top(6)
        card.set_margin_bottom(6)
        card.set_margin_start(6)
        card.set_margin_end(6)
        
        # Image/Icon
        if img_url and img_url.startswith("file://"):
             # Placeholder for async image loading
             icon = Gtk.Image(icon_name="emoji-nature-symbolic", pixel_size=48)
        else:
             icon = Gtk.Image(icon_name="emoji-nature-symbolic", pixel_size=48)
        
        icon.set_margin_top(12)
        card.append(icon)
        
        # Name
        lbl = Gtk.Label(label=name)
        lbl.set_wrap(True)
        lbl.set_justify(Gtk.Justification.CENTER)
        lbl.set_max_width_chars(12)
        lbl.set_ellipsize(Pango.EllipsizeMode.END)
        lbl.add_css_class("heading")
        card.append(lbl)
        
        # Remove Button
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.set_margin_bottom(12)
        
        remove_btn = Gtk.Button(icon_name="user-trash-symbolic")
        remove_btn.add_css_class("flat")
        remove_btn.add_css_class("destructive-action")
        remove_btn.connect("clicked", lambda b: self._on_remove_plant_clicked(plant_id, card))
        
        btn_box.append(remove_btn)
        card.append(btn_box)
        
        self.flowbox.append(card)

    def _on_add_plant_clicked(self, btn):
        if not self.plants_cache:
            self.window.show_toast("No plants in garden to add")
            return

        # Show Popover to pick plant
        popover = Gtk.Popover()
        popover.set_parent(btn)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)
        
        # Plant List
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(200)
        scrolled.set_min_content_width(200)
        scrolled.set_max_content_height(300)
        
        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        
        for p_id, p_name in self.plants_cache:
            row = Gtk.ListBoxRow()
            lbl = Gtk.Label(label=p_name, xalign=0)
            row.set_child(lbl)
            row.plant_id = p_id
            row.plant_name = p_name
            listbox.append(row)
            
        listbox.connect("row-activated", lambda b, r: self._on_plant_picked(r, btn, popover))
        
        scrolled.set_child(listbox)
        box.append(scrolled)
        
        popover.set_child(box)
        popover.present()

    def _on_plant_picked(self, row, btn, popover):
        popover.popdown()
        if row.plant_id:
            self.db.add_layout_item(self.current_layout_id, row.plant_id)
            # Refetch details to get image if needed, or just pass None for now
            # To do it properly we could fetch from DB, but let's just pass name
            self._add_plant_card(row.plant_id, row.plant_name)

    def _on_remove_plant_clicked(self, plant_id, card_widget):
        self.db.remove_layout_item(self.current_layout_id, plant_id)
        # Remove from flowbox. The card_widget is the child of a GtkFlowBoxChild
        parent = card_widget.get_parent()
        if parent:
            self.flowbox.remove(parent)

    def _on_back_clicked(self, btn):
        self.window.close_layout_editor(refresh=True)

    def _on_edit_clicked(self, btn):
        dialog = Adw.AlertDialog(heading="Edit Collection")
        
        group = Adw.PreferencesGroup()
        
        name_entry = Adw.EntryRow(title="Name")
        name_entry.set_text(self.current_layout_name)
        
        type_entry = Adw.ComboRow(title="Type")
        
        types = ["Indoor Garden", "Raised Bed", "In-Ground Bed", "Container Garden"]
        model = Gtk.StringList.new(types)
        type_entry.set_model(model)
        
        # Set selection
        try:
            idx = types.index(self.current_layout_type)
            type_entry.set_selected(idx)
        except ValueError:
            type_entry.set_selected(0)
        
        group.add(name_entry)
        group.add(type_entry)
        
        dialog.set_extra_child(group)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        
        def callback(source, result):
            response = source.choose_finish(result)
            if response == "save":
                name = name_entry.get_text().strip()
                if not name:
                    self.window.show_toast("Name is required")
                    return
                
                selected_idx = type_entry.get_selected()
                l_type = types[selected_idx]
                
                self.db.update_layout(self.current_layout_id, name, l_type)
                
                # Update View
                self.current_layout_name = name
                self.current_layout_type = l_type
                self.title_widget.set_title(name)
                # self.window.show_toast("Collection updated")
                
        dialog.choose(self.window, None, callback)
