import tkinter as tk
from tkinter import messagebox, scrolledtext
from pyrfc import Connection

# SAP connection parameters defined in code
SAP_CONN_PARAMS = {
    "user": "touatigb",
        "passwd": "NEver@winfcd100",
        "ashost": "137.121.21.13",
        "sysnr": "13",
        "client": "100",
        "lang": "en",
}

# Function to connect to SAP and read table data
def read_table_from_sap(prod_input):
    try:
        # Connect to SAP
        conn = Connection(**SAP_CONN_PARAMS)

        

        # Read table data using RFC_READ_TABLE
        result = conn.call('RFC_READ_TABLE',
                           QUERY_TABLE="JITHD",
                           FIELDS=[{'FIELDNAME': "JINUM"},  {'FIELDNAME': 'PRODN'}])

        # Retrieve and display data
        data = [row['WA'] for row in result['DATA']]
        return data

    except Exception as e:
        messagebox.showerror("Error", f"Failed to retrieve data: {e}")
        return None

# Function to handle the GUI button click
def on_submit():
    prod_input = entry.get()
    if not prod_input:
        messagebox.showwarning("Input Error", "Please enter a PRODN value.")
        return

    data = read_table_from_sap(prod_input)
    if data:
        result_text.config(state=tk.NORMAL)
        result_text.delete('1.0', tk.END)
        for row in data:
            result_text.insert(tk.END, row + "\n")
        result_text.config(state=tk.DISABLED)

# Create the GUI application
app = tk.Tk()
app.title("SAP Table Reader")

# Input Label and Entry
label = tk.Label(app, text="Enter PRODN:")
label.pack(pady=5)
entry = tk.Entry(app)
entry.pack(pady=5)

# Submit Button
submit_button = tk.Button(app, text="Submit", command=on_submit)
submit_button.pack(pady=5)

# Result Display
result_text = scrolledtext.ScrolledText(app, width=50, height=15, state=tk.DISABLED)
result_text.pack(pady=10)

# Start the GUI event loop
app.mainloop()
