import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3
import os

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

# path to data files
file_path_de = r'data/Primärverbrauch DE.csv'
file_path_fr = r'data/Primärverbrauch FR.json'
file_path_gb = r'data/Primärverbrauch GB.db'

# global variables
df = pd.DataFrame()
country_var = tk.StringVar()
energy_var = tk.StringVar()
year_var = tk.StringVar()

# Top-Frame für Dropdown-Menüs
top_frame = tk.Frame(root, bg="white")
top_frame.pack(pady=10)

# Styles für Dropdown-Menüs
style = ttk.Style()
style.configure("TCombobox", font=("Arial", 20), fieldbackground="white", background="white", foreground="black")

# Dropdown-Menüs für Land, Energieträger und Jahr
tk.Label(top_frame, text="Land:", font=("Arial", 16), bg="white", fg="black").grid(row=0, column=0, padx=5, pady=5, sticky="w")
country_dropdown = ttk.Combobox(top_frame, textvariable=country_var, state="readonly", style="TCombobox", font=("Arial", 16))
country_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="w")

tk.Label(top_frame, text="Energieträger:", font=("Arial", 16), bg="white", fg="black").grid(row=1, column=0, padx=5, pady=5, sticky="w")
energy_dropdown = ttk.Combobox(top_frame, textvariable=energy_var, state="readonly", style="TCombobox", font=("Arial", 16))
energy_dropdown.grid(row=1, column=1, padx=5, pady=5, sticky="w")

tk.Label(top_frame, text="Jahr:", font=("Arial", 16), bg="white", fg="black").grid(row=2, column=0, padx=5, pady=5, sticky="w")
year_dropdown = ttk.Combobox(top_frame, textvariable=year_var, state="readonly", style="TCombobox", font=("Arial", 16))
year_dropdown.grid(row=2, column=1, padx=5, pady=5, sticky="w")

# Middle-Frame für Statistik-Labels und Kreisdiagramm
middle_frame = tk.Frame(root, bg="white")
middle_frame.pack(pady=10)

# Statistik-Labels
stat_labels = {}
for i, label in enumerate(["Maximaler Jahresverbrauch", "Durchschn. Jahresverbrauch", "Minimaler Jahresverbrauch"]):
    tk.Label(middle_frame, text=label + ":", anchor="w", font=("Arial", 16, "bold"), bg="white", fg="black").grid(row=i, column=0, sticky="w", padx=5, pady=2)
    stat_labels[label] = tk.Label(middle_frame, text="... PJ", relief="sunken", font=("Arial", 16), bg="white", fg="black")
    stat_labels[label].grid(row=i, column=1, padx=5, pady=2)

# Kreisdiagramm
fig, ax = plt.subplots(figsize=(5, 4))
canvas = FigureCanvasTkAgg(fig, master=middle_frame)
canvas.get_tk_widget().grid(row=0, column=2, rowspan=3, padx=20, pady=10)

# Label für "Keine Werte verfügbar"
no_data_label = tk.Label(middle_frame, text="Keine Werte verfügbar", font=("Arial", 16), fg="red", bg="white")
no_data_label.grid(row=3, column=2, pady=10)
no_data_label.grid_remove()

# Table-Frame
table_frame = tk.Frame(root, bg="white", bd=1, relief="solid")
table_frame.pack(padx=10, pady=10)

# Styles für die Tabelle
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

# load data from CSV, JSON or DB
def load_csv_or_json_or_db():
    global df
    try:
        selected_country = country_var.get()
        if selected_country == "Deutschland":
            raw_df = pd.read_csv(file_path_de, sep=';', encoding='utf-8')
            df = raw_df.fillna(0)
            df = df.set_index(raw_df.columns[0]).T.reset_index()
            df.rename(columns={df.columns[0]: "Jahr"}, inplace=True)
            df["Jahr"] = pd.to_numeric(df["Jahr"], errors='coerce').fillna(0).astype(int)
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

        energy_data = selected_row.iloc[0, 1:]  # Alle Spalten außer "Jahr"
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

# Display data
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

        # Update Pie Chart based on selected year
        update_pie_chart()
    except Exception as e:
        messagebox.showerror("Fehler beim Anzeigen der Daten", str(e))

# Footer-Frame
footer_frame = tk.Frame(root, bg="lightgrey", height=30)
footer_frame.pack(side="bottom", fill="x")

# Text für den Footer
footer_label = tk.Label(
    footer_frame,
    text="2025 | made by Benedikt Krings | Version: 3.1.1",
    font=("Arial", 12),
    bg="lightgrey",
    fg="black"
)
footer_label.pack(pady=5)

# Start Application
country_dropdown['values'] = ["Deutschland", "Frankreich", "Großbritannien"]
country_dropdown.bind("<<ComboboxSelected>>", lambda e: load_csv_or_json_or_db())
country_dropdown.current(0)
load_csv_or_json_or_db()
root.mainloop()
