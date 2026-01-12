import os
import threading
import requests
import hashlib
from datetime import datetime
from gi.repository import Gtk, Adw, Gio, Gdk, GLib, Pango

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
        self.name_entry = builder.manual_name_entry
        self.science_entry = builder.manual_science_entry
        self.image_row = builder.manual_image_row
        self.select_img_btn = builder.select_image_button
        self.add_btn = builder.add_manual_button

        # --- Connect Signals ---
        self.select_img_btn.connect("clicked", self._on_select_image_clicked)
        self.add_btn.connect("clicked", self._on_add_manual_clicked)
        # GtkFlowBox uses child-activated
        self.favorites_list.connect("child-activated", self._on_child_activated)
        
        self.search_entry.connect("search-changed", self._on_search_changed)
        self.favorites_list.set_filter_func(self._filter_func)

    def refresh(self):
        """Refreshes the list of plants in the garden."""
        self._clear_list()
        
        # Fetch minimal info needed for the list
        self.db.cursor.execute("SELECT id, common_name, scientific_name, image_url FROM favorites")
        rows = self.db.cursor.fetchall()
        
        # Hide the collection group if empty to look cleaner
        self.favorites_group.set_visible(len(rows) > 0)
        
        for r in rows:
            # Reconstruct the dictionary format expected by the DetailView
            p_dict = {
                'id': r[0], 
                'common_name': r[1], 
                'scientific_name': r[2], 
                'image_url': r[3]
            }
            self._add_card(p_dict)

    def _add_card(self, plant):
        # Create card widget for Grid View
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.set_halign(Gtk.Align.CENTER)
        
        # Avatar Image (Rounded)
        image = Adw.Avatar(size=100, show_initials=True)
        name = plant.get('common_name') or plant.get('scientific_name') or "Unknown"
        image.set_text(name)
        
        if plant.get('image_url'):
            threading.Thread(target=self._load_image, args=(plant['image_url'], image), daemon=True).start()
            
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

    def _on_add_manual_clicked(self, btn):
        name = self.name_entry.get_text()
        science = self.science_entry.get_text()
        
        if not name.strip():
            self.window.show_toast("Plant name is required")
            return

        # Handle local image path
        img_uri = None
        if self.selected_manual_image_path:
            img_uri = "file://" + self.selected_manual_image_path

        # Generate a simple ID (timestamp)
        manual_id = int(datetime.now().timestamp())
        
        # Add to DB
        #p_id, common, sci, family, genus, year, bib, edible, veg, img, habit, harvest, light, notes)
        success = self.db.add_favorite(
            manual_id, 
            name, 
            science, 
            family="", 
            genus="", 
            year="", 
            bib="", 
            edible="",   # <--- Added
            veg="",      # <--- Added
            img=img_uri, # It is safer to use a keyword argument here if possible
            habit="", 
            harvest="", 
            light="", 
            notes=""
        )

        if success:
            self._clear_form()
            self.window.show_toast(f"Added {name} to Garden!")
            self.refresh() # Immediate update
        else:
            self.window.show_toast("Error adding plant")

    def _on_select_image_clicked(self, btn):
        dialog = Gtk.FileChooserDialog(
            title="Select Plant Photo", 
            transient_for=self.window, 
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Open", Gtk.ResponseType.OK)
        
        filter_img = Gtk.FileFilter()
        filter_img.set_name("Images")
        filter_img.add_mime_type("image/png")
        filter_img.add_mime_type("image/jpeg")
        dialog.add_filter(filter_img)

        dialog.connect("response", self._on_file_dialog_response)
        dialog.present()

    def _on_file_dialog_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            file = dialog.get_file()
            self.selected_manual_image_path = file.get_path()
            self.image_row.set_subtitle(file.get_basename())
        dialog.destroy()

    def _clear_form(self):
        self.name_entry.set_text("")
        self.science_entry.set_text("")
        self.image_row.set_subtitle("No image selected")
        self.selected_manual_image_path = None

    def _clear_list(self):
        while child := self.favorites_list.get_child_at_index(0):
            self.favorites_list.remove(child)

    # --- Image Loading Helpers ---
    def _get_cache_path(self, url):
        """Generates a local cache path for a given URL."""
        cache_base = os.path.join(GLib.get_user_cache_dir(), "flora", "images")
        if not os.path.exists(cache_base):
            os.makedirs(cache_base, exist_ok=True)
        
        # Create a safe filename from the URL hash
        hash_name = hashlib.md5(url.encode('utf-8')).hexdigest()
        return os.path.join(cache_base, hash_name)

    def _load_image(self, url, target_avatar):
        try:
            texture = None
            if url.startswith("file://"):
                path = url.replace("file://", "")
                f = Gio.File.new_for_path(path)
                try:
                    texture = Gdk.Texture.new_from_file(f)
                except:
                    pass
            else:
                cache_path = self._get_cache_path(url)
                
                # Check cache first
                if os.path.exists(cache_path):
                    f = Gio.File.new_for_path(cache_path)
                    try:
                        texture = Gdk.Texture.new_from_file(f)
                    except:
                        pass
                
                if not texture:
                    # Download
                    try:
                        response = requests.get(url, timeout=10)
                        if response.status_code == 200:
                            with open(cache_path, 'wb') as f:
                                f.write(response.content)
                            f = Gio.File.new_for_path(cache_path)
                            texture = Gdk.Texture.new_from_file(f)
                    except:
                        pass
            
            if texture:
                GLib.idle_add(target_avatar.set_custom_image, texture)
                
        except Exception as e:
            print(f"Image load error: {e}")
