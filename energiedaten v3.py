#######################################################################
# Author: Benedikt Krings                                             #
# GitHub Repo: https://github.com/Benedikt1905/energiedaten-app       #
# GitHub Branch: main                                                 #
# Version: 2025060404                                                 #
#          YYYYMMDD Change Number                                     #
#######################################################################

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
import datetime

def log_message(level, message):
    log_dir = os.path.join(base_path, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_path = os.path.join(log_dir, "energiedaten-app.log")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{now}] {level}: {message}\n")

def log_and_show_error(title, message):
    log_message("ERROR", f"{title}: {message}")
    messagebox.showerror(title, message)

def log_and_show_warning(title, message):
    log_message("WARNING", f"{title}: {message}")
    messagebox.showwarning(title, message)

# main window with icon
root = tk.Tk()
root.title("Primärenergieverbrauch v2.5")
root.config(bg="white")
base_path = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base_path, "img/dbay-icon.ico")
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)
else:
    print(f"Icon-Datei '{icon_path}' nicht gefunden. Standard-Icon wird verwendet.")

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
file_path_gb = r'data/Primärverbrauch GB (mit Fehlern).db'
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
# styles for every Combobox entry
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

# Add scrollbar
scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
scrollbar.pack(side="right", fill="y")
table.configure(yscrollcommand=scrollbar.set)

# Function to check the CSV file for malicious code according to the client's security concept ^^
def check_csv_for_malicious_code(file_path):
    suspicious_patterns = [
        r"^=",  
        r"@",
        r"^@",
        r"cmd", r"powershell", r"shell", r"WScript",
        r"WEBSERVICE", r"IMPORTXML", r"IMPORTDATA", r"IMPORTHTML", r"IMPORTRANGE", r"HYPERLINK",
        r"UNICHAR", r"CHAR", r"CONCATENATE", r"EXEC", r"OPEN", r"INCLUDE",
        r"WMIC", r"-EX", r"CREATE", 
        r"DROP", r"DELETE", r"ALTER", r"INSERT", r"UPDATE",
        r"\|", 
        r"\u202e", 
        r"\u202d",  
        r"\u2066", r"\u2067", r"\u2068", r"\u202a", r"\u202b", r"\u202c", r"\u2069",
    ]
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                if any(uc in line for uc in ['\u202e', '\u202d', '\u2066', '\u2067', '\u2068', '\u202a', '\u202b', '\u202c', '\u2069']):
                    log_and_show_warning(
                        "Critical Security Warning!",
                        f"The CSV file contains suspicious Unicode control characters (e.g. RTL/LTR-Override) in line {line_num}.\n"
                        f"Import will be aborted. Check the logs."
                    )
                    return False
                for pattern in suspicious_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        log_and_show_warning(
                            "Critical Security Warning!",
                            f"The CSV file contains potentially malicious or dangerous code in line {line_num}.\n"
                            f"Import will be aborted.\nDetected pattern: {pattern} Check the logs."
                        )
                        return False
        return True
    except Exception as e:
        log_and_show_error("An error occurred during the security check! Please try again. Check the logs", str(e) )
        return False
    
# load data from CSV, JSON, DB, or API
def load_csv_or_json_or_db_or_api():
    global df
    try:
        selected_country = country_var.get()
        if selected_country == "Deutschland":
            # Security check before reading!
            if not check_csv_for_malicious_code(file_path_de):
                return
            # Automatically detect encoding
            with open(file_path_de, 'rb') as f:
                rawdata = f.read(4096)
                result = chardet.detect(rawdata)
                detected_encoding = result['encoding'] if result['encoding'] else 'utf-8'
            try:
                raw_df = pd.read_csv(file_path_de, sep=';', encoding=detected_encoding)
            except UnicodeDecodeError:
                messagebox.showerror("Error", f"The file '{file_path_de}' could not be read with the detected encoding '{detected_encoding}'.")
                return

            # Check for decimal numbers (with dot or comma), spaces/tabs, special characters and negative numbers
            for col in raw_df.columns[1:]:
                for val in raw_df[col].astype(str):
                    if '-' in val:
                        log_and_show_error("Error code 204", "Invalid data in the CSV file. Values in the CSV file must not be negative numbers. Please check the data in the CSV file. Check the logs.")
                        return
                    if ',' in val or '.' in val:
                        log_and_show_error("Error code 201", "Invalid data in the CSV file. Values in the CSV file must not be decimal numbers or empty. Please check the data in the CSV file. Check the logs.")
                        return
                    if ' ' in val or '\t' in val:
                        log_and_show_error("Error code 202", "Invalid data in the CSV file. Values must not contain spaces or TABS. Please check the data in the CSV file. Check the logs.")
                        return
                    if not re.fullmatch(r'\d+', val):
                        log_and_show_error("Error code 203", "Invalid data in the CSV file. Values must not contain special characters. Please check the data in the CSV file. Check the logs.")
                        return
                    if len(val) > 6:
                        log_and_show_error("Error code 211", "Invalid data in the CSV file. Values must not be greater than 999999. Please check the data in the CSV file. Check the logs.")
                        return

            df = raw_df.fillna(0)
            df = df.set_index(raw_df.columns[0]).T.reset_index()
            df.rename(columns={df.columns[0]: "Jahr"}, inplace=True)
            df["Jahr"] = pd.to_numeric(df["Jahr"], errors='coerce').fillna(0).astype(int)

            # Check: Year column must not contain value 0
            if (df["Jahr"] == 0).any():
                log_and_show_error("Error code 205", "Invalid data in the CSV file. The year column must not contain the value 0 or special characters. Please check the data in the CSV file. See the logs.")
                return

            # Check: Year must be at least 4 digits
            if any(df["Jahr"].apply(lambda x: len(str(x)) < 4)):
                log_and_show_error("Error code 206", "Invalid data in the CSV file. Each year value must be at least 4 digits (e.g. 1990). Check the logs.")
                return

            # Check: Years must be sorted in ascending order (each year >= previous and <= next)
            years = df["Jahr"].tolist()
            for i in range(1, len(years)):
                if years[i] < years[i-1]:
                    log_and_show_error("Error code 207", f"Invalid data in the CSV file. The year {years[i]} is less than the previous year {years[i-1]}. Years must be sorted in ascending order. Check ths logs.")
                    return
                if years[i] == years[i-1]:
                    log_and_show_error("Error code 208", f"Invalid data in the CSV file. The year {years[i]} is duplicated. Each year value may only occur once.Ceck the logs.")
                    return
            for i in range(len(years)-1):
                if years[i] > years[i+1]:
                    log_and_show_error("Error code 209", f"Invalid data in the CSV file. The year {years[i]} is greater than the next year {years[i+1]}. Years must be sorted in ascending order. Check the logs.")
                    return
                if years[i] == years[i+1]:
                    log_and_show_error("Error code 210", f"Invalid data in the CSV file. The year {years[i]} is duplicated. Each year value may only occur once. Check the logs")
                    return
        elif selected_country == "Frankreich":
            raw_data = pd.read_json(file_path_fr)
            df = pd.DataFrame(raw_data).T.reset_index()
            df.rename(columns={"index": "Jahr"}, inplace=True)
            for col in df.columns[1:]:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        elif selected_country == "Großbritannien":
            conn = sqlite3.connect(file_path_gb)
            query = "SELECT * FROM energieverbrauch"
            df = pd.read_sql_query(query, conn)
            conn.close()
            df.rename(columns={df.columns[0]: "Jahr"}, inplace=True)
            df["Jahr"] = pd.to_numeric(df["Jahr"], errors='coerce').fillna(0).astype(int)
            # Alle Werte (außer Jahr) auf ganze Zahlen runden
            for col in df.columns:
                if col != "Jahr":
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            # Jahre prüfen und ggf. sortieren
            years = df["Jahr"].tolist()
            years_sorted = sorted(years)
            if years != years_sorted:
                log_and_show_warning(
                    "Warnung: Jahre nicht sortiert",
                    "Die Jahre in der Datenbank sind nicht aufsteigend sortiert. Die Daten werden trotzdem verwendet und die Jahre werden automatisch sortiert."
                )
                df = df.sort_values(by="Jahr").reset_index(drop=True)
                years = df["Jahr"].tolist()
            # Prüfe auf doppelte Jahre nach dem Sortieren
            if len(years) != len(set(years)):
                log_and_show_warning(
                    "Warnung: Doppelte Jahre",
                    "Die Datenbank enthält doppelte Jahre. Die Daten werden trotzdem verwendet, aber doppelte Jahre können zu fehlerhaften Auswertungen führen."
                )
        elif selected_country == "Polen":
            response = requests.get(api_url)
            if response.status_code == 200:
                raw_data = response.json()
                # The actual data is in the "data" key and is a dict: {year: {energy_source: value, ...}, ...}
                api_data = raw_data.get("data", {})
                if not api_data:
                    raise ValueError("The API did not return any data.")
                # Convert to DataFrame: year as column
                df_api = pd.DataFrame.from_dict(api_data, orient="index")
                df_api.index.name = "Jahr"
                df_api.reset_index(inplace=True)
                # Convert year to int
                df_api["Jahr"] = pd.to_numeric(df_api["Jahr"], errors='coerce').fillna(0).astype(int)
                for col in df_api.columns[1:]:
                    df_api[col] = pd.to_numeric(df_api[col], errors='coerce').fillna(0)
                df = df_api
            else:
                raise ValueError(f"Error retrieving API data: {response.status_code}")
        else:
            log_and_show_error("Error", "Invalid country selection. See the logs.")
            return
        update_dropdowns()
        display_data()
    except Exception as e:
        log_and_show_error("Error loading file", str(e))

# Update dropdown menus
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
        log_and_show_error("Error updating dropdown menus", str(e),"Check the logs.")

# Update pie chart
def update_pie_chart():
    try:
        selected_year = year_var.get()
        if not selected_year:
            messagebox.showinfo("Error", "Please select a year.")
            return

        selected_row = df[df["Jahr"] == int(selected_year)]
        if selected_row.empty:
            log_and_show_error("Error", "No data available for the selected year. Chekc the logs.")
            return
        # all columns except "Year"
        energy_data = selected_row.iloc[0, 1:]  
        ax.clear()

        if energy_data.sum() == 0:
            wedges, texts = ax.pie([1], colors=["lightgrey"])
            ax.text(0, 0, "No values\navailable", ha='center', va='center', fontsize=16, color="red")
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
        log_and_show_error("Error updating pie chart", str(e), "Check the logs")

# Function to sort the table
def sort_table(column, reverse):
    try:
        if column == "Jahr" or column in df.columns[1:]:
            sorted_df = df.sort_values(by=column, ascending=not reverse)
            update_table(sorted_df)
            table.heading(column, command=lambda: sort_table(column, not reverse))
    except Exception as e:
        log_and_show_error("Error sorting table", str(e), "Check the logs")

# Function to update the table
def update_table(dataframe):
    try:
        table.delete(*table.get_children())
        for i, (_, row) in enumerate(dataframe.iterrows()):
            values = [row["Jahr"]] + list(row[1:])
            tag = "even" if i % 2 == 0 else "odd"
            table.insert("", "end", values=values, tags=(tag,))
    except Exception as e:
        log_and_show_error("Error updating table", str(e), "Check the logs")

# Updated function to display the data
def display_data():
    selected_country = country_var.get()
    if not selected_country:
        log_and_show_error("Error", "Please select a country. Check the logs.")
        return
    try:
        table.delete(*table.get_children())
        table["columns"] = ["Jahr"] + list(df.columns[1:])
        table.heading("#0", text="", anchor="center")
        table.column("#0", width=0, stretch=tk.NO)
        # sort fumktion for each column
        for col in table["columns"]:
            table.heading(col, text=col, anchor="center", command=lambda c=col: sort_table(c, False))
            table.column(col, anchor="center", width=170)

        # Paint table line white and grey alternatively
        for i, (_, row) in enumerate(df.iterrows()):
            values = [row["Jahr"]] + list(row[1:])
            tag = "even" if i % 2 == 0 else "odd"
            table.insert("", "end", values=values, tags=(tag,))

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
        log_and_show_error("Error displaying data", str(e), "Check the logs")

# Start application
country_dropdown['values'] = ["Deutschland", "Frankreich", "Großbritannien", "Polen"]
country_dropdown.bind("<<ComboboxSelected>>", lambda e: load_csv_or_json_or_db_or_api())
country_dropdown.current(0)
load_csv_or_json_or_db_or_api()
root.mainloop()

