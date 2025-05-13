import csv
import os
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk 

# Funktion zum Einlesen der CSV-Datei und Anzeigen im Treeview
def load_csv(file_path):
    print(f"Lade CSV-Datei: {file_path}")  # Debugging-Ausgabe
    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        headers = next(reader)  # Erste Zeile als Header (Energieträger)
        tree["columns"] = headers[1:]  # Spaltenüberschriften (ohne die erste Spalte)
        tree.heading("#0", text="Jahr", anchor="w")  # Erste Spalte für Jahreszahlen
        tree.column("#0", anchor="w", width=100)  # Breite der ersten Spalte

        # Spaltenüberschriften und Breite festlegen
        for header in headers[1:]:
            tree.heading(header, text=header, anchor="w")
            tree.column(header, anchor="w", width=150)

        # Alte Daten löschen
        for row in tree.get_children():
            tree.delete(row)

        # Daten aus der CSV-Datei hinzufügen
        for row in reader:
            tree.insert("", tk.END, text=row[0], values=row[1:])  # Erste Spalte als Text, Rest als Werte

# Funktion zum Verarbeiten der ausgewählten Datei
def open_file():
    file_path = filedialog.askopenfilename(
        title="Wähle eine CSV-Datei aus",
        filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")]
    )
    if file_path: 
        load_csv(file_path)
    else:
        print("Keine Datei ausgewählt.")

# Funktion zum Laden der lokalen CSV-Datei, wenn "Deutschland" ausgewählt ist
def update_table(*args):
    print(f"Ausgewählte Option: {selected_option.get()}")  # Debugging-Ausgabe
    if selected_option.get() == "Deutschland":
        base_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_path, "energiedaten.csv")
        print(f"Überprüfe Datei: {file_path}")  # Debugging-Ausgabe
        if os.path.exists(file_path):
            load_csv(file_path)
        else:
            print(f"Die Datei '{file_path}' wurde nicht gefunden.")
    else:
        # Tabelle leeren, wenn ein anderes Land ausgewählt ist
        for row in tree.get_children():
            tree.delete(row)

# Tkinter-Fenster erstellen
root = tk.Tk()
root.title("Primärenergieverbrauch")

# Festgelegter Pfad für das Icon
base_path = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base_path, "dbay-icon.ico")
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

# Dropdown-Menü-Änderung überwachen
selected_option.trace("w", update_table)

# Zweites Dropdown-Menü hinzufügen
energy_options = ["Steinkohle", "Braunkohle", "Mineralöle", "Gase", "Erneuerbare Energien", "Sonstige Energieträger", "Kernenergie"]
selected_energy = tk.StringVar(value="Energieträger auswählen")
energy_dropdown = ttk.Combobox(root, textvariable=selected_energy, values=energy_options, font=("Arial", 12), state="readonly")
energy_dropdown.place(relx=0.5, rely=0.15, anchor="center")  # Position unter dem ersten Dropdown-Menü

# Treeview für die Tabelle hinzufügen
tree = ttk.Treeview(root, show="headings")
tree.place(relx=0.5, rely=0.6, anchor="center", relwidth=0.9, relheight=0.6)  # Position und Größe anpassen

# Scrollbar für die Tabelle hinzufügen
scrollbar = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.place(relx=0.95, rely=0.6, anchor="center", relheight=0.6)

# Hauptloop starten
root.mainloop()

