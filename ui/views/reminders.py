from gi.repository import Gtk, Adw

class RemindersView:
    def __init__(self, window, db, builder):
        self.window = window
        self.db = db

        # --- UI References ---
        self.stack = builder.reminder_stack
        self.list_box = builder.reminder_list
        self.task_entry = builder.reminder_entry
        self.date_entry = builder.reminder_date_entry
        self.add_btn = builder.add_reminder_button
        self.calendar_btn = builder.calendar_button

        # --- Setup Calendar Popover ---
        self._setup_calendar()

        # --- Connect Signals ---
        self.add_btn.connect("clicked", self._on_add_reminder_clicked)

    def refresh(self):
        """Reloads the reminder list from the database."""
        self._clear_list()
        reminders = self.db.get_reminders()
        
        if not reminders:
            self.stack.set_visible_child_name("empty")
        else:
            self.stack.set_visible_child_name("list")
            for r_id, task, date in reminders:
                row = Adw.ActionRow(title=task)
                row.set_subtitle(f"Due: {date}")
                
                # Delete button
                del_btn = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER)
                del_btn.add_css_class("flat")
                del_btn.connect("clicked", lambda b, rid=r_id, r=row: self._remove_reminder(rid, r))
                
                row.add_suffix(del_btn)
                self.list_box.append(row)

    def _setup_calendar(self):
        self.calendar_popover = Gtk.Popover()
        self.calendar_popover.set_parent(self.calendar_btn)
        
        self.calendar_widget = Gtk.Calendar()
        self.calendar_popover.set_child(self.calendar_widget)
        
        self.calendar_btn.connect("clicked", lambda b: self.calendar_popover.popup())
        self.calendar_widget.connect("day-selected", self._on_date_selected)

    def _on_date_selected(self, calendar):
        dt = calendar.get_date()
        date_str = dt.format("%Y-%m-%d")
        self.date_entry.set_text(date_str)
        self.calendar_popover.popdown()

    def _on_add_reminder_clicked(self, btn):
        task = self.task_entry.get_text()
        date = self.date_entry.get_text()
        
        if task.strip() and date.strip():
            if self.db.add_reminder(task, date):
                self.task_entry.set_text("")
                self.date_entry.set_text("")
                self.refresh()
                self.window.show_toast("Reminder added!")
        else:
            self.window.show_toast("Task and date are required")

    def _remove_reminder(self, r_id, row):
        self.db.delete_reminder(r_id)
        self.list_box.remove(row)
        if self.list_box.get_first_child() is None:
            self.stack.set_visible_child_name("empty")

    def _clear_list(self):
        while child := self.list_box.get_first_child():
            self.list_box.remove(child)
