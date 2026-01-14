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

        # Migration: Add title column to journal if it doesn't exist
        try:
            self.cursor.execute("ALTER TABLE journal ADD COLUMN title TEXT")
        except sqlite3.OperationalError:
            pass # Column likely exists

        # Layouts / Collections
        # Check for old schema
        try:
            self.cursor.execute("SELECT width FROM layouts LIMIT 1")
            # If successful, we have the old schema. Drop it.
            self.cursor.execute("DROP TABLE layout_items")
            self.cursor.execute("DROP TABLE layouts")
        except sqlite3.OperationalError:
            # Table doesn't exist or column doesn't exist (already migrated)
            pass

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS layouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                type TEXT,
                created_date DATE DEFAULT (date('now'))
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS layout_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                layout_id INTEGER,
                plant_id INTEGER,
                FOREIGN KEY(layout_id) REFERENCES layouts(id) ON DELETE CASCADE
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
        self.cursor.execute("DELETE FROM layout_items WHERE plant_id=?", (p_id,))
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

    def complete_reminder(self, r_id):
        self.cursor.execute("UPDATE reminders SET completed=1 WHERE id=?", (r_id,))
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

    def update_journal_entry(self, j_id, title, content):
        self.cursor.execute(
            "UPDATE journal SET title=?, content=? WHERE id=?",
            (title, content, j_id)
        )
        self.conn.commit()
        return True

    # --- Layouts (Collections) ---
    def create_layout(self, name, type_val):
        self.cursor.execute("INSERT INTO layouts (name, type) VALUES (?, ?)", (name, type_val))
        self.conn.commit()
        return self.cursor.lastrowid

    def update_layout(self, l_id, name, type_val):
        self.cursor.execute("UPDATE layouts SET name=?, type=? WHERE id=?", (name, type_val, l_id))
        self.conn.commit()
        return True

    def get_layouts(self):
        self.cursor.execute("SELECT id, name, type, created_date FROM layouts ORDER BY created_date DESC")
        return self.cursor.fetchall()

    def delete_layout(self, l_id):
        self.cursor.execute("DELETE FROM layouts WHERE id=?", (l_id,))
        self.cursor.execute("DELETE FROM layout_items WHERE layout_id=?", (l_id,))
        self.conn.commit()
        return True

    def get_layout_items(self, l_id):
        # Join with favorites to get plant name/image
        self.cursor.execute('''
            SELECT li.id, li.plant_id, f.common_name, f.image_url 
            FROM layout_items li
            LEFT JOIN favorites f ON li.plant_id = f.id
            WHERE li.layout_id = ?
        ''', (l_id,))
        return self.cursor.fetchall()

    def add_layout_item(self, l_id, plant_id):
        self.cursor.execute("INSERT INTO layout_items (layout_id, plant_id) VALUES (?, ?)", (l_id, plant_id))
        self.conn.commit()
        return True

    def remove_layout_item(self, l_id, plant_id):
        # Removes all instances of this plant from the layout?
        # Or should we pass the item id? For UI simplicity, passing plant_id is often easier if we assume uniqueness or don't care which one.
        # But if we list items, we usually have item_id. 
        # However, looking at the previous implementation, it removed by coords.
        # Let's support removing by item_id if possible, but the plan said update to remove plant_id.
        # Let's stick to removing by plant_id for now as the prompt implies assigning plants.
        self.cursor.execute("DELETE FROM layout_items WHERE layout_id=? AND plant_id=?", (l_id, plant_id))
        self.conn.commit()
        return True

    def get_layouts_for_plant(self, plant_id):
        self.cursor.execute("SELECT layout_id FROM layout_items WHERE plant_id=?", (plant_id,))
        rows = self.cursor.fetchall()
        return [r[0] for r in rows]

    def clear_plant_layouts(self, plant_id):
        self.cursor.execute("DELETE FROM layout_items WHERE plant_id=?", (plant_id,))
        self.conn.commit()
        return True

    def get_collections_count(self):
        self.cursor.execute("SELECT COUNT(*) FROM layouts")
        return self.cursor.fetchone()[0]
