#######################################################################
# Author: Benedikt Krings                                             #
# GitHub Repo: https://github.com/Benedikt1905/energiedaten-app       #
# GitHub Branch: main                                                 #
# Version: 2025061003                                                 #
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

#---------Global variables---------
base_path = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(base_path, "img/dbay-icon.png")
icon_path = os.path.join(base_path, "img/dbay-icon.ico")
file_path_de = r'data/Primärverbrauch DE.csv'
file_path_fr = r'data/Primärverbrauch mehr Daten und Fehler.json'
file_path_gb = r'data/Primärverbrauch GB (mit Fehlern).db'
api_url = "http://localhost:8000/api/1/primary_energy_consumption"

#------------Logging-----------
def log_message(level, message):
    log_dir = os.path.join(base_path, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_path = os.path.join(log_dir, "energiedaten-app.log")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{now}] {level}: {message}\n")

# show error, warning or info message in a messagebox graphicaly
def show_error(title, message):
    messagebox.showerror(title, message)

def show_warning(title, message):
    messagebox.showwarning(title, message)

def show_info(title, message):
    messagebox.showinfo(title, message)    

# only logs the info, error or warning message and does not show it in a messagebox in the GUI 
def log_info(message):
    log_message("[INFO]", f"{message}")   

def log_warning(message):
    log_message("[WARNING]", f"{message}")

def log_error(message):
    log_message("[ERROR]", f"{message}")        

# log startup message in the log file
log_info ("energiedaten-app started successfully.")

def log_entry_on_close():
    log_message("[INFO]", "energiedaten-app shut down successfully.")
    root.destroy()

#--------------GUI--------------
root = tk.Tk()
root.title("Primärenergieverbrauch v2.6")
root.config(bg="white")

#-----------Icon and logo images-----------
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)
else:
    log_warning(f"Icon image not found in'{icon_path}'. Default icon in use. Please check if the path and image exists.")
    show_warning("Warning", "Default icon in use.")

# logo image in GUI
if os.path.exists(logo_path):
    logo_image = tk.PhotoImage(file=logo_path)
else:
    log_warning(f"Logo image'{logo_path}' not found. No logo image will be used.")
    show_warning("Warning","Logo image not found. No logo image in use.")
    logo_image = None

# display logo image in top frame
if logo_image:
    logo_label = tk.Label(root, image=logo_image, bg="white")
    logo_label.place(relx=0.20, rely=-0.04)

# global variables
df = pd.DataFrame()
country_var = tk.StringVar()
energy_var = tk.StringVar()
year_var = tk.StringVar()

#--------------Dropdown menus--------------
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

#----------------Malware check for CSV file---------------
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
                    log_warning(f"Suspicious Unicode control characters found in line {line_num} of '{file_path}'.")
                    show_warning(
                        "Critical Security Warning!",
                        f"The CSV file contains suspicious Unicode control characters (e.g. RTL/LTR-Override).\n"
                        f"Import will be aborted. Check the logs."
                    )
                    return False
                for pattern in suspicious_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        log_warning(f"Suspicious pattern '{pattern}' found in line {line_num} of '{file_path}'.")
                        show_warning(
                            "Critical Security Warning!",
                            f"The CSV file contains potentially malicious or dangerous code.\n"
                            f"Import will be aborted.\nDetected pattern: {pattern} Check the logs."
                        )
                        return False
        return True
    except Exception as e:
        log_error(f"Critical error during security check of '{file_path}': {str(e)}")
        show_error("An error occurred during the security check! Please try again. Check the logs", str(e) )
        return False
    
#--------------Loading Data from CSV, JSON, DB and API-------------
def load_csv_or_json_or_db_or_api():
    global df
    try:
        selected_country = country_var.get()
        if selected_country == "Deutschland":
            # security check before reading!
            if not check_csv_for_malicious_code(file_path_de):
                return
            # automatically detect encoding
            with open(file_path_de, 'rb') as f:
                rawdata = f.read(4096)
                result = chardet.detect(rawdata)
                detected_encoding = result['encoding'] if result['encoding'] else 'utf-8'
            try:
                raw_df = pd.read_csv(file_path_de, sep=';', encoding=detected_encoding, skip_blank_lines=True)
                # remove empty rows 
                raw_df = raw_df.dropna(how='all')
            except UnicodeDecodeError:
                log_error(f"The file '{file_path_de}' could not be read with the detected encoding '{detected_encoding}'.")
                show_error("Error", "The file could not be read with the detected encoding. Check the logs for more details.")
                return
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
            query = "SELECT * FROM energieverbrauch"
            df = pd.read_sql_query(query, conn)
            conn.close()
            df.rename(columns={df.columns[0]: "Jahr"}, inplace=True)
            df["Jahr"] = pd.to_numeric(df["Jahr"], errors='coerce').fillna(0).astype(int)
             # round all colums to integers
            for col in df.columns:
                if col != "Jahr":
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            # check if years are sorted and if not round them
            years = df["Jahr"].tolist()
            years_sorted = sorted(years)
            if years != years_sorted:
                log_warning("The years have not been sorted in ascending order. The data will be used anyway and the years will be showed correctly anyways.")
                show_warning(
                    "Warnung: Jahre nicht sortiert",
                    "Die Jahre in der CSV-Datei sind nicht aufsteigend sortiert. Die Daten werden trotzdem verwendet und die Jahre werden automatisch sortiert."
                )
                df = df.sort_values(by="Jahr").reset_index(drop=True)
                years = df["Jahr"].tolist()
            # check for duplicate years
            if len(years) != len(set(years)):
                log_warning("The CSV file contains duplicate years. The data will be used anyway, but duplicate years can lead to incorrect evaluations.")
                show_warning(
                    "Warnung: Doppelte Jahre",
                    "Die CSV-Datei enthält doppelte Jahre. Die Daten werden trotzdem verwendet, aber doppelte Jahre können zu fehlerhaften Auswertungen führen."
                )
        elif selected_country == "Polen":
            log_info(f"Connecting to the API to retrieve data for {selected_country}........")
            response = requests.get(api_url)
            if response.status_code == 200:
                log_info(f"Response Code: {response.status_code} Successfully connected to the API {api_url}")
                raw_data = response.json()
                # the actual data is in the "data" key and is a dict: {year: {energy_source: value, ...}, ...}
                api_data = raw_data.get("data", {})
                if not api_data:
                    raise ValueError("The API did not return any data.")
                # convert to DataFrame: year as column
                df_api = pd.DataFrame.from_dict(api_data, orient="index")
                df_api.index.name = "Jahr"
                df_api.reset_index(inplace=True)
                # convert year to int
                df_api["Jahr"] = pd.to_numeric(df_api["Jahr"], errors='coerce').fillna(0).astype(int)
                for col in df_api.columns[1:]:
                    df_api[col] = pd.to_numeric(df_api[col], errors='coerce').fillna(0)
                df = df_api
            else:
                raise ValueError(f"Error retrieving API data: {response.status_code}")
        else:
            log_error(f"Invalid country selection: {selected_country}")
            show_error("Error", "Invalid country selection.")
            return
        update_dropdowns()
        display_data()
    except Exception as e:
        log_error(f"Error loading data for {selected_country}: {str(e)}")
        show_error("Error loading file", str(e))

#--------------Update dropdown menu----------------
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
        log_error(f"Error updating dropdown menus: {str(e)}, data can't be updated.")
        show_error("Error updating dropdown menus", str(e),"Check the logs.")

#---------------Pie chart-----------------
fig, ax = plt.subplots(figsize=(5, 4))
canvas = FigureCanvasTkAgg(fig, master=middle_frame)
canvas.get_tk_widget().grid(row=0, column=2, rowspan=3, padx=20, pady=10)

# label for "Keine Werte verfügbar"
no_data_label = tk.Label(middle_frame, text="Keine Werte verfügbar", font=("Arial", 16), fg="red", bg="white")
no_data_label.grid(row=3, column=2, pady=10)
no_data_label.grid_remove()

# update values in pie chart
def update_pie_chart():
    try:
        selected_year = year_var.get()
        selected_row = df[df["Jahr"] == int(selected_year)]
        if selected_row.empty:
            log_error(f"No data available for the selected year: {selected_year}")
            show_error("Error", "No data available for the selected year.")
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
        log_error(f"Error updating pie chart: {str(e)}, access denied. No data available for the selected year.")   
        show_error("Error updating pie chart", str(e), "Check the logs")

#------------------Table------------------
table_frame = tk.Frame(root, bg="white", bd=1, relief="solid")
table_frame.pack(padx=10, pady=10)
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

# scrollbar for the table
scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
scrollbar.pack(side="right", fill="y")
table.configure(yscrollcommand=scrollbar.set)

# sort table by column
def sort_table(column, reverse):
    try:
        if column == "Jahr" or column in df.columns[1:]:
            sorted_df = df.sort_values(by=column, ascending=not reverse)
            update_table(sorted_df)
            table.heading(column, command=lambda: sort_table(column, not reverse))
    except Exception as e:
        log_error(f"Error sorting table by {column}: {str(e)}")
        show_error("Error sorting table", str(e), "Check the logs")

# update table
def update_table(dataframe):
    try:
        table.delete(*table.get_children())
        for i, (_, row) in enumerate(dataframe.iterrows()):
            values = [row["Jahr"]] + list(row[1:])
            tag = "even" if i % 2 == 0 else "odd"
            table.insert("", "end", values=values, tags=(tag,))
    except Exception as e:
        log_error(f"Error updating table: {str(e)} access denied" )
        show_error("Error updating table", str(e), "Check the logs")

#--------------Display data in table and calculate statistics--------------
def display_data():
    selected_country = country_var.get()
    if not selected_country:
        log_error("Display data: no country selected. Please select a country.")
        show_error("Error", "Please select a country. Check the logs.")
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

        # paint table line white and grey alternatively
        for i, (_, row) in enumerate(df.iterrows()):
            values = [row["Jahr"]] + list(row[1:])
            tag = "even" if i % 2 == 0 else "odd"
            table.insert("", "end", values=values, tags=(tag,))

        table.tag_configure("even", background="white")
        table.tag_configure("odd", background="lightgrey")
        #--------calculate average, max and min values----------
        selected_energy = energy_var.get()
        if selected_energy and selected_energy in df.columns:
            max_value = df[selected_energy].max()
            mean_value = df[selected_energy].mean()
            min_value = df[selected_energy].min()
            stat_labels["Maximaler Jahresverbrauch"].config(text=f"{max_value:.2f} PJ")
            stat_labels["Durchschn. Jahresverbrauch"].config(text=f"{mean_value:.2f} PJ")
            stat_labels["Minimaler Jahresverbrauch"].config(text=f"{min_value:.2f} PJ")

        # update pie chart based on selected year
        update_pie_chart()
    except Exception as e:
        log_error(f"Error displaying data for {selected_country}: {str(e)}. Data can't be displayed by the function.")
        show_error("Error displaying data", str(e), "Check the logs")

# update dropdowns and load initial data
country_dropdown['values'] = ["Deutschland", "Frankreich", "Großbritannien", "Polen", "Afrika"]
country_dropdown.bind("<<ComboboxSelected>>", lambda e: load_csv_or_json_or_db_or_api())
country_dropdown.current(0)
load_csv_or_json_or_db_or_api()
# log entry when the application is closed
root.protocol("WM_DELETE_WINDOW", log_entry_on_close)
#--------------Main loop--------------
root.mainloop()
