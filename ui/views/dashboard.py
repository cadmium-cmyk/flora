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

    def refresh(self):
        self._update_garden_status()
        self._refresh_reminders()
        self._refresh_water_tasks()
        threading.Thread(target=self._fetch_weather, daemon=True).start()

    def _update_garden_status(self):
        # We need a new method in database.py for this, or execute directly
        # Ideally: count = self.db.get_plant_count()
        self.db.cursor.execute("SELECT COUNT(*) FROM favorites")
        count = self.db.cursor.fetchone()[0]

        if count == 0:
            self.status_row.set_title("Your Garden is Empty")
            self.status_row.set_subtitle("Head over to Search to find your first plant!")
            self.reminders_group.set_visible(False)
            self.water_group.set_visible(False)
        else:
            self.status_row.set_title("Garden Growing!")
            self.status_row.set_subtitle(f"You are currently caring for {count} plants.")
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
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            response = requests.get(weather_url, timeout=5).json()
            
            if "current_weather" in response:
                current = response["current_weather"]
                temp = current["temperature"]
                code = current["weathercode"]
                icon = "weather-clear-symbolic"
                if code > 3: icon = "weather-overcast-symbolic"
                
                GLib.idle_add(self._update_weather_ui, temp, icon)
        except Exception as e:
            print(f"Weather error: {e}")

    def _update_weather_ui(self, temp, icon_name):
        self.weather_row.set_subtitle(f"Currently {temp}°C")
        self.weather_icon.set_from_icon_name(icon_name)
        return False

    def _refresh_reminders(self):
        self._clear_list(self.reminders_list)
        reminders = self.db.get_reminders()[:3]
        if not reminders:
            self.reminders_list.append(Adw.ActionRow(title="No upcoming tasks"))
        else:
            for _, task, date in reminders:
                row = Adw.ActionRow(title=task)
                row.set_subtitle(f"Due: {date}")
                row.add_prefix(Gtk.Image(icon_name="task-due-symbolic"))
                self.reminders_list.append(row)

    def _refresh_water_tasks(self):
        self._clear_list(self.water_list)
        # Ideally, move this query to database.py
        self.db.cursor.execute("SELECT common_name, last_watered FROM favorites ORDER BY last_watered ASC LIMIT 3")
        plants = self.db.cursor.fetchall()
        for name, last in plants:
            row = Adw.ActionRow(title=name)
            row.set_subtitle(f"Last watered: {last or 'Never'}")
            row.add_prefix(Gtk.Image(icon_name="weather-showers-scattered-symbolic"))
            self.water_list.append(row)

    def _clear_list(self, listbox):
        while child := listbox.get_first_child():
            listbox.remove(child)
