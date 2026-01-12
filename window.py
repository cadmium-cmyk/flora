import os
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk

from database import Database

# Import our new Modular Views
from ui.views import (
    DashboardView,
    SearchView,
    PlantDetailView,
    GardenView,
    JournalView,
    RemindersView
)
from ui.views.orientation import OrientationPage

# UI_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "window.ui")
# Using resource path
@Gtk.Template(resource_path="/com/github/cadmiumcmyk/Flora/window.ui")
class PlantWindow(Adw.ApplicationWindow):
    __gtype_name__ = "PlantWindow"

    # --- Template Children ---
    # These match the IDs in window.ui so we can pass them to the views
    toast_overlay = Gtk.Template.Child()
    main_stack = Gtk.Template.Child()
    view_stack = Gtk.Template.Child()
    
    # Navigation Sidebar
    split_view = Gtk.Template.Child()
    sidebar_list = Gtk.Template.Child()
    
    # Toggle buttons (Sidebar toggle)
    sidebar_btn_1 = Gtk.Template.Child()
    sidebar_btn_2 = Gtk.Template.Child()
    sidebar_btn_3 = Gtk.Template.Child()
    sidebar_btn_4 = Gtk.Template.Child()
    sidebar_btn_5 = Gtk.Template.Child()
    sidebar_btn_6 = Gtk.Template.Child()

    # We declare these here so the 'builder' (self) has references to them 
    # to pass to the View classes.
    
    # Search
    search_stack = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    result_list = Gtk.Template.Child()
    search_spinner = Gtk.Template.Child()
    
    # Favorites (Garden)
    garden_search_entry = Gtk.Template.Child()
    favorites_list = Gtk.Template.Child()
    favorites_group = Gtk.Template.Child()
    manual_name_entry = Gtk.Template.Child()
    manual_science_entry = Gtk.Template.Child()
    manual_image_row = Gtk.Template.Child()
    select_image_button = Gtk.Template.Child()
    add_manual_button = Gtk.Template.Child()

    # Details
    detail_image = Gtk.Template.Child()
    detail_name = Gtk.Template.Child()
    detail_genus = Gtk.Template.Child()
    detail_family = Gtk.Template.Child()
    detail_scientific = Gtk.Template.Child()
    detail_year = Gtk.Template.Child()
    detail_bib = Gtk.Template.Child()
    detail_edible = Gtk.Template.Child()
    detail_vegetable = Gtk.Template.Child()
    detail_habit = Gtk.Template.Child()
    detail_harvest = Gtk.Template.Child()
    detail_light = Gtk.Template.Child()
    detail_notes = Gtk.Template.Child()
    detail_date = Gtk.Template.Child()
    detail_counter = Gtk.Template.Child()
    detail_watered_row = Gtk.Template.Child()
    save_edits_button = Gtk.Template.Child()
    water_button = Gtk.Template.Child()
    fav_button = Gtk.Template.Child()
    delete_button = Gtk.Template.Child()
    back_button = Gtk.Template.Child()
    image_spinner = Gtk.Template.Child()
    change_photo_button = Gtk.Template.Child()

    # Reminders
    reminder_stack = Gtk.Template.Child()
    reminder_list = Gtk.Template.Child()
    reminder_entry = Gtk.Template.Child()
    reminder_date_entry = Gtk.Template.Child()
    add_reminder_button = Gtk.Template.Child()
    calendar_button = Gtk.Template.Child()
    
    # Journal
    journal_stack = Gtk.Template.Child()
    journal_list = Gtk.Template.Child()
    journal_new_btn = Gtk.Template.Child()
    
    # Dashboard
    dashboard_status = Gtk.Template.Child()
    dashboard_reminders_group = Gtk.Template.Child()
    dashboard_reminders_list = Gtk.Template.Child()
    dashboard_water_group = Gtk.Template.Child()
    dashboard_water_list = Gtk.Template.Child()
    weather_row = Gtk.Template.Child()
    weather_icon = Gtk.Template.Child()

    # Settings
    api_provider_row = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = Database()

        self.setup_css()
        
        # --- Initialize Views ---
        # We pass 'self' as the builder because the window acts as the container
        # for the templated widgets.
        
        self.dashboard_view = DashboardView(
            app_config=self.get_application().config, 
            db=self.db, 
            builder=self
        )
        
        self.search_view = SearchView(
            app_config=self.get_application().config,
            builder=self,
            on_plant_selected_callback=self.on_plant_selected
        )
        
        self.garden_view = GardenView(
            window=self,
            db=self.db,
            builder=self,
            on_plant_selected_callback=self.on_plant_selected
        )
        
        self.detail_view = PlantDetailView(
            window=self, 
            db=self.db, 
            builder=self
        )
        
        self.journal_view = JournalView(
            window=self, 
            db=self.db, 
            builder=self
        )
        
        self.reminders_view = RemindersView(
            window=self, 
            db=self.db, 
            builder=self
        )

        # --- Setup Orientation ---
        self.orientation_page = self.main_stack.get_child_by_name("orientation_page")
        # The child of the page is a placeholder Box, but we want to replace it or add to it
        # Actually in the ui file we put a GtkBox.
        # Let's just create the OrientationPage widget and set it as the child.
        
        self.orientation_view = OrientationPage(self.on_get_started)
        self.orientation_page.append(self.orientation_view)

        # --- Setup Settings ---
        self.setup_settings()

        # --- Setup Navigation ---
        self.connect_signals()
        
        # Check Orientation Logic
        if not self.get_application().config.get("orientation_viewed"):
            self.main_stack.set_visible_child_name("orientation_page")
        else:
            self.main_stack.set_visible_child_name("explorer_page")
        
        # Select first row initially (Dashboard)
        row = self.sidebar_list.get_row_at_index(0)
        self.sidebar_list.select_row(row)
        
        # Initial Tab Load
        self.on_tab_changed(self.view_stack, None)

    def on_get_started(self):
        self.get_application().config["orientation_viewed"] = True
        self.get_application().save_config()
        self.main_stack.set_visible_child_name("explorer_page")

    def setup_settings(self):
        # Set initial value for API provider combo row
        provider = self.get_application().config.get("api_provider", "trefle")
        if provider == "perenual":
            self.api_provider_row.set_selected(1)
        else:
            self.api_provider_row.set_selected(0)
            
        self.api_provider_row.connect("notify::selected", self.on_api_provider_changed)

    def on_api_provider_changed(self, row, pspec):
        index = row.get_selected()
        provider = "trefle" if index == 0 else "perenual"
        self.get_application().config["api_provider"] = provider
        self.get_application().save_config()

    def setup_css(self):
        css_provider = Gtk.CssProvider()
        # css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
        # if os.path.exists(css_path):
        #     css_provider.load_from_path(css_path)
        try:
            css_provider.load_from_resource("/com/github/cadmiumcmyk/Flora/style.css")
        except Exception as e:
            print(f"Failed to load CSS from resource: {e}")
            # Fallback for development if resource not compiled (optional, but good)
            css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
            if os.path.exists(css_path):
                css_provider.load_from_path(css_path)
            else:
                css_provider.load_from_data(b".rounded-image { border-radius: 24px; }")
        
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), 
            css_provider, 
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def connect_signals(self):
        # Global Window Navigation
        self.sidebar_list.connect("row-activated", self.on_sidebar_row_selected)
        self.view_stack.connect("notify::visible-child", self.on_tab_changed)
        
        # Sidebar Toggles
        for btn in [self.sidebar_btn_1, self.sidebar_btn_2, self.sidebar_btn_3, 
                   self.sidebar_btn_4, self.sidebar_btn_5, self.sidebar_btn_6]:
            btn.connect("clicked", self.on_sidebar_toggle_clicked)

    def on_plant_selected(self, plant_data):
        """
        Callback used by Search and Garden views to navigate to details.
        """
        self.detail_view.load_plant(plant_data)

    def on_sidebar_toggle_clicked(self, btn):
        is_visible = self.split_view.get_show_sidebar()
        self.split_view.set_show_sidebar(not is_visible)
    
    def on_sidebar_row_selected(self, box, row):
        if not row: return
        title = row.get_title()
        
        page_map = {
            "Dashboard": "home_view",
            "Search": "search_view",
            "My Garden": "fav_view",
            "Reminders": "reminders_view",
            "Journal": "journal_view",
            "Settings": "settings_view"
        }
        
        target_page = page_map.get(title)
        if target_page:
            self.view_stack.set_visible_child_name(target_page)
            
        # Auto-collapse sidebar on mobile/small screens if needed
        if self.split_view.get_collapsed():
            self.split_view.set_show_sidebar(False)

    def on_tab_changed(self, stack, pspec):
        """
        When the user switches tabs, tell the relevant view to refresh its data.
        """
        target = stack.get_visible_child_name()
        
        if target == "home_view":
            self.dashboard_view.refresh()
        elif target == "search_view":
            self.search_view.focus()
        elif target == "fav_view":
            self.garden_view.refresh()
        elif target == "reminders_view":
            self.reminders_view.refresh()
        elif target == "journal_view":
            self.journal_view.refresh()

    def show_toast(self, message):
        """Helper to show toasts from sub-views"""
        self.toast_overlay.add_toast(Adw.Toast.new(message))
