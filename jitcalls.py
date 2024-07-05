import tkinter as tk
from tkinter import messagebox, scrolledtext
from pyrfc import Connection
import mysql.connector

# SAP connection parameters defined in code
SAP_CONN_PARAMS = {
    "user": "touatigb",
    "passwd": "NEver@winfcd100",
    "ashost": "137.121.21.13",
    "sysnr": "13",
    "client": "100",
    "lang": "en",
}

# MySQL connection parameters defined in code
MYSQL_CONN_PARAMS = {
    "host": "localhost",
    "user": "root",
    "password": "Passw0rd123",
    "database": "PickByLight"
}

# Function to connect to MySQL and fetch JINUM for a given PRODN
def fetch_jinum_from_mysql(prodn):
    try:
        # Connect to MySQL
        conn_mysql = mysql.connector.connect(**MYSQL_CONN_PARAMS)
        cursor = conn_mysql.cursor()

        # Query to fetch JINUM for the given PRODN
        sql = "SELECT JINUM FROM Jithead WHERE PRODN = %s"
        cursor.execute(sql, (prodn,))
        result = cursor.fetchone()

        # Disconnect from MySQL
        cursor.close()
        conn_mysql.close()

        if result:
            return result[0]  # Return JINUM if found
        else:
            return None

    except mysql.connector.Error as err:
        print(f"Failed to fetch JINUM from MySQL: {err}")
        return None

# Function to call BAPI_JITCALLIN_GETDETAILS in SAP and fetch jitcalcomponents
def call_bapi_get_details(jinum):
    try:
        # Connect to SAP
        conn_sap = Connection(**SAP_CONN_PARAMS)

        # Prepare JITCALLS parameter
        jitcalls = [{'JITCALLNUMBER': jinum}]

        # Call BAPI_JITCALLIN_GETDETAILS
        result = conn_sap.call('BAPI_JITCALLIN_GETDETAILS',
                               JITCALLS=jitcalls)

        # Disconnect from SAP
        conn_sap.close()

        # Extract jitcalcomponents from the result
        jitcalcomponents = result['JITCALLCOMPONENTS']

        return jitcalcomponents

    except Exception as e:
        print(f"Failed to call BAPI_JITCALLIN_GETDETAILS: {e}")
        return None

# Function to handle fetching JIT Call Components and displaying in GUI
def fetch_jit_components():
    prodn = entry_prodn.get().strip()
    if not prodn:
        messagebox.showwarning("Input Error", "Please enter a PRODN value.")
        return

    # Fetch JINUM from MySQL for the given PRODN
    jinum = fetch_jinum_from_mysql(prodn)
    if not jinum:
        messagebox.showerror("Error", f"Could not find JINUM for PRODN: {prodn}")
        return

    # Call BAPI_JITCALLIN_GETDETAILS in SAP using the retrieved JINUM
    jitcalcomponents = call_bapi_get_details(jinum)
    if jitcalcomponents:
        # Display JIT Call Components in the scrolled text widget
        result_text.config(state=tk.NORMAL)
        result_text.delete('1.0', tk.END)
        result_text.insert(tk.END, f"JIT Call Components for JINUM {jinum}:\n")
        for component in jitcalcomponents:
            result_text.insert(tk.END, f"{component}\n")
        result_text.config(state=tk.DISABLED)
    else:
        messagebox.showerror("Error", f"No JIT Call Components found for JINUM {jinum}")

# GUI setup
app = tk.Tk()
app.title("SAP JIT Call Components Fetcher")

# Input Label and Entry for PRODN
label_prodn = tk.Label(app, text="Enter PRODN:")
label_prodn.pack(pady=5)
entry_prodn = tk.Entry(app)
entry_prodn.pack(pady=5)

# Fetch Button
fetch_button = tk.Button(app, text="Fetch JIT Call Components", command=fetch_jit_components)
fetch_button.pack(pady=10)

# Result Display using ScrolledText
result_text = scrolledtext.ScrolledText(app, width=50, height=15, state=tk.DISABLED)
result_text.pack(pady=10)

# Start the GUI event loop
app.mainloop()
