import subprocess
import sys
import os
import json
import threading
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib, Gdk

# Load GResource
resource_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "com.github.cadmiumcmyk.Flora.gresource")
if os.path.exists(resource_path):
    resource = Gio.Resource.load(resource_path)
    resource._register()
else:
    # Try alternate location (e.g., /app/share/flora/...)
    resource_path = "/app/share/flora/com.github.cadmiumcmyk.Flora.gresource"
    if os.path.exists(resource_path):
        resource = Gio.Resource.load(resource_path)
        resource._register()

from window import PlantWindow

# Default Configuration
# Placeholder for API key. Users should set this in the settings or via environment variable.
DEFAULT_TOKEN = "YOUR_TREFLE_API_TOKEN"

class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.github.cadmiumcmyk.Flora", flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.config_dir = os.path.join(GLib.get_user_config_dir(), "flora")
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        self.config_file = os.path.join(self.config_dir, "flora_config.json")
        self.config = self.load_config()

    def load_config(self):
        defaults = {
            "api_key": DEFAULT_TOKEN, 
            "theme": "default", 
            "city": "Winnipeg",
            "orientation_viewed": False,
            "api_provider": "trefle"
        }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return {**defaults, **json.load(f)}
            except:
                return defaults
        return defaults

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)

    def do_activate(self):
        # Add resource path to icon theme
        display = Gdk.Display.get_default()
        if display:
            icon_theme = Gtk.IconTheme.get_for_display(display)
            icon_theme.add_resource_path("/com/github/cadmiumcmyk/Flora/resources")

        # Apply theme before showing window
        self.apply_theme(self.config.get("theme", "default"))
        
        self.win = PlantWindow(application=self)
        self.create_actions()
        self.win.present()

    def create_actions(self):
        theme_action = Gio.SimpleAction.new_stateful("set_theme", GLib.VariantType.new("s"), GLib.Variant.new_string(self.config["theme"]))
        theme_action.connect("activate", self.on_theme_activated)
        self.add_action(theme_action)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about_activated)
        self.add_action(about_action)

        api_action = Gio.SimpleAction.new("set_api_key", None)
        api_action.connect("activate", self.on_api_activated)
        self.add_action(api_action)
        
        city_action = Gio.SimpleAction.new("set_city", None)
        city_action.connect("activate", self.on_city_activated)
        self.add_action(city_action)

    def apply_theme(self, theme):
        style_manager = Adw.StyleManager.get_default()
        if theme == "light":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        elif theme == "dark":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)

    def on_theme_activated(self, action, parameter):
        theme = parameter.get_string()
        self.apply_theme(theme)
        self.config["theme"] = theme
        self.save_config()
        action.set_state(parameter)

    def on_about_activated(self, action, parameter):
        about = Adw.AboutWindow(
            transient_for=self.win,
            application_name="Flora",
            application_icon="com.github.cadmiumcmyk.Flora",
            developer_name="Andrew Bair",
            version="v0.0.5-beta",
            copyright="© 2026 Andrew Blair",
            website="https://github.com/cadmium-cmyk/flora"
        )
        about.present()

    def on_api_activated(self, action, parameter):
        dialog = Adw.MessageDialog(transient_for=self.win, heading="API Configuration", body="Enter your Trefle API Token:")
        entry = Gtk.Entry(text=self.config["api_key"])
        dialog.set_extra_child(entry)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(d, response):
            if response == "save":
                new_key = entry.get_text()
                self.config["api_key"] = new_key
                self.save_config()
                self.win.show_toast("API Key Updated")
            d.close()

        dialog.connect("response", on_response)
        dialog.present()
        
    def on_city_activated(self, action, parameter):
        dialog = Adw.MessageDialog(
            transient_for=self.win, 
            heading="Weather Settings", 
            body="Enter city for local weather:"
        )
        
        entry = Gtk.Entry(text=self.config.get("city", "Winnipeg"))
        dialog.set_extra_child(entry)
        
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(d, response):
            if response == "save":
                new_city = entry.get_text().strip()
                if new_city:
                    self.config["city"] = new_city
                    self.save_config() 
                    self.win.show_toast(f"City updated to {new_city}")
                    threading.Thread(target=self.win.fetch_weather, daemon=True).start()
            d.close()

        dialog.connect("response", on_response)
        dialog.present()

if __name__ == "__main__":
    App().run(sys.argv)
