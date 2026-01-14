import os
import threading
import requests
import hashlib
from datetime import datetime
from gi.repository import Gtk, Adw, Gio, Gdk, GLib, Pango, GdkPixbuf

class GardenView:
    def __init__(self, window, db, builder, on_plant_selected_callback):
        self.window = window # Needed for FileChooser dialog parent
        self.db = db
        self.on_plant_selected = on_plant_selected_callback
        self.selected_manual_image_path = None

        # --- UI References ---
        self.favorites_list = builder.favorites_list
        self.search_entry = builder.garden_search_entry
        self.favorites_group = builder.favorites_group
        self.add_btn = builder.garden_add_btn
        self.stack = builder.garden_stack
        self.empty_add_btn = builder.garden_empty_add_btn

        # --- Connect Signals ---
        self.add_btn.connect("clicked", self._show_add_plant_dialog)
        self.empty_add_btn.connect("clicked", self._show_add_plant_dialog)
        # GtkFlowBox uses child-activated
        self.favorites_list.connect("child-activated", self._on_child_activated)
        
        self.search_entry.connect("search-changed", self._on_search_changed)
        self.favorites_list.set_filter_func(self._filter_func)

    def refresh(self):
        """Refreshes the list of plants in the garden."""
        self._clear_list()
        
        # Fetch info needed for the list and details
        # We fetch all columns to ensure detail view gets full info
        cols = ["id", "common_name", "scientific_name", "family", "genus", "year", "bibliography", "edible", "vegetable", "image_url", "habit", "harvest", "light", "notes", "added_date", "last_watered"]
        query = "SELECT " + ", ".join(cols) + " FROM favorites"
        
        self.db.cursor.execute(query)
        rows = self.db.cursor.fetchall()
        
        if not rows:
            self.stack.set_visible_child_name("empty")
        else:
            self.stack.set_visible_child_name("list")
        
        for r in rows:
            # Reconstruct the dictionary format
            p_dict = {}
            for i, col in enumerate(cols):
                p_dict[col] = r[i]
            
            self._add_card(p_dict)

    def _add_card(self, plant):
        # Create card widget for Grid View
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.set_halign(Gtk.Align.CENTER)
        card.set_size_request(180, 180)
        # card.set_hexpand(True)
        # card.set_vexpand(True)
        
        
        
        
        # Image (Rounded with Shadow)
        image = Gtk.Picture(width_request=160, height_request=160)
        image.set_content_fit(Gtk.ContentFit.COVER)
        # image.set_valign(Gtk.Align.CENTER)
        # image.set_halign(Gtk.Align.FILL)
        # image.set_hexpand(False)
        # image.set_vexpand(False)
        image.add_css_class("plant-card-image")
        
        name = plant.get('common_name') or plant.get('scientific_name') or "Unknown"
        
        if plant.get('image_url'):
            threading.Thread(target=self._load_image, args=(plant['image_url'], image), daemon=True).start()
        else:
            self._load_default_image(image)
            
        # Label
        label = Gtk.Label(label=name)
        label.set_wrap(True)
        label.set_justify(Gtk.Justification.CENTER)
        label.set_lines(2)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_max_width_chars(15)
        
        card.append(image)
        card.append(label)
        
        # Store data on the card widget
        card.plant_info = plant 
        self.favorites_list.append(card)

    def _on_child_activated(self, flowbox, child):
        # child is GtkFlowBoxChild
        widget = child.get_child()
        if hasattr(widget, 'plant_info'):
            self.on_plant_selected(widget.plant_info)

    def _on_search_changed(self, entry):
        self.favorites_list.invalidate_filter()

    def _filter_func(self, child):
        query = self.search_entry.get_text().lower()
        if not query:
            return True
            
        # The child of the flowbox is a GtkFlowBoxChild
        # We need to get our custom widget inside it
        widget = child.get_child()
        if not hasattr(widget, 'plant_info'):
            return False
            
        plant = widget.plant_info
        name = (plant.get('common_name') or "").lower()
        sci = (plant.get('scientific_name') or "").lower()
        
        return query in name or query in sci

    def _show_add_plant_dialog(self, btn):
        dialog = Adw.AlertDialog(
            heading="Add New Plant"
        )
        
        group = Adw.PreferencesGroup()
        
        # Inputs
        self.dialog_name_entry = Adw.EntryRow(title="Common Name")
        self.dialog_science_entry = Adw.EntryRow(title="Scientific Name")
        
        self.dialog_image_row = Adw.ActionRow(title="Plant Photo", subtitle="Select an image")
        img_btn = Gtk.Button(icon_name="list-add-symbolic", valign=Gtk.Align.CENTER)
        img_btn.add_css_class("flat")
        img_btn.connect("clicked", self._on_dialog_select_image_clicked)
        self.dialog_image_row.add_suffix(img_btn)
        
        group.add(self.dialog_name_entry)
        group.add(self.dialog_science_entry)
        group.add(self.dialog_image_row)
        
        dialog.set_extra_child(group)
        
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("add", "Add")
        dialog.set_response_appearance("add", Adw.ResponseAppearance.SUGGESTED)
        
        # Clear previous selection
        self.selected_manual_image_path = None
        
        def callback(source, result):
            response = source.choose_finish(result)
            if response == "add":
                name = self.dialog_name_entry.get_text()
                science = self.dialog_science_entry.get_text()
                
                if not name.strip():
                    self.window.show_toast("Plant name is required")
                else:
                    self._add_plant_to_db(name, science)
        
        dialog.choose(self.window, None, callback)

    def _add_plant_to_db(self, name, science):
        # Handle local image path
        img_uri = None
        if self.selected_manual_image_path:
            img_uri = "file://" + self.selected_manual_image_path

        # Generate a simple ID (timestamp)
        manual_id = int(datetime.now().timestamp())
        
        # Add to DB
        success = self.db.add_favorite(
            manual_id, 
            name, 
            science, 
            family="", 
            genus="", 
            year="", 
            bib="", 
            edible="", 
            veg="", 
            img=img_uri,
            habit="", 
            harvest="", 
            light="", 
            notes=""
        )

        if success:
            self.window.show_toast(f"Added {name} to Garden!")
            self.refresh()
        else:
            self.window.show_toast("Error adding plant")

    def _on_dialog_select_image_clicked(self, btn):
        dialog = Gtk.FileChooserNative(
            title="Select Plant Photo", 
            transient_for=self.window, 
            action=Gtk.FileChooserAction.OPEN,
            accept_label="_Open",
            cancel_label="_Cancel"
        )
        
        filter_img = Gtk.FileFilter()
        filter_img.set_name("Images")
        filter_img.add_mime_type("image/png")
        filter_img.add_mime_type("image/jpeg")
        dialog.add_filter(filter_img)

        dialog.connect("response", self._on_dialog_file_response)
        dialog.show()

    def _on_dialog_file_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            self.selected_manual_image_path = file.get_path()
            self.dialog_image_row.set_subtitle(file.get_basename())
        dialog.destroy()

    def _clear_list(self):
        while child := self.favorites_list.get_child_at_index(0):
            self.favorites_list.remove(child)

    # --- Image Loading Helpers ---
    def _load_default_image(self, target_picture):
        # Load flowers.svg from resources
        try:
            texture = Gdk.Texture.new_from_resource("/com/github/cadmiumcmyk/Flora/resources/flora-flowers.svg")
            target_picture.set_paintable(texture)
        except Exception as e:
            print(f"Failed to load default image: {e}")

    def _get_cache_path(self, url):
        """Generates a local cache path for a given URL."""
        cache_base = os.path.join(GLib.get_user_cache_dir(), "flora", "images")
        if not os.path.exists(cache_base):
            os.makedirs(cache_base, exist_ok=True)
        
        # Create a safe filename from the URL hash
        hash_name = hashlib.md5(url.encode('utf-8')).hexdigest()
        return os.path.join(cache_base, hash_name)

    def _load_image(self, url, target_picture):
        try:
            texture = None
            if url.startswith("file://"):
                path = url.replace("file://", "")
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 160, 160, True)
                    texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                except:
                    pass
            else:
                cache_path = self._get_cache_path(url)
                
                # Check cache first
                if os.path.exists(cache_path):
                    try:
                        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(cache_path, 160, 160, True)
                        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                    except:
                        pass
                
                if not texture:
                    # Download
                    try:
                        headers = {'User-Agent': 'Flora/0.1 (https://github.com/cadmiumcmyk/Flora; your@email.com)'}
                        response = requests.get(url, headers=headers, timeout=10)
                        if response.status_code == 200:
                            with open(cache_path, 'wb') as f:
                                f.write(response.content)
                            
                            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(cache_path, 160, 160, True)
                            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                    except:
                        pass
            
            if texture:
                GLib.idle_add(target_picture.set_paintable, texture)
            else:
                 GLib.idle_add(self._load_default_image, target_picture)
                
        except Exception as e:
            print(f"Image load error: {e}")
            GLib.idle_add(self._load_default_image, target_picture)
