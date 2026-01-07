import sqlite3
import os
from datetime import datetime

def get_db_path():
    data_dir = os.path.expanduser("~/.local/share/flora")
    # In a Flatpak, this usually maps to ~/.var/app/org.gnome.Flora/data
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, 'flora.db')

def init_db():
    conn = sqlite3.connect(get_db_path())
    conn.execute('''CREATE TABLE IF NOT EXISTS gardens 
                    (id INTEGER PRIMARY KEY, name TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS plants 
                    (id INTEGER PRIMARY KEY, name TEXT, garden_id INTEGER, 
                     planting_date DATE, sunlight TEXT, water_interval INTEGER DEFAULT 7,
                     species_id INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS journal_entries 
                    (id INTEGER PRIMARY KEY, plant_id INTEGER, 
                     entry_date DATE, note TEXT, status TEXT, photo TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS care_guides 
                    (id INTEGER PRIMARY KEY, species TEXT, sunlight TEXT, interval INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS tasks 
                    (id INTEGER PRIMARY KEY, description TEXT, due_date DATE, completed INTEGER DEFAULT 0)''')
    
    cursor = conn.execute("SELECT COUNT(*) FROM gardens")
    if cursor.fetchone()[0] == 0:
        conn.execute("INSERT INTO gardens (name) VALUES ('Home Garden')")

    cursor = conn.execute("SELECT COUNT(*) FROM care_guides")
    if cursor.fetchone()[0] == 0:
        conn.executemany("INSERT INTO care_guides (species, sunlight, interval) VALUES (?, ?, ?)", [
            ('Monstera Deliciosa', 'Partial Shade', 7),
            ('Snake Plant', 'Full Shade', 14),
            ('Pothos', 'Partial Shade', 5),
            ('Lavender', 'Full Sun', 3),
            ('Succulent', 'Full Sun', 10)
        ])
    conn.commit()
    conn.close()

def calculate_age(date_str):
    if not date_str: return "New"
    try:
        born = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        diff = today - born
        days = diff.days
        if days <= 0: return "Today"
        if days < 30: return f"{days}d"
        months = days // 30
        if months < 12: return f"{months}m"
        return f"{months // 12}y"
    except: return "New"

def get_all_journal_entries():
    conn = sqlite3.connect(get_db_path()) # Ensure you're using the path helper we created earlier
    query = """
        SELECT j.id, j.entry_date, j.note, p.name, j.photo 
        FROM journal_entries j 
        JOIN plants p ON j.plant_id = p.id 
        ORDER BY j.entry_date DESC
    """
    cursor = conn.execute(query)
    entries = cursor.fetchall()
    conn.close()
    return entries
