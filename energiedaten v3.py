import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3
import os
import requests
import chardet
import re

# main window with icon
root = tk.Tk()
root.title("Primärenergieverbrauch")
root.config(bg="white")
base_path = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base_path, "img/dbay-icon.ico")
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)
else:
    print(f"Icon-Datei '{icon_path}' nicht gefunden. Standard-Icon wird verwendet.")

# Load logo image
logo_path = os.path.join(base_path, "img/dbay-icon.png")
if os.path.exists(logo_path):
    logo_image = tk.PhotoImage(file=logo_path)
else:
    print(f"Logo-Datei '{logo_path}' nicht gefunden.")
    logo_image = None

# Display logo image in top frame
if logo_image:
    logo_label = tk.Label(root, image=logo_image, bg="white")
    logo_label.place(relx=0.20, rely=-0.04)

# path to data files
file_path_de = r'data/Primärverbrauch DE.csv'
file_path_fr = r'data/Primärverbrauch FR.json'
file_path_gb = r'data/Primärverbrauch GB.db'
api_url = "http://localhost:8000/api/1/primary_energy_consumption"

# global variables
df = pd.DataFrame()
country_var = tk.StringVar()
energy_var = tk.StringVar()
year_var = tk.StringVar()

# Top-Frame and styles for dropdown-menus
top_frame = tk.Frame(root, bg="white")
top_frame.pack(pady=10)
style = ttk.Style()
style.configure("TCombobox", font=("Arial", 20), fieldbackground="white", background="white", foreground="black")

# dropdown menus for country, energy source and year
tk.Label(top_frame, text="Land:", font=("Arial", 16), bg="white", fg="black").grid(row=0, column=0, padx=5, pady=5, sticky="w")
country_dropdown = ttk.Combobox(top_frame, textvariable=country_var, state="readonly", style="TCombobox", font=("Arial", 16))
country_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="w")

tk.Label(top_frame, text="Energieträger:", font=("Arial", 16), bg="white", fg="black").grid(row=1, column=0, padx=5, pady=5, sticky="w")
energy_dropdown = ttk.Combobox(top_frame, textvariable=energy_var, state="readonly", style="TCombobox", font=("Arial", 16))
energy_dropdown.grid(row=1, column=1, padx=5, pady=5, sticky="w")

tk.Label(top_frame, text="Jahr:", font=("Arial", 16), bg="white", fg="black").grid(row=2, column=0, padx=5, pady=5, sticky="w")
year_dropdown = ttk.Combobox(top_frame, textvariable=year_var, state="readonly", style="TCombobox", font=("Arial", 16))
year_dropdown.grid(row=2, column=1, padx=5, pady=5, sticky="w")

# middle frame for statistics and pie chart
middle_frame = tk.Frame(root, bg="white")
middle_frame.pack(pady=10)

# statistics labels
stat_labels = {}
for i, label in enumerate(["Maximaler Jahresverbrauch", "Durchschn. Jahresverbrauch", "Minimaler Jahresverbrauch"]):
    tk.Label(middle_frame, text=label + ":", anchor="w", font=("Arial", 16, "bold"), bg="white", fg="black").grid(row=i, column=0, sticky="w", padx=5, pady=2)
    stat_labels[label] = tk.Label(middle_frame, text="... PJ", relief="sunken", font=("Arial", 16), bg="white", fg="black")
    stat_labels[label].grid(row=i, column=1, padx=5, pady=2)

# pie chart
fig, ax = plt.subplots(figsize=(5, 4))
canvas = FigureCanvasTkAgg(fig, master=middle_frame)
canvas.get_tk_widget().grid(row=0, column=2, rowspan=3, padx=20, pady=10)

# label for "Keine Werte verfügbar"
no_data_label = tk.Label(middle_frame, text="Keine Werte verfügbar", font=("Arial", 16), fg="red", bg="white")
no_data_label.grid(row=3, column=2, pady=10)
no_data_label.grid_remove()

# Table-Frame
table_frame = tk.Frame(root, bg="white", bd=1, relief="solid")
table_frame.pack(padx=10, pady=10)

# styles for the table
style.configure("Treeview",
                rowheight=25,
                font=("Arial", 16),
                borderwidth=1,
                relief="solid",
                background="white",
                fieldbackground="white")
style.configure("Treeview.Heading",
                font=("Arial", 18, "bold"),
                borderwidth=1,
                relief="solid")
style.map("Treeview",
          background=[("selected", "lightblue")],
          foreground=[("selected", "black")])
style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

table = ttk.Treeview(table_frame, show="headings", height=10, style="Treeview")
table.pack(side="left", padx=5, pady=5, fill="both", expand=True)

# Scrollbar hinzufügen
scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
scrollbar.pack(side="right", fill="y")
table.configure(yscrollcommand=scrollbar.set)

# load data from CSV, JSON, DB, or API
def load_csv_or_json_or_db_or_api():
    global df
    try:
        selected_country = country_var.get()
        if selected_country == "Deutschland":
            # Encoding automatisch erkennen
            with open(file_path_de, 'rb') as f:
                rawdata = f.read(4096)
                result = chardet.detect(rawdata)
                detected_encoding = result['encoding'] if result['encoding'] else 'utf-8'
            try:
                raw_df = pd.read_csv(file_path_de, sep=';', encoding=detected_encoding)
            except UnicodeDecodeError:
                messagebox.showerror("Fehler", f"Die Datei '{file_path_de}' konnte nicht mit dem erkannten Encoding '{detected_encoding}' gelesen werden.")
                return

            # Prüfung auf Kommazahlen (mit Punkt oder Komma), Leerzeichen/Tabs, Sonderzeichen und negative Zahlen
            for col in raw_df.columns[1:]:
                for val in raw_df[col].astype(str):
                    if '-' in val:
                        messagebox.showerror("Fehlercode 204", "Fehlerhafte Daten in der CSV Datei. Werte in der CSV Datei dürfen keine negativen Zahlen sein. Bitte überprüfen Sie die Daten in der CSV Datei.")
                        return
                    if ',' in val or '.' in val:
                        messagebox.showerror("Fehlercode 201", "Fehlerhafte Daten in der CSV Datei. Werte in der CSV Datei dürfen keine Kommazahlen sein oder leer sein. Bitte überprüfen Sie die Daten in der CSV Datei.")
                        return
                    if ' ' in val or '\t' in val:
                        messagebox.showerror("Fehlercode 202", "Fehlerhafte Daten in der CSV Datei. Werte dürfen keine Leerzeichen oder TABS enthalten. Bitte überprüfen Sie die Daten in der CSV Datei.")
                        return
                    if not re.fullmatch(r'\d+', val):
                        messagebox.showerror("Fehlercode 203", "Fehlerhafte Daten in der CSV Datei. Werte dürfen keine Sonderzeichen enthalten. Bitte überprüfen Sie die Daten in der CSV Datei.")
                        return
                    if len(val) > 6:
                        messagebox.showerror("Fehlercode 210", "Fehlerhafte Daten in der CSV Datei. Werte dürfen nicht größer als 999999 sein. Bitte überprüfen Sie die Daten in der CSV Datei.")
                        return

            df = raw_df.fillna(0)
            df = df.set_index(raw_df.columns[0]).T.reset_index()
            df.rename(columns={df.columns[0]: "Jahr"}, inplace=True)
            df["Jahr"] = pd.to_numeric(df["Jahr"], errors='coerce').fillna(0).astype(int)

            # Prüfung: Jahr-Spalte darf keinen Wert 0 enthalten
            if (df["Jahr"] == 0).any():
                messagebox.showerror("Fehlercode 205", "Fehlerhafte Daten in der CSV Datei. In der Jahr-Spalte darf der Wert nicht 0 sein oder Sonderzeichen enthalten. Bitte überprüfen Sie die Daten in der CSV Datei.")
                return

            # Prüfung: Jahr muss mindestens 4-stellig sein
            if any(df["Jahr"].apply(lambda x: len(str(x)) < 4)):
                messagebox.showerror("Fehlercode 206", "Fehlerhafte Daten in der CSV Datei. Jeder Jahr-Wert muss mindestens 4-stellig sein (z.B. 1990).")
                return

            # Prüfung: Jahre müssen aufsteigend sortiert sein (jedes Jahr >= vorheriges und <= nächstes)
            jahre = df["Jahr"].tolist()
            for i in range(1, len(jahre)):
                if jahre[i] < jahre[i-1]:
                    messagebox.showerror("Fehlercode 207", f"Fehlerhafte Daten in der CSV Datei. Das Jahr {jahre[i]} ist kleiner als das vorherige Jahr {jahre[i-1]}. Die Jahre müssen aufsteigend sortiert sein.")
                    return
                if jahre[i] == jahre[i-1]:
                    messagebox.showerror("Fehlercode 209", f"Fehlerhafte Daten in der CSV Datei. Das Jahr {jahre[i]} ist doppelt vorhanden. Jeder Jahr-Wert darf nur einmal vorkommen.")
                    return
            for i in range(len(jahre)-1):
                if jahre[i] > jahre[i+1]:
                    messagebox.showerror("Fehlercode 208", f"Fehlerhafte Daten in der CSV Datei. Das Jahr {jahre[i]} ist größer als das nächste Jahr {jahre[i+1]}. Die Jahre müssen aufsteigend sortiert sein.")
                    return
                if jahre[i] == jahre[i+1]:
                    messagebox.showerror("Fehlercode 209", f"Fehlerhafte Daten in der CSV Datei. Das Jahr {jahre[i]} ist doppelt vorhanden. Jeder Jahr-Wert darf nur einmal vorkommen.")
                    return

        elif selected_country == "Frankreich":
            raw_data = pd.read_json(file_path_fr)
            df = pd.DataFrame(raw_data).T.reset_index()
            df.rename(columns={"index": "Jahr"}, inplace=True)
            for col in df.columns[1:]:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        elif selected_country == "Großbritannien":
            conn = sqlite3.connect(file_path_gb)
            query = "SELECT * FROM energieverbrauch ORDER BY Jahr"
            df = pd.read_sql_query(query, conn)
            conn.close()
            df.rename(columns={df.columns[0]: "Jahr"}, inplace=True)
            df["Jahr"] = pd.to_numeric(df["Jahr"], errors='coerce').fillna(0).astype(int)
        elif selected_country == "API":
            response = requests.get(api_url)
            if response.status_code == 200:
                raw_data = response.json()
                # Die eigentlichen Daten liegen im "data"-Key und sind ein Dict: {jahr: {energieträger: wert, ...}, ...}
                api_data = raw_data.get("data", {})
                if not api_data:
                    raise ValueError("Die API hat keine Daten geliefert.")
                # In DataFrame umwandeln: Jahr als Spalte
                df_api = pd.DataFrame.from_dict(api_data, orient="index")
                df_api.index.name = "Jahr"
                df_api.reset_index(inplace=True)
                # Jahr in int umwandeln
                df_api["Jahr"] = pd.to_numeric(df_api["Jahr"], errors='coerce').fillna(0).astype(int)
                for col in df_api.columns[1:]:
                    df_api[col] = pd.to_numeric(df_api[col], errors='coerce').fillna(0)
                df = df_api
            else:
                raise ValueError(f"Fehler beim Abrufen der API-Daten: {response.status_code}")
        else:
            messagebox.showerror("Fehler", "Ungültige Länderauswahl.")
            return
        update_dropdowns()
        display_data()
    except Exception as e:
        messagebox.showerror("Fehler beim Laden der Datei", str(e))

# update dropdown menus
def update_dropdowns():
    try:
        energy_sources = [col for col in df.columns if col != "Jahr"]
        energy_dropdown['values'] = energy_sources
        energy_dropdown.current(0)
        energy_dropdown.bind("<<ComboboxSelected>>", lambda e: display_data())

        years = df["Jahr"].astype(str).tolist()
        year_dropdown['values'] = years
        year_dropdown.current(0)
        year_dropdown.bind("<<ComboboxSelected>>", lambda e: update_pie_chart())
    except Exception as e:
        messagebox.showerror("Fehler beim Aktualisieren der Dropdown-Menüs", str(e))

# update pie chart
def update_pie_chart():
    try:
        selected_year = year_var.get()
        if not selected_year:
            messagebox.showerror("Fehler", "Bitte wählen Sie ein Jahr aus.")
            return

        selected_row = df[df["Jahr"] == int(selected_year)]
        if selected_row.empty:
            messagebox.showerror("Fehler", "Keine Daten für das ausgewählte Jahr verfügbar.")
            return

        energy_data = selected_row.iloc[0, 1:]  # all columns except "Jahr"
        ax.clear()

        if energy_data.sum() == 0:
            wedges, texts = ax.pie([1], colors=["lightgrey"])
            ax.text(0, 0, "Keine Werte\nverfügbar", ha='center', va='center', fontsize=16, color="red")
        else:
            explode = [0.01] * len(energy_data)
            ax.pie(
                energy_data,
                labels=energy_data.index,
                autopct='%1.1f%%',
                explode=explode,
                shadow=True, 
                startangle=90
            )
        canvas.draw()
    except Exception as e:
        messagebox.showerror("Fehler beim Aktualisieren des Kreisdiagramms", str(e))

# Funktion zum Sortieren der Tabelle
def sort_table(column, reverse):
    try:
        if column == "Jahr" or column in df.columns[1:]:  # Nur "Jahr" und Energieträger sortierbar
            sorted_df = df.sort_values(by=column, ascending=not reverse)
            update_table(sorted_df)
            table.heading(column, command=lambda: sort_table(column, not reverse))  # Sortierrichtung umkehren
    except Exception as e:
        messagebox.showerror("Fehler beim Sortieren der Tabelle", str(e))

# Funktion zum Aktualisieren der Tabelle
def update_table(dataframe):
    try:
        table.delete(*table.get_children())
        for i, (_, row) in enumerate(dataframe.iterrows()):
            values = [row["Jahr"]] + list(row[1:])
            tag = "even" if i % 2 == 0 else "odd"
            table.insert("", "end", values=values, tags=(tag,))
    except Exception as e:
        messagebox.showerror("Fehler beim Aktualisieren der Tabelle", str(e))

# Aktualisierte Funktion zum Anzeigen der Daten
def display_data():
    selected_country = country_var.get()
    if not selected_country:
        messagebox.showerror("Fehler", "Bitte wählen Sie ein Land aus.")
        return
    try:
        table.delete(*table.get_children())
        table["columns"] = ["Jahr"] + list(df.columns[1:])
        table.heading("#0", text="", anchor="center")
        table.column("#0", width=0, stretch=tk.NO)
        for col in table["columns"]:
            table.heading(col, text=col, anchor="center", command=lambda c=col: sort_table(c, False))  # Sortierfunktion hinzufügen
            table.column(col, anchor="center", width=170)

        # Paint table line white and grey alternatively
        for i, (_, row) in enumerate(df.iterrows()):
            values = [row["Jahr"]] + list(row[1:])
            tag = "even" if i % 2 == 0 else "odd"
            table.insert("", "end", values=values, tags=(tag,))

        # color tags
        table.tag_configure("even", background="white")
        table.tag_configure("odd", background="lightgrey")

        selected_energy = energy_var.get()
        if selected_energy and selected_energy in df.columns:
            max_value = df[selected_energy].max()
            mean_value = df[selected_energy].mean()
            min_value = df[selected_energy].min()

            stat_labels["Maximaler Jahresverbrauch"].config(text=f"{max_value:.2f} PJ")
            stat_labels["Durchschn. Jahresverbrauch"].config(text=f"{mean_value:.2f} PJ")
            stat_labels["Minimaler Jahresverbrauch"].config(text=f"{min_value:.2f} PJ")

        # Update Pie Chart based on selected year
        update_pie_chart()
    except Exception as e:
        messagebox.showerror("Fehler beim Anzeigen der Daten", str(e))

# Footer-Frame
footer_frame = tk.Frame(root, bg="lightgrey", height=30)
footer_frame.pack(side="bottom", fill="x")

# Text for footer
footer_label = tk.Label(
    footer_frame,
    text="2025 | made by Benedikt Krings | Version: 3.3.0",
    font=("Arial", 12),
    bg="lightgrey",
    fg="black"
)
footer_label.pack(pady=5)

# Start application
country_dropdown['values'] = ["Deutschland", "Frankreich", "Großbritannien", "API"]
country_dropdown.bind("<<ComboboxSelected>>", lambda e: load_csv_or_json_or_db_or_api())
country_dropdown.current(0)
load_csv_or_json_or_db_or_api()
root.mainloop()