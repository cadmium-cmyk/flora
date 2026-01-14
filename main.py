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
        
        # Apply CSS classes after window creation
        self.update_css_classes()
        
        # Listen for system theme changes
        Adw.StyleManager.get_default().connect("notify::dark", self.on_system_theme_changed)

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

    def update_css_classes(self):
        if not hasattr(self, 'win') or not self.win:
            return
            
        theme = self.config.get("theme", "default")
        style_manager = Adw.StyleManager.get_default()
        is_dark = style_manager.get_dark()
        
        effective_dark = False
        if theme == "dark":
            effective_dark = True
        elif theme == "light":
            effective_dark = False
        else:
            effective_dark = is_dark
            
        if effective_dark:
            self.win.add_css_class("dark-mode")
            self.win.remove_css_class("light-mode")
        else:
            self.win.add_css_class("light-mode")
            self.win.remove_css_class("dark-mode")

    def on_system_theme_changed(self, manager, pspec):
        if self.config.get("theme", "default") == "default":
            self.update_css_classes()

    def on_theme_activated(self, action, parameter):
        theme = parameter.get_string()
        self.config["theme"] = theme
        self.save_config()
        self.apply_theme(theme)
        self.update_css_classes()
        action.set_state(parameter)

    def on_about_activated(self, action, parameter):
        about = Adw.AboutWindow(
            transient_for=self.win,
            application_name="Flora",
            application_icon="com.github.cadmiumcmyk.Flora",
            developer_name="Andrew Bair",
            version="v0.0.5-beta",
            license_type="GTK_LICENSE_GPL_3_0",
            copyright="© 2026 Andrew Blair",
            website="https://github.com/cadmium-cmyk/flora"
        )
        if Adw.StyleManager.get_default().get_dark():
            about.add_css_class("dark-mode")
        about.present()

    def on_api_activated(self, action, parameter):
        dialog = Adw.AlertDialog(heading="API Configuration", body="Enter your Trefle API Token:")
        entry = Gtk.Entry(text=self.config["api_key"])
        dialog.set_extra_child(entry)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        
        def callback(source, result):
            response = source.choose_finish(result)
            if response == "save":
                new_key = entry.get_text()
                self.config["api_key"] = new_key
                self.save_config()
                self.win.show_toast("API Key Updated")

        dialog.choose(self.win, None, callback)
        
    def on_city_activated(self, action, parameter):
        dialog = Adw.AlertDialog(
            heading="Weather Settings", 
            body="Enter city for local weather:"
        )
        
        entry = Gtk.Entry(text=self.config.get("city", "Winnipeg"))
        dialog.set_extra_child(entry)
        
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        
        if Adw.StyleManager.get_default().get_dark():
            dialog.add_css_class("dark-mode")
        else:
            dialog.add_css_class("light-mode")
        
        def callback(source, result):
            response = source.choose_finish(result)
            if response == "save":
                new_city = entry.get_text().strip()
                if new_city:
                    self.config["city"] = new_city
                    self.save_config() 
                    self.win.show_toast(f"City updated to {new_city}")
                    # Note: fetch_weather is not defined on PlantWindow in the provided window.py
                    # but leaving it as in original
                    try:
                        threading.Thread(target=self.win.dashboard_view.refresh, daemon=True).start()
                    except:
                        pass

        dialog.choose(self.win, None, callback)

if __name__ == "__main__":
    App().run(sys.argv)
