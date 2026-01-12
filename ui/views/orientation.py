import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

class OrientationPage(Gtk.Box):
    def __init__(self, on_get_started_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        
        # Single Status Page
        page = Adw.StatusPage()
        page.set_title("Welcome to Flora")
        page.set_description("Your personal plant explorer. Track your garden, search for plants, and set care reminders.")
        page.set_icon_name("com.github.cadmiumcmyk.Flora")
        page.set_vexpand(True)
        page.set_hexpand(True)
        
        btn = Gtk.Button(label="Get Started")
        btn.add_css_class("pill")
        btn.add_css_class("suggested-action")
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", lambda b: on_get_started_callback())
        
        page.set_child(btn)
        self.append(page)
