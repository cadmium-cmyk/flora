import datetime
import uuid
import os
from gi.repository import Gtk, Adw, Gio

def generate_ics(reminders):
    """
    Generates an ICS string from a list of (task, date_str) tuples.
    date_str format: YYYY-MM-DD
    """
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Flora//NONSGML v1.0//EN",
    ]
    
    # Use timezone-aware UTC if possible, else fallback (environment dependent)
    dtstamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    
    for task, date_str in reminders:
        # Convert YYYY-MM-DD to YYYYMMDD
        try:
            dt_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            dt_val = dt_obj.strftime("%Y%m%d")
        except ValueError:
            continue # Skip invalid dates

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uuid.uuid4()}")
        lines.append(f"DTSTAMP:{dtstamp}")
        lines.append(f"DTSTART;VALUE=DATE:{dt_val}")
        lines.append(f"SUMMARY:{task}")
        lines.append("END:VEVENT")
        
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)

def parse_ics(content):
    """
    Parses an ICS string and returns a list of (task, date_str) tuples.
    """
    reminders = []
    
    lines = content.splitlines()
    
    in_event = False
    current_summary = None
    current_dtstart = None
    
    for line in lines:
        line = line.strip()
        if line == "BEGIN:VEVENT":
            in_event = True
            current_summary = None
            current_dtstart = None
        elif line == "END:VEVENT":
            if in_event and current_summary and current_dtstart:
                reminders.append((current_summary, current_dtstart))
            in_event = False
        elif in_event:
            if line.startswith("SUMMARY:"):
                current_summary = line[8:]
            elif line.startswith("DTSTART"):
                # Handle DTSTART;VALUE=DATE:20231025
                # or DTSTART:20231025T120000Z
                parts = line.split(":", 1)
                if len(parts) == 2:
                    val = parts[1]
                    # Try to parse YYYYMMDD
                    if len(val) >= 8:
                        date_part = val[:8]
                        try:
                            d = datetime.datetime.strptime(date_part, "%Y%m%d")
                            current_dtstart = d.strftime("%Y-%m-%d")
                        except ValueError:
                            pass

    return reminders

class RemindersView:
    def __init__(self, window, db, builder):
        self.window = window
        self.db = db

        # --- UI References ---
        self.upcoming_stack = builder.reminder_stack
        self.upcoming_list = builder.reminder_list
        self.daily_stack = builder.daily_reminder_stack
        self.daily_list = builder.daily_reminder_list
        self.main_calendar = builder.reminders_calendar
        
        # New Add Button in Header
        self.add_btn = builder.reminders_add_btn
        
        # Import/Export Buttons
        self.export_btn = builder.reminders_export_btn
        self.import_btn = builder.reminders_import_btn

        # --- Setup Main Calendar ---
        # GTK4 Calendar selection
        self.main_calendar.connect("notify::day", self._on_main_calendar_day_selected)
        self.main_calendar.connect("notify::month", self._on_main_calendar_day_selected)
        self.main_calendar.connect("notify::year", self._on_main_calendar_day_selected)

        # --- Connect Signals ---
        self.add_btn.connect("clicked", self._show_add_reminder_dialog)
        self.export_btn.connect("clicked", self._on_export_clicked)
        self.import_btn.connect("clicked", self._on_import_clicked)

    def refresh(self):
        """Reloads the reminder list from the database."""
        self._update_marks()
        self._update_daily_list()
        self._update_upcoming_list()

    def _update_marks(self):
        reminders = self.db.get_reminders()
        self.main_calendar.clear_marks()
        for _, _, date_str in reminders:
            try:
                parts = date_str.split('-')
                if len(parts) == 3:
                    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                    current_date = self.main_calendar.get_date()
                    if current_date.get_year() == y and current_date.get_month() == m:
                         self.main_calendar.mark_day(d)
            except ValueError:
                pass

    def _update_daily_list(self):
        self._clear_list(self.daily_list)
        
        dt = self.main_calendar.get_date()
        date_str = dt.format("%Y-%m-%d")
        
        reminders = self.db.get_reminders()
        # Filter for this date
        day_tasks = [r for r in reminders if r[2] == date_str]
        
        if not day_tasks:
            self.daily_stack.set_visible_child_name("empty")
        else:
            self.daily_stack.set_visible_child_name("list")
            for r_id, task, date in day_tasks:
                row = Adw.ActionRow(title=task)
                
                # Delete button
                del_btn = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER)
                del_btn.add_css_class("flat")
                del_btn.connect("clicked", lambda b, rid=r_id, r=row: self._remove_reminder(rid, r))
                
                row.add_suffix(del_btn)
                self.daily_list.append(row)

    def _update_upcoming_list(self):
        self._clear_list(self.upcoming_list)
        reminders = self.db.get_reminders()
        
        if not reminders:
            self.upcoming_stack.set_visible_child_name("empty")
        else:
            self.upcoming_stack.set_visible_child_name("list")
            for r_id, task, date in reminders:
                row = Adw.ActionRow(title=task)
                row.set_subtitle(f"Due: {date}")
                
                # Delete button
                del_btn = Gtk.Button(icon_name="feather-check-symbolic", valign=Gtk.Align.CENTER)
                del_btn.add_css_class("flat")
                del_btn.connect("clicked", lambda b, rid=r_id, r=row: self._remove_reminder(rid, r))
                
                row.add_suffix(del_btn)
                self.upcoming_list.append(row)

    def _on_main_calendar_day_selected(self, calendar, pspec=None):
        self._update_marks() # In case month changed
        self._update_daily_list()

    def _show_add_reminder_dialog(self, btn):
        dialog = Adw.AlertDialog(
            heading="New Task"
        )
        
        # Content
        group = Adw.PreferencesGroup()
        self.dialog_task_entry = Adw.EntryRow(title="Task")
        self.dialog_date_entry = Adw.EntryRow(title="Due Date (YYYY-MM-DD)")
        
        # Calendar button for dialog
        cal_btn = Gtk.Button(icon_name="today-alt2-symbolic", valign=Gtk.Align.CENTER)
        cal_btn.add_css_class("flat")
        
        # We need a popover for this button
        popover = Gtk.Popover()
        calendar = Gtk.Calendar()
        popover.set_child(calendar)
        cal_btn.connect("clicked", lambda b: popover.set_visible(True))
        
        def on_date_selected(cal, pspec=None):
            dt = cal.get_date()
            self.dialog_date_entry.set_text(dt.format("%Y-%m-%d"))
            popover.set_visible(False)
            
        calendar.connect("notify::day", on_date_selected)
        popover.set_parent(cal_btn) # Important for Gtk4
        
        self.dialog_date_entry.add_suffix(cal_btn)
        
        group.add(self.dialog_task_entry)
        group.add(self.dialog_date_entry)
        
        dialog.set_extra_child(group)
        
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("add", "Add")
        dialog.set_response_appearance("add", Adw.ResponseAppearance.SUGGESTED)
        
        def callback(source, result):
            response = source.choose_finish(result)
            if response == "add":
                task = self.dialog_task_entry.get_text()
                date = self.dialog_date_entry.get_text()
                
                if task.strip() and date.strip():
                    if self.db.add_reminder(task, date):
                        self.refresh()
                        self.window.show_toast("Reminder added!")
                    else:
                        self.window.show_toast("Error adding reminder")
                else:
                    self.window.show_toast("Task and date are required")

        dialog.choose(self.window, None, callback)

    def _on_export_clicked(self, btn):
        dialog = Gtk.FileChooserNative(
            title="Export Reminders",
            transient_for=self.window,
            action=Gtk.FileChooserAction.SAVE,
            accept_label="_Save",
            cancel_label="_Cancel"
        )
        
        filter_ics = Gtk.FileFilter()
        filter_ics.set_name("Calendar Files (*.ics)")
        filter_ics.add_pattern("*.ics")
        dialog.add_filter(filter_ics)
        
        dialog.set_current_name("reminders.ics")
        
        def on_response(d, response):
            if response == Gtk.ResponseType.ACCEPT:
                file = d.get_file()
                path = file.get_path()
                reminders = self.db.get_reminders()
                # reminders is list of (id, task, date)
                data = [(r[1], r[2]) for r in reminders]
                content = generate_ics(data)
                try:
                    with open(path, 'w') as f:
                        f.write(content)
                    self.window.show_toast("Reminders exported!")
                except Exception as e:
                    self.window.show_toast(f"Export failed: {e}")
            d.destroy()
            
        dialog.connect("response", on_response)
        dialog.show()

    def _on_import_clicked(self, btn):
        dialog = Gtk.FileChooserNative(
            title="Import Reminders",
            transient_for=self.window,
            action=Gtk.FileChooserAction.OPEN,
            accept_label="_Open",
            cancel_label="_Cancel"
        )
        
        filter_ics = Gtk.FileFilter()
        filter_ics.set_name("Calendar Files (*.ics)")
        filter_ics.add_pattern("*.ics")
        dialog.add_filter(filter_ics)
        
        def on_response(d, response):
            if response == Gtk.ResponseType.ACCEPT:
                file = d.get_file()
                path = file.get_path()
                try:
                    with open(path, 'r') as f:
                        content = f.read()
                    reminders = parse_ics(content)
                    count = 0
                    for task, date in reminders:
                        if self.db.add_reminder(task, date):
                            count += 1
                    self.refresh()
                    self.window.show_toast(f"Imported {count} reminders!")
                except Exception as e:
                    self.window.show_toast(f"Import failed: {e}")
            d.destroy()
            
        dialog.connect("response", on_response)
        dialog.show()

    def _remove_reminder(self, r_id, row):
        self.db.delete_reminder(r_id)
        self.refresh()

    def _clear_list(self, list_box):
        while child := list_box.get_first_child():
            list_box.remove(child)
