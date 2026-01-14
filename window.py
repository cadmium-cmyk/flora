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
    RemindersView,
    CollectionsView
)
from ui.views.collections import CollectionEditorView
from ui.views.journal_editor import JournalEditorView
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
    sidebar_close_btn = Gtk.Template.Child()
    
    # Toggle buttons (Sidebar toggle)
    sidebar_btn_1 = Gtk.Template.Child()
    sidebar_btn_2 = Gtk.Template.Child()
    sidebar_btn_3 = Gtk.Template.Child()
    sidebar_btn_4 = Gtk.Template.Child()
    sidebar_btn_5 = Gtk.Template.Child()
    sidebar_btn_6 = Gtk.Template.Child()
    sidebar_btn_7 = Gtk.Template.Child()

    # We declare these here so the 'builder' (self) has references to them 
    # to pass to the View classes.
    
    # Search
    search_stack = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    result_list = Gtk.Template.Child()
    search_spinner = Gtk.Template.Child()
    
    # Favorites (Garden)
    garden_search_entry = Gtk.Template.Child()
    garden_stack = Gtk.Template.Child()
    favorites_list = Gtk.Template.Child()
    favorites_group = Gtk.Template.Child()
    garden_add_btn = Gtk.Template.Child()
    garden_empty_add_btn = Gtk.Template.Child()

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
    detail_save_btn = Gtk.Template.Child()
    detail_assign_dropdown = Gtk.Template.Child()
    water_button = Gtk.Template.Child()
    fav_button = Gtk.Template.Child()
    delete_button = Gtk.Template.Child()
    back_button = Gtk.Template.Child()
    image_spinner = Gtk.Template.Child()

    # Reminders
    reminder_stack = Gtk.Template.Child()
    reminder_list = Gtk.Template.Child()
    daily_reminder_stack = Gtk.Template.Child()
    daily_reminder_list = Gtk.Template.Child()
    reminders_calendar = Gtk.Template.Child()
    reminders_add_btn = Gtk.Template.Child()
    reminders_export_btn = Gtk.Template.Child()
    reminders_import_btn = Gtk.Template.Child()
    
    # Journal
    journal_stack = Gtk.Template.Child()
    journal_list = Gtk.Template.Child()
    journal_new_btn = Gtk.Template.Child()
    journal_empty_add_btn = Gtk.Template.Child()
    
    # Journal Editor
    editor_back_btn = Gtk.Template.Child()
    editor_save_btn = Gtk.Template.Child()
    editor_title_entry = Gtk.Template.Child()
    editor_text_view = Gtk.Template.Child()
    editor_bold_btn = Gtk.Template.Child()
    editor_italic_btn = Gtk.Template.Child()
    editor_underline_btn = Gtk.Template.Child()
    editor_bullet_btn = Gtk.Template.Child()
    editor_align_left_btn = Gtk.Template.Child()
    editor_align_right_btn = Gtk.Template.Child()
    editor_align_center_btn = Gtk.Template.Child()
    editor_align_fill_btn = Gtk.Template.Child()

    # Layouts
    layouts_stack = Gtk.Template.Child()
    layouts_list = Gtk.Template.Child()
    layouts_add_btn = Gtk.Template.Child()
    layouts_empty_add_btn = Gtk.Template.Child()
    
    # Layout Editor
    layout_editor_back_btn = Gtk.Template.Child()
    layout_editor_title = Gtk.Template.Child()
    layout_editor_edit_btn = Gtk.Template.Child()
    layout_editor_add_btn = Gtk.Template.Child()
    layout_flowbox = Gtk.Template.Child()

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
    settings_api_key_entry = Gtk.Template.Child()
    settings_city_entry = Gtk.Template.Child()
    settings_api_save_btn = Gtk.Template.Child()
    settings_city_save_btn = Gtk.Template.Child()

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
        
        self.journal_editor_view = JournalEditorView(
            window=self,
            db=self.db,
            builder=self
        )

        self.reminders_view = RemindersView(
            window=self, 
            db=self.db, 
            builder=self
        )
        
        self.collections_view = CollectionsView(
            window=self,
            db=self.db,
            builder=self
        )
        
        self.collection_editor_view = CollectionEditorView(
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
        config = self.get_application().config
        provider = config.get("api_provider", "trefle")
        if provider == "perenual":
            self.api_provider_row.set_selected(1)
        else:
            self.api_provider_row.set_selected(0)
            
        self.api_provider_row.connect("notify::selected", self.on_api_provider_changed)

        # API Key
        self.settings_api_key_entry.set_text(config.get("api_key", ""))

        # Weather Location
        self.settings_city_entry.set_text(config.get("city", ""))
        
        # Save Buttons
        self.settings_api_save_btn.connect("clicked", self.on_save_api_key)
        self.settings_city_save_btn.connect("clicked", self.on_save_city)

    def on_api_provider_changed(self, row, pspec):
        index = row.get_selected()
        provider = "trefle" if index == 0 else "perenual"
        self.get_application().config["api_provider"] = provider
        self.get_application().save_config()

    def on_save_api_key(self, btn):
        key = self.settings_api_key_entry.get_text().strip()
        self.get_application().config["api_key"] = key
        self.get_application().save_config()
        self.show_toast("API Key Saved")

    def on_save_city(self, btn):
        city = self.settings_city_entry.get_text().strip()
        self.get_application().config["city"] = city
        self.get_application().save_config()
        self.show_toast("Location Saved")
        # Trigger weather update if needed
        self.dashboard_view.refresh()

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
                   self.sidebar_btn_4, self.sidebar_btn_5, self.sidebar_btn_6, self.sidebar_btn_7]:
            btn.connect("clicked", self.on_sidebar_toggle_clicked)
        
        # Sidebar Close Button
        self.sidebar_close_btn.connect("clicked", self.on_sidebar_close_clicked)
        self.split_view.connect("notify::collapsed", self.update_sidebar_close_btn)
        self.split_view.connect("notify::pin-sidebar", self.update_sidebar_close_btn)
        self.update_sidebar_close_btn(self.split_view, None)

    def on_sidebar_close_clicked(self, btn):
        self.split_view.set_show_sidebar(False)

    def update_sidebar_close_btn(self, split_view, pspec):
        collapsed = split_view.get_collapsed()
        pinned = split_view.get_pin_sidebar()
        self.sidebar_close_btn.set_visible(collapsed and not pinned)

    def on_plant_selected(self, plant_data):
        """
        Callback used by Search and Garden views to navigate to details.
        """
        self.detail_view.load_plant(plant_data)

    def open_journal_editor(self, entry_id=None, title="", content=""):
        self.journal_editor_view.open_entry(entry_id, title, content)
        self.main_stack.set_visible_child_name("journal_editor_page")

    def close_journal_editor(self, saved=False):
        self.main_stack.set_visible_child_name("explorer_page")
        if saved:
            self.journal_view.refresh()

    def open_layout_editor(self, l_id, name, l_type):
        self.collection_editor_view.load_layout(l_id, name, l_type)
        self.main_stack.set_visible_child_name("layout_editor_page")

    def close_layout_editor(self, refresh=False):
        self.main_stack.set_visible_child_name("explorer_page")
        if refresh:
            self.collections_view.refresh()

    def on_sidebar_toggle_clicked(self, btn):
        is_visible = self.split_view.get_show_sidebar()
        self.split_view.set_show_sidebar(not is_visible)
    
    def on_sidebar_row_selected(self, box, row):
        if not row: return
        title = row.get_title()
        
        page_map = {
            "Dashboard": "home_view",
            "Plant Search": "search_view",
            "My Plants": "fav_view",
            "Reminders": "reminders_view",
            "Journal": "journal_view",
            "Settings": "settings_view",
            "My Gardens": "layouts_view"
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
        elif target == "layouts_view":
            self.collections_view.refresh()

    def show_toast(self, message):
        """Helper to show toasts from sub-views"""
        self.toast_overlay.add_toast(Adw.Toast.new(message))
