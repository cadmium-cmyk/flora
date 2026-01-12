import sqlite3
import os
from gi.repository import GLib

class Database:
    def __init__(self):
        data_dir = os.path.join(GLib.get_user_data_dir(), "flora")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        self.db_path = os.path.join(data_dir, "plants.db")
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY,
                common_name TEXT,
                scientific_name TEXT,
                family TEXT,
                genus TEXT,
                year TEXT,
                bibliography TEXT,
                edible TEXT,
                vegetable TEXT,
                image_url TEXT,
                habit TEXT,
                harvest TEXT,
                light TEXT,
                notes TEXT,
                added_date DATE DEFAULT (date('now')),
                last_watered TEXT
            )
        ''')
        
        # Migration: Add new columns if they don't exist
        columns_to_add = ['family', 'genus', 'year', 'bibliography', 'edible', 'vegetable']
        for col in columns_to_add:
            try:
                self.cursor.execute(f"ALTER TABLE favorites ADD COLUMN {col} TEXT")
            except sqlite3.OperationalError:
                pass  # Column likely exists

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT,
                due_date DATE,
                completed INTEGER DEFAULT 0
            )
        ''')
        
        # New Journal Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                date DATE DEFAULT (date('now'))
            )
        ''')
        
        self.conn.commit()

    def add_favorite(self, p_id, common, sci, family, genus, year, bib, edible, veg, img, habit, harvest, light, notes):
        try:
            self.cursor.execute(
                "INSERT INTO favorites (id, common_name, scientific_name, family, genus, year, bibliography, edible, vegetable, image_url, habit, harvest, light, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (p_id, common, sci, family, genus, year, bib, edible, veg, img, habit, harvest, light, notes)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_favorite(self, p_id):
        self.cursor.execute("DELETE FROM favorites WHERE id=?", (p_id,))
        self.conn.commit()
        return True

    def update_favorite(self, p_id, common, sci, family, genus, year, bib, edible, veg, habit, harvest, light, notes, image_url=None):
        if image_url:
            self.cursor.execute(
                "UPDATE favorites SET common_name=?, scientific_name=?, family=?, genus=?, year=?, bibliography=?, edible=?, vegetable=?, habit=?, harvest=?, light=?, notes=?, image_url=? WHERE id=?",
                (common, sci, family, genus, year, bib, edible, veg, habit, harvest, light, notes, image_url, p_id)
            )
        else:
            self.cursor.execute(
                "UPDATE favorites SET common_name=?, scientific_name=?, family=?, genus=?, year=?, bibliography=?, edible=?, vegetable=?, habit=?, harvest=?, light=?, notes=? WHERE id=?",
                (common, sci, family, genus, year, bib, edible, veg, habit, harvest, light, notes, p_id)
            )
        self.conn.commit()
        return True

    def water_plant(self, p_id, timestamp):
        self.cursor.execute("UPDATE favorites SET last_watered=? WHERE id=?", (timestamp, p_id))
        self.conn.commit()
        return True

    def add_reminder(self, task, date):
        self.cursor.execute("INSERT INTO reminders (task, due_date) VALUES (?, ?)", (task, date))
        self.conn.commit()
        return True
    
    def get_reminders(self):
        self.cursor.execute("SELECT id, task, due_date FROM reminders WHERE completed=0 ORDER BY due_date ASC")
        return self.cursor.fetchall()

    def delete_reminder(self, r_id):
        self.cursor.execute("DELETE FROM reminders WHERE id=?", (r_id,))
        self.conn.commit()
        return True
        
    def add_journal_entry(self, title, content):
        self.cursor.execute("INSERT INTO journal (title, content) VALUES (?, ?)", (title, content))
        self.conn.commit()
        return True
        
    def get_journal_entries(self):
        self.cursor.execute("SELECT id, title, content, date FROM journal ORDER BY date DESC")
        return self.cursor.fetchall()

    def delete_journal_entry(self, j_id):
        self.cursor.execute("DELETE FROM journal WHERE id=?", (j_id,))
        self.conn.commit()
        return True
