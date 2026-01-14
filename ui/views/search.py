import threading
import requests
import json
import os
from gi.repository import GLib, Gtk, Adw

DEFAULT_TOKEN = "YOUR_TREFLE_API_TOKEN"

class SearchView:
    def __init__(self, app_config, builder, on_plant_selected_callback):
        self.config = app_config
        self.on_plant_selected = on_plant_selected_callback
        
        self.stack = builder.search_stack
        self.entry = builder.search_entry
        self.result_list = builder.result_list
        self.spinner = builder.search_spinner
        
        self.search_timeout_id = None

        # Connect signals
        self.entry.connect("activate", self._on_search_triggered)
        self.entry.connect("search-changed", self._on_search_changed)
        self.result_list.connect("row-activated", self._on_row_clicked)

    def focus(self):
        """Called when tab becomes visible"""
        pass # Could set focus to entry here if desired

    def _on_search_changed(self, entry):
        text = entry.get_text()
        if not text:
            self.stack.set_visible_child_name("empty_search")
            self._clear_results()
            return
            
        if self.search_timeout_id:
            GLib.source_remove(self.search_timeout_id)
            
        self.search_timeout_id = GLib.timeout_add(400, self._trigger_live_search, text)

    def _trigger_live_search(self, query):
        self.search_timeout_id = None
        self._perform_search(query)
        return False

    def _on_search_triggered(self, entry):
        query = entry.get_text()
        if query:
            if self.search_timeout_id:
                GLib.source_remove(self.search_timeout_id)
                self.search_timeout_id = None
            self._perform_search(query)

    def _perform_search(self, query):
        self.stack.set_visible_child_name("loading")
        threading.Thread(target=self._fetch_plants, args=(query,), daemon=True).start()

    def _search_local_plants(self, query):
        try:
            # Locate plants.json relative to this file
            base_path = os.path.dirname(os.path.abspath(__file__))
            # search.py is in ui/views, so we need to go up two levels to reach root
            json_path = os.path.join(base_path, "../../plants.json")
            
            if not os.path.exists(json_path):
                # Fallback: check current directory (useful for testing)
                if os.path.exists("plants.json"):
                    json_path = "plants.json"
                
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    data = json.load(f).get('data', [])
                    
                query_lower = query.lower()
                results = [
                    p for p in data 
                    if query_lower in (p.get('common_name') or "").lower() 
                    or query_lower in (p.get('scientific_name') or "").lower()
                ]
                return results
            else:
                print(f"plants.json not found at {json_path}")
                return []
        except Exception as e:
            print(f"Local search error: {e}")
            return []

    def _fetch_plants(self, query):
        try:
            token = self.config.get("api_key")
            provider = self.config.get("api_provider", "trefle")
            
            # Check for valid API key
            if not token or token == DEFAULT_TOKEN:
                data = self._search_local_plants(query)
                GLib.idle_add(self._populate_results, data)
                return
            
            data = []
            
            if provider == "perenual":
                url = f"https://perenual.com/api/v2/species-list?key={token}&q={query}"
                res = requests.get(url, timeout=10)
                
                if res.status_code == 200:
                    json_data = res.json().get('data', [])
                    
                    # Normalize Perenual data to match Trefle structure partially
                    # Perenual returns 'scientific_name' as list, Trefle as string
                    # Perenual returns 'default_image' dict, Trefle 'image_url' string
                    for item in json_data:
                        # Perenual scientific_name is a list
                        sci_name = item.get('scientific_name', [])
                        if isinstance(sci_name, list):
                            sci_name = sci_name[0] if sci_name else "Unknown"
                            
                        # Handle image
                        img_url = None
                        default_img = item.get('default_image')
                        if default_img and isinstance(default_img, dict):
                            img_url = default_img.get('regular_url')
                            
                        data.append({
                            'id': item.get('id'), # Note: IDs might collide if mixing providers in DB
                            'common_name': item.get('common_name'),
                            'scientific_name': sci_name,
                            'image_url': img_url,
                            'family': item.get('family'), # Might be null in list view
                            'year': item.get('year'), # Not usually in list view
                            'bibliography': None,
                            # Extra fields that might be useful if we fetch details
                            'cycle': item.get('cycle'),
                            'watering': item.get('watering'),
                            'sunlight': item.get('sunlight')
                        })
                elif res.status_code == 401:
                     data = self._search_local_plants(query)
            else:
                # Default to Trefle
                url = f"https://trefle.io/api/v1/plants/search?token={token}&q={query}"
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    data = res.json().get('data', [])
                elif res.status_code == 401:
                     data = self._search_local_plants(query)
                else:
                     print(f"API Error {res.status_code}")
                
            GLib.idle_add(self._populate_results, data)
        except Exception as e:
            print(f"Search error: {e}")
            # Optional: GLib.idle_add to show an error toast/state

    def _populate_results(self, data):
        self._clear_results()
        if not data:
            self.stack.set_visible_child_name("empty_search")
            return
        
        self.stack.set_visible_child_name("results")
        for plant in data:
            common = plant.get('common_name')
            scientific = plant.get('scientific_name')
            
            row = Adw.ActionRow(title=common or scientific)
            row.set_subtitle(scientific if common else "")
            row.set_activatable(True)
            # Store raw data on the row object to retrieve later
            row.plant_info = plant 
            self.result_list.append(row)
        return False

    def _on_row_clicked(self, listbox, row):
        if hasattr(row, 'plant_info'):
            self.on_plant_selected(row.plant_info)

    def _clear_results(self):
        while child := self.result_list.get_first_child():
            self.result_list.remove(child)
