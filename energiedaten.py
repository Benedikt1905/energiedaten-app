import csv
import sqlite3
import os
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk 

# Erstelle einen absoluten Pfad zur Datenbankdatei (im selben Verzeichnis wie das Skript)
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "energiedaten.db")

# Verbindung zur SQLite-Datenbank
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Tabelle erstellen
cursor.execute('''
    CREATE TABLE IF NOT EXISTS energieverbrauch (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        traeger TEXT NOT NULL,
        jahr INTEGER NOT NULL,
        wert INTEGER NOT NULL
    )
''')
conn.commit()
conn.close()

# Funktion zum Verarbeiten der ausgewählten Datei
def open_file():
    file_path = filedialog.askopenfilename(
        title="Wähle eine CSV-Datei aus",
        filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")]
    )
    if file_path:  # Prüfen, ob eine Datei ausgewählt wurde
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                print(row)
    else:
        print("Keine Datei ausgewählt.")

# Tkinter-Fenster erstellen
root = tk.Tk()
root.title("Primärenergieverbrauch")

# Festgelegter Pfad für das Icon
base_path = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dbay-icon.ico")
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)
else:
    print(f"Icon-Datei '{icon_path}' nicht gefunden. Standard-Icon wird verwendet.")

# Fenster auf volle Bildschirmgröße setzen
root.state("zoomed")

# Erstes Dropdown-Menü hinzufügen
options = ["Deutschland", "Frankreich", "Großbritannien", "USA"]
selected_option = tk.StringVar(value="Land auswählen")
dropdown = ttk.Combobox(root, textvariable=selected_option, values=options, font=("Arial", 12), state="readonly")
dropdown.place(relx=0.5, rely=0.1, anchor="center")  # Position oben in der Mitte

# Zweites Dropdown-Menü hinzufügen
energy_options = ["Steinkohle", "Braunkohle", "Mineralöle", "Gase", "Erneuerbare Energien","Sonstige Energieträger", "Kernenergie"]
selected_energy = tk.StringVar(value="Energieträger auswählen")
energy_dropdown = ttk.Combobox(root, textvariable=selected_energy, values=energy_options, font=("Arial", 12), state="readonly")
energy_dropdown.place(relx=0.5, rely=0.15, anchor="center")  # Position unter dem ersten Dropdown-Menü

# Button hinzufügen (unter dem zweiten Dropdown-Menü)
button = tk.Button(root, text="Datei auswählen", command=open_file, font=("Arial", 12))
button.place(relx=0.5, rely=0.25, anchor="center")  # Position unter dem zweiten Dropdown-Menü

# Hauptloop starten
root.mainloop() 
