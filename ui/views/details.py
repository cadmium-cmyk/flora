import threading
import requests
import hashlib
import os
from datetime import datetime
from gi.repository import GLib, Gtk, Adw, Gdk, Gio

class PlantDetailView:
    def __init__(self, window, db, builder):
        self.window = window  # Reference to main window for toasts/navigation
        self.db = db
        self.current_plant = None
        
        # --- UI References ---
        self.main_stack = builder.main_stack
        self.image = builder.detail_image
        self.spinner = builder.image_spinner
        self.name_lbl = builder.detail_name
        self.family_lbl = builder.detail_family
        self.science_lbl = builder.detail_scientific
        self.year_lbl = builder.detail_year
        self.bib_lbl = builder.detail_bib
        self.genus_lbl = builder.detail_genus
        self.edible_lbl = builder.detail_edible
        self.vegetable_lbl = builder.detail_vegetable
        self.habit_entry = builder.detail_habit
        self.harvest_entry = builder.detail_harvest
        self.light_entry = builder.detail_light
        self.notes_view = builder.detail_notes
        self.date_added_row = builder.detail_date
        self.days_owned_row = builder.detail_counter
        self.watered_row = builder.detail_watered_row
        self.btn_save = builder.save_edits_button
        self.btn_water = builder.water_button
        self.btn_fav = builder.fav_button
        self.btn_delete = builder.delete_button
        self.btn_back = builder.back_button
        self.change_photo_btn = builder.change_photo_button
        
        self.new_image_path = None
        
        self._connect_signals()

    def _connect_signals(self):
        self.btn_back.connect("clicked", self._go_back)
        self.btn_fav.connect("clicked", self._on_favorite_clicked)
        self.btn_delete.connect("clicked", self._on_delete_clicked)
        self.btn_save.connect("clicked", self._on_save_edits_clicked)
        self.btn_water.connect("clicked", self._on_water_clicked)
        self.change_photo_btn.connect("clicked", self._on_change_photo_clicked)

    def load_plant(self, plant_data):
        """Populates the view with plant data and checks DB for existing records."""
        self.new_image_path = None
        self.current_plant = plant_data
        p = plant_data
        
        # 1. Populate Static Info
        self.name_lbl.set_text(p.get('common_name') or "")
        self.family_lbl.set_text(p.get('family_common_name') or p.get('family') or "")
        self.science_lbl.set_text(p.get('scientific_name') or "")
        self.year_lbl.set_text(str(p.get('year')) if p.get('year') else "")
        self.bib_lbl.set_text(p.get('bibliography') or "")
        
        # New fields defaults
        self.genus_lbl.set_text(p.get('genus') or "")
        self.edible_lbl.set_text("")
        self.vegetable_lbl.set_text("")

        # Fetch more details if available
        threading.Thread(target=self._fetch_full_details, args=(p,), daemon=True).start()

        # 2. Load Image (Threaded)
        # Reset avatar first
        self.image.set_custom_image(None)
        
        # Set text for initials
        name = p.get('common_name') or p.get('scientific_name') or "Unknown"
        self.image.set_text(name)
        
        if p.get('image_url'):
            threading.Thread(target=self._load_image, args=(p['image_url'],), daemon=True).start()

        # 3. Check Database State (Is this in My Garden?)
        # We access the cursor directly or we could add a method in database.py
        self.db.cursor.execute(
            "SELECT added_date, notes, last_watered, habit, harvest, light, common_name, scientific_name, family, genus, year, bibliography, edible, vegetable FROM favorites WHERE id=?", 
            (p['id'],)
        )
        record = self.db.cursor.fetchone()

        if record:
            self._populate_existing_plant(record)
        else:
            self._populate_new_plant(p)
            
        # 4. Show the page
        self.main_stack.set_visible_child_name("details_page")

    def _populate_existing_plant(self, record):
        added_str, notes, watered, habit, harvest, light, common, sci, family, genus, year, bib, edible, veg = record
        
        self.date_added_row.set_subtitle(f"Added on {added_str}")
        self._calculate_days_owned(added_str)
        
        self.notes_view.get_buffer().set_text(notes or "")
        self.watered_row.set_subtitle(f"Last watered: {watered or 'Never'}")
        self.habit_entry.set_text(habit or "")
        self.harvest_entry.set_text(harvest or "")
        self.light_entry.set_text(light or "")

        # Populate new editable fields
        self.name_lbl.set_text(common or "")
        self.science_lbl.set_text(sci or "")
        self.family_lbl.set_text(family or "")
        self.genus_lbl.set_text(genus or "")
        self.year_lbl.set_text(year or "")
        self.bib_lbl.set_text(bib or "")
        self.edible_lbl.set_text(edible or "")
        self.vegetable_lbl.set_text(veg or "")
        
        # UI State
        self.btn_fav.set_icon_name("starred-symbolic")
        self.btn_delete.set_visible(True)

    def _populate_new_plant(self, p):
        self.date_added_row.set_subtitle("Not in collection")
        self.days_owned_row.set_subtitle("—")
        self.notes_view.get_buffer().set_text("")
        self.watered_row.set_subtitle("Never logged")
        
        # Try to fill defaults from API data if available
        self.habit_entry.set_text(p.get('growth_habit') or "")
        self.harvest_entry.set_text(str(p.get('days_to_harvest')) if p.get('days_to_harvest') else "")
        self.light_entry.set_text(str(p.get('light')) if p.get('light') else "")
        
        # New fields (already set in load_plant, but ensuring "Unknown" isn't used)
        
        # UI State
        self.btn_fav.set_icon_name("bookmark-new-symbolic")
        self.btn_delete.set_visible(False)

    def _calculate_days_owned(self, added_str):
        try:
            added_date = datetime.strptime(added_str, "%Y-%m-%d").date()
            days = (datetime.now().date() - added_date).days
            self.days_owned_row.set_subtitle("Added today" if days <= 0 else f"{days} days")
        except:
            self.days_owned_row.set_subtitle("Unknown duration")

    def _fetch_full_details(self, p):
        try:
            token = self.window.get_application().config.get("api_key")
            provider = self.window.get_application().config.get("api_provider", "trefle")
            
            if not p.get('id'):
                return

            if provider == "trefle":
                url = f"https://trefle.io/api/v1/plants/{p['id']}?token={token}"
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    data = res.json().get('data', {})
                    GLib.idle_add(self._update_ui_with_details, data, "trefle")
            
            elif provider == "perenual":
                url = f"https://perenual.com/api/v2/species/details/{p['id']}?key={token}"
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    GLib.idle_add(self._update_ui_with_details, data, "perenual")
                    
        except Exception as e:
            print(f"Details fetch error: {e}")

    def _update_ui_with_details(self, data, provider):
        # Only update if the field is empty to avoid overwriting user edits on saved plants?
        # But this is called for new plants too.
        # Ideally, we check if the field is empty.
        
        if provider == "trefle":
            if data.get('genus') and not self.genus_lbl.get_text():
                self.genus_lbl.set_text(data['genus'])
            
            # Trefle: vegetable is bool, edible_part is list or null
            is_veg = data.get('vegetable')
            if is_veg is not None and not self.vegetable_lbl.get_text():
                self.vegetable_lbl.set_text("Yes" if is_veg else "No")
            
            edible = data.get('edible_part')
            if not self.edible_lbl.get_text():
                self.edible_lbl.set_text(", ".join(edible) if edible else ("No" if is_veg is False else ""))

            # Update others if missing
            if not self.habit_entry.get_text() or self.habit_entry.get_text() == "N/A":
                # Trefle spec structure is complex, often under main_species -> growth
                main_species = data.get('main_species', {})
                growth = main_species.get('growth', {})
                habit = main_species.get('specifications', {}).get('growth_habit')
                if habit:
                     self.habit_entry.set_text(habit)
                
                # Light
                light = growth.get('light')
                if light:
                     self.light_entry.set_text(str(light))
            
        elif provider == "perenual":
            # Perenual has different structure
            # cycle, watering, sunlight, maintenance, care_level
            
            # Genus not always direct, maybe in scientific name
            
            # Edible
            # Perenual usually doesn't have explicit edible flag in free tier details easily mapped?
            # But let's check keys.
            # Assuming 'cuisine' field or similar if available, or just skip if not known.
            if data.get('fruits') and not self.edible_lbl.get_text():
                self.edible_lbl.set_text("Fruits (maybe)") # Very rough guess
            
            # Sunlight
            sunlight = data.get('sunlight')
            if sunlight and (not self.light_entry.get_text() or self.light_entry.get_text() == "Unknown"):
                if isinstance(sunlight, list):
                    self.light_entry.set_text(", ".join(sunlight))
                else:
                    self.light_entry.set_text(str(sunlight))
            
            # Watering
            watering = data.get('watering')
            # Map watering to habit or notes? Or just ignore for now as we don't have a field.
            # We could append to light or habit?
            
            # Cycle
            cycle = data.get('cycle')
            if cycle and (not self.habit_entry.get_text() or self.habit_entry.get_text() == "N/A"):
                self.habit_entry.set_text(cycle)

    def _get_cache_path(self, url):
        """Generates a local cache path for a given URL."""
        cache_base = os.path.join(GLib.get_user_cache_dir(), "flora", "images")
        if not os.path.exists(cache_base):
            os.makedirs(cache_base, exist_ok=True)
        
        # Create a safe filename from the URL hash
        hash_name = hashlib.md5(url.encode('utf-8')).hexdigest()
        return os.path.join(cache_base, hash_name)

    def _load_image(self, url):
        GLib.idle_add(self.spinner.set_spinning, True)
        try:
            texture = None
            if url.startswith("file://"):
                path = url.replace("file://", "")
                f = Gio.File.new_for_path(path)
                texture = Gdk.Texture.new_from_file(f)
            else:
                cache_path = self._get_cache_path(url)
                
                # Check cache first
                if os.path.exists(cache_path):
                    f = Gio.File.new_for_path(cache_path)
                    try:
                        texture = Gdk.Texture.new_from_file(f)
                    except Exception as e:
                        print(f"Failed to load cached image: {e}")
                        # If cache load fails, try downloading again (proceeds to download block)
                
                if not texture:
                    # Download if not in cache or cache load failed
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        # Save to cache
                        with open(cache_path, 'wb') as f:
                            f.write(response.content)
                        
                        # Load from file
                        f = Gio.File.new_for_path(cache_path)
                        texture = Gdk.Texture.new_from_file(f)
                    else:
                        raise Exception("Download failed")
            
            if texture:
                GLib.idle_add(lambda: self._set_texture(texture))
            else:
                raise Exception("No texture loaded")
                
        except Exception as e:
            print(f"Image load error: {e}")
            GLib.idle_add(self.spinner.set_spinning, False)
            # Avatar will just show initials if loading fails

    def _set_texture(self, texture):
        self.image.set_custom_image(texture)
        self.spinner.set_spinning(False)

    # --- Actions ---

    def _on_favorite_clicked(self, btn):
        if not self.current_plant: return
        p = self.current_plant
        buf = self.notes_view.get_buffer()
        notes = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        
        success = self.db.add_favorite(
            p['id'], 
            self.name_lbl.get_text(),
            self.science_lbl.get_text(),
            self.family_lbl.get_text(),
            self.genus_lbl.get_text(),
            self.year_lbl.get_text(),
            self.bib_lbl.get_text(),
            self.edible_lbl.get_text(),
            self.vegetable_lbl.get_text(),
            p.get('image_url'), 
            self.habit_entry.get_text(), 
            self.harvest_entry.get_text(), 
            self.light_entry.get_text(), 
            notes
        )
        
        if success:
            self.btn_fav.set_icon_name("starred-symbolic")
            self.btn_delete.set_visible(True)
            self.window.show_toast("Added to Garden!")
        else:
            self.window.show_toast("Already in Garden")

    def _on_save_edits_clicked(self, btn):
        if not self.current_plant: return
        buf = self.notes_view.get_buffer()
        notes = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        
        new_url = self.new_image_path if self.new_image_path else None
        
        if self.db.update_favorite(
            self.current_plant['id'], 
            self.name_lbl.get_text(),
            self.science_lbl.get_text(),
            self.family_lbl.get_text(),
            self.genus_lbl.get_text(),
            self.year_lbl.get_text(),
            self.bib_lbl.get_text(),
            self.edible_lbl.get_text(),
            self.vegetable_lbl.get_text(),
            self.habit_entry.get_text(), 
            self.harvest_entry.get_text(), 
            self.light_entry.get_text(), 
            notes, 
            image_url=new_url
        ):
            if new_url:
                self.current_plant['image_url'] = new_url
            self.window.show_toast("Changes saved")

    def _on_change_photo_clicked(self, btn):
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
            self.new_image_path = "file://" + file.get_path()
            
            # Update the avatar immediately to show preview
            f = Gio.File.new_for_path(file.get_path())
            try:
                texture = Gdk.Texture.new_from_file(f)
                self.image.set_custom_image(texture)
            except Exception as e:
                print(f"Error loading preview: {e}")
                
        dialog.destroy()

    def _on_water_clicked(self, btn):
        if not self.current_plant: return
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        if self.db.water_plant(self.current_plant['id'], now):
            self.watered_row.set_subtitle(f"Last watered: {now}")
            self.window.show_toast("Watered!")

    def _on_delete_clicked(self, btn):
        if not self.current_plant: return
        p_name = self.current_plant.get('common_name') or "this plant"
        
        dialog = Adw.MessageDialog(
            transient_for=self.window,
            heading="Remove from Garden?",
            body=f"Are you sure you want to remove '{p_name}' from your collection?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("remove", "Remove")
        dialog.set_response_appearance("remove", Adw.ResponseAppearance.DESTRUCTIVE)
        
        dialog.connect("response", self._confirm_delete)
        dialog.present()

    def _confirm_delete(self, dialog, response):
        if response == "remove":
            if self.db.remove_favorite(self.current_plant['id']):
                self.window.show_toast(f"Removed {self.current_plant.get('common_name')}")
                self._go_back(None)
        dialog.close()

    def _go_back(self, btn):
        # Return to main stack
        self.main_stack.set_visible_child_name("explorer_page")
        # Optional: Trigger a refresh on the garden view if we just deleted something
        # Ideally, we'd emit a signal here that the main window listens to.
