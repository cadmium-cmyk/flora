# ui/views/dashboard.py
import threading
import requests
from gi.repository import GLib, Gtk, Adw

class DashboardView:
    def __init__(self, app_config, db, builder):
        self.config = app_config
        self.db = db
        
        # FIX: Access attributes directly instead of using get_object()
        self.weather_row = builder.weather_row
        self.weather_icon = builder.weather_icon
        self.status_row = builder.dashboard_status
        self.reminders_group = builder.dashboard_reminders_group
        self.reminders_list = builder.dashboard_reminders_list
        self.water_group = builder.dashboard_water_group
        self.water_list = builder.dashboard_water_list
        self.window = builder # The builder passed is the PlantWindow instance

    def refresh(self):
        self._update_garden_status()
        self._refresh_reminders()
        self._refresh_water_tasks()
        threading.Thread(target=self._fetch_weather, daemon=True).start()

    def _update_garden_status(self):
        # We need a new method in database.py for this, or execute directly
        # Ideally: count = self.db.get_plant_count()
        self.db.cursor.execute("SELECT COUNT(*) FROM favorites")
        plant_count = self.db.cursor.fetchone()[0]
        
        coll_count = self.db.get_collections_count()

        if plant_count == 0 and coll_count == 0:
            self.status_row.set_title("Your Garden is Empty")
            self.status_row.set_subtitle("Head over to Search to find your first plant!")
            self.reminders_group.set_visible(False)
            self.water_group.set_visible(False)
        else:
            self.status_row.set_title("Garden Growing!")
            self.status_row.set_subtitle(f"You have {plant_count} plants across {coll_count} collections.")
            self.reminders_group.set_visible(True)
            self.water_group.set_visible(True)

    def _fetch_weather(self):
        try:
            city = self.config.get("city", "Winnipeg")
            # Step 1: Geocoding
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
            geo_resp = requests.get(geo_url, timeout=5).json()
            
            if not geo_resp.get("results"):
                GLib.idle_add(self.weather_row.set_subtitle, f"City '{city}' not found")
                return

            location = geo_resp["results"][0]
            lat, lon = location["latitude"], location["longitude"]
            
            # Step 2: Weather
            # Request daily precipitation probability max to get chance of rain
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=precipitation_probability_max&timezone=auto"
            response = requests.get(weather_url, timeout=5).json()
            
            if "current_weather" in response:
                current = response["current_weather"]
                temp = current["temperature"]
                code = current["weathercode"]
                
                # Chance of rain
                precip_prob = 0
                if "daily" in response and "precipitation_probability_max" in response["daily"]:
                    probs = response["daily"]["precipitation_probability_max"]
                    if probs:
                        precip_prob = probs[0] # Today's max probability

                icon = "weather-clear-symbolic"
                if code > 3: icon = "weather-overcast-symbolic"
                if code >= 51: icon = "weather-showers-symbolic" # Rain codes start around 51
                
                GLib.idle_add(self._update_weather_ui, temp, icon, precip_prob)
        except Exception as e:
            print(f"Weather error: {e}")

    def _update_weather_ui(self, temp, icon_name, precip_prob):
        self.weather_row.set_subtitle(f"Currently {temp}°C • {precip_prob}% Chance of Rain")
        self.weather_icon.set_from_icon_name(icon_name)
        return False

    def _refresh_reminders(self):
        self._clear_list(self.reminders_list)
        reminders = self.db.get_reminders()[:3]
        if not reminders:
            self.reminders_list.append(Adw.ActionRow(title="No upcoming tasks"))
        else:
            for r_id, task, date in reminders:
                row = Adw.ActionRow(title=task)
                row.set_subtitle(f"Due: {date}")
                row.add_prefix(Gtk.Image(icon_name="task-due-symbolic"))
                
                # Add check button
                btn = Gtk.Button(icon_name="feather-check-symbolic", valign=Gtk.Align.CENTER)
                btn.add_css_class("flat")
                btn.set_tooltip_text("Mark as Completed")
                btn.connect("clicked", self._on_complete_reminder, r_id)
                row.add_suffix(btn)
                
                self.reminders_list.append(row)

    def _on_complete_reminder(self, button, r_id):
        self.db.complete_reminder(r_id)
        self._refresh_reminders()
        self.window.show_toast("Task completed")

    def _refresh_water_tasks(self):
        self._clear_list(self.water_list)
        # Ideally, move this query to database.py
        self.db.cursor.execute("SELECT id, common_name, last_watered FROM favorites ORDER BY last_watered ASC LIMIT 3")
        plants = self.db.cursor.fetchall()
        for p_id, name, last in plants:
            row = Adw.ActionRow(title=name)
            row.set_subtitle(f"Last watered: {last or 'Never'}")
            row.add_prefix(Gtk.Image(icon_name="leaf-symbolic"))
            
            # Add water button
            btn = Gtk.Button(icon_name="rain-symbolic", valign=Gtk.Align.CENTER)
            btn.add_css_class("flat")
            btn.set_tooltip_text("Water Plant")
            btn.connect("clicked", self._on_water_plant, p_id)
            row.add_suffix(btn)
            
            self.water_list.append(row)

    def _on_water_plant(self, button, p_id):
        import datetime
        now = datetime.date.today().strftime("%Y-%m-%d")
        self.db.water_plant(p_id, now)
        self._refresh_water_tasks()
        self.window.show_toast("Plant watered")

    def _clear_list(self, listbox):
        while child := listbox.get_first_child():
            listbox.remove(child)
