import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3
import os

# Hauptfenster
root = tk.Tk()
root.title("Primärenergieverbrauch")

# Pfad zur Icon-Datei
base_path = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base_path, "dbay-icon.ico")
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)
else:
    print(f"Icon-Datei '{icon_path}' nicht gefunden. Standard-Icon wird verwendet.")

# Pfade zu den Dateien
file_path_de = r'data/Primärverbrauch DE.csv'
file_path_fr = r'data/Primärverbrauch FR.json'
file_path_gb = r'data/Primärverbrauch GB.db'

# Globale Variablen
df = pd.DataFrame()
country_var = tk.StringVar()
energy_var = tk.StringVar()

# Layout-Struktur
top_frame = tk.Frame(root)
top_frame.pack(pady=10)

# Stil für die Dropdown-Menüs anpassen
style = ttk.Style()
style.configure("TCombobox", font=("Arial", 20))
style.map("TCombobox",
          fieldbackground=[("readonly", "white")],
          background=[("readonly", "white")],
          foreground=[("readonly", "black")])

# Dropdown-Menüs
tk.Label(top_frame, text="Land:", font=("Arial", 16)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
country_dropdown = ttk.Combobox(top_frame, textvariable=country_var, state="readonly", style="TCombobox", font=("Arial", 16))
country_dropdown.grid(row=1, column=0, padx=5, pady=5, sticky="w")

tk.Label(top_frame, text="Energieträger:", font=("Arial", 16)).grid(row=2, column=0, padx=5, pady=5, sticky="w")
energy_dropdown = ttk.Combobox(top_frame, textvariable=energy_var, state="readonly", style="TCombobox", font=("Arial", 16))
energy_dropdown.grid(row=3, column=0, padx=5, pady=5, sticky="w")

middle_frame = tk.Frame(root)
middle_frame.pack(pady=10)

# Statistik-Labels
stat_labels = {}
for i, label in enumerate(["Maximaler Jahresverbrauch", "Durchschn. Jahresverbrauch", "Minimaler Jahresverbrauch"]):
    tk.Label(middle_frame, text=label + ":", anchor="w", font=("Arial", 16, "bold")).grid(row=i, column=0, sticky="w", padx=5, pady=2)
    stat_labels[label] = tk.Label(middle_frame, text="... PJ", relief="sunken", font=("Arial", 16))
    stat_labels[label].grid(row=i, column=1, padx=5, pady=2)

# Kreisdiagramm
fig, ax = plt.subplots(figsize=(7, 6))
canvas = FigureCanvasTkAgg(fig, master=middle_frame)
canvas.get_tk_widget().grid(row=0, column=2, rowspan=3, padx=20)

# Label für keine Daten
no_data_label = tk.Label(middle_frame, text="Keine Werte verfügbar", font=("Arial", 16), fg="red")
no_data_label.grid(row=3, column=2, pady=10)
no_data_label.grid_remove()

# Tabellen-Frame
table_frame = tk.Frame(root, bd=1, relief="solid")
table_frame.pack(padx=10, pady=10)

# Tabelle mit Stil
style = ttk.Style()
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
table.pack(padx=5, pady=5)

# Daten laden
def load_csv_or_json_or_db():
    global df
    try:
        selected_country = country_var.get()
        if selected_country == "Deutschland":
            raw_df = pd.read_csv(file_path_de, sep=';', encoding='utf-8')
            df = raw_df.fillna(0)
            df = df.set_index(raw_df.columns[0]).T.reset_index()
            df.rename(columns={df.columns[0]: "Jahr"}, inplace=True)
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
        else:
            messagebox.showerror("Fehler", "Ungültige Länderauswahl.")
            return
        update_dropdowns()
        display_data()
    except Exception as e:
        messagebox.showerror("Fehler beim Laden der Datei", str(e))

# Dropdowns aktualisieren
def update_dropdowns():
    try:
        energy_sources = [col for col in df.columns if col != "Jahr"]
        energy_dropdown['values'] = energy_sources
        energy_dropdown.current(0)
        energy_dropdown.bind("<<ComboboxSelected>>", lambda e: display_data())
    except Exception as e:
        messagebox.showerror("Fehler beim Aktualisieren der Dropdown-Menüs", str(e))

# Daten anzeigen
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
            table.heading(col, text=col, anchor="center")
            table.column(col, anchor="center", width=170)

        for _, row in df.iterrows():
            values = [row["Jahr"]] + list(row[1:])
            table.insert("", "end", values=values)

        selected_energy = energy_var.get()
        if selected_energy and selected_energy in df.columns:
            max_value = df[selected_energy].max()
            mean_value = df[selected_energy].mean()
            min_value = df[selected_energy].min()

            stat_labels["Maximaler Jahresverbrauch"].config(text=f"{max_value:.2f} PJ")
            stat_labels["Durchschn. Jahresverbrauch"].config(text=f"{mean_value:.2f} PJ")
            stat_labels["Minimaler Jahresverbrauch"].config(text=f"{min_value:.2f} PJ")

            ax.clear()
            if max_value == 0 and mean_value == 0 and min_value == 0:
                wedges, texts = ax.pie([1], colors=["lightgrey"])
                ax.text(0, 0, "Keine Werte\nverfügbar", ha='center', va='center', fontsize=16, color="red")
            else:
                ax.pie([max_value, mean_value, min_value],
                       labels=["Max", "Durchschnitt", "Min"],
                       autopct='%1.1f%%')
            canvas.draw()
    except Exception as e:
        messagebox.showerror("Fehler bei Anzeige", str(e))

# Start der Anwendung
country_dropdown['values'] = ["Deutschland", "Frankreich", "Großbritannien"]
country_dropdown.bind("<<ComboboxSelected>>", lambda e: load_csv_or_json_or_db())
country_dropdown.current(0)
load_csv_or_json_or_db()
root.mainloop()