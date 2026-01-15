import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

class OrientationPage(Gtk.Box):
    def __init__(self, on_get_started_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Internal ToolbarView since we can't subclass it
        toolbar_view = Adw.ToolbarView()
        toolbar_view.set_vexpand(True)
        toolbar_view.set_hexpand(True)
        self.append(toolbar_view)
        
        # --- Top Bar ---
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(True)
        toolbar_view.add_top_bar(header)
        
        # --- Content ---
        # Single Status Page
        page = Adw.StatusPage()
        page.set_title("Welcome to Flora")
        page.set_description("Your personal plant explorer and garden companion.")
        page.set_icon_name("emoji-nature-symbolic")
        
        btn = Gtk.Button(label="Get Started")
        btn.add_css_class("pill")
        btn.add_css_class("suggested-action")
        btn.set_halign(Gtk.Align.CENTER)
        btn.set_margin_top(24)
        btn.connect("clicked", lambda b: on_get_started_callback())
        
        page.set_child(btn)
        
        toolbar_view.set_content(page)
