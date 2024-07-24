import tkinter as tk
from tkinter import messagebox
import requests

# Define the material-to-GUI mapping
material_gpio_mapping = {
    '3BG1069381013': {'led': 1, 'button': 1},
    'Material2': {'led': 2, 'button': 2},
    '920003924': {'led': 3, 'button': 3},
    'Material4': {'led': 4, 'button': 4},
    '3BG1012081000': {'led': 5, 'button': 5},
    'Material6': {'led': 6, 'button': 6},
    '3BG0212081089': {'led': 7, 'button': 7},
    'Material8': {'led': 8, 'button': 8},
}

# Create the main window
root = tk.Tk()
root.title("GPIO Simulator")

# Create dictionaries to hold references to UI components
led_labels = {}
button_buttons = {}

# Function to toggle LED
def control_led_for_material(material, state):
    if material in material_gpio_mapping:
        led = material_gpio_mapping[material]['led']
        led_labels[led].config(bg="green" if state else "gray")

# Function to simulate button press
def wait_for_button_press(material):
    if material in material_gpio_mapping:
        button = material_gpio_mapping[material]['button']
        # Simulate waiting for button press
        result = messagebox.askokcancel("Button Press", f"Press the button for {material}")
        return result
    return False

# Function to fetch JSON data
def fetch_json_data(prodn):
    try:
        url = f'http://localhost:5000/fetch_jit_components_api?PRODN={prodn}'
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch JSON data: {e}")
        return None

# Function to process materials and control LEDs
def process_materials(json_data):
    if not json_data:
        return
    
    for material in material_gpio_mapping.keys():
        # Check if the material is in the JSON results
        if any(component['CUST_MAT'] == material for component in json_data['results']):
            control_led_for_material(material, True)
            if wait_for_button_press(material):
                control_led_for_material(material, False)
        else:
            control_led_for_material(material, False)

# Setup GUI components
for material, pins in material_gpio_mapping.items():
    led_label = tk.Label(root, text=f"LED {pins['led']}", bg="gray", width=20, height=2)
    led_label.grid(row=pins['led'], column=0, padx=10, pady=5)
    led_labels[pins['led']] = led_label

    button_button = tk.Button(root, text=f"Button {pins['button']}", width=20, height=2, command=lambda m=material: wait_for_button_press(m))
    button_button.grid(row=pins['button'], column=1, padx=10, pady=5)
    button_buttons[pins['button']] = button_button

# Function to start the simulation
def start_simulation():
    scanned_prodn = prodn_entry.get().strip()
    if not scanned_prodn:
        messagebox.showerror("Error", "Please enter a PRODN value.")
        return
    
    data = fetch_json_data(scanned_prodn)
    process_materials(data)

# Add input field and button to start the simulation
tk.Label(root, text="Enter PRODN:").grid(row=0, column=0, padx=10, pady=5)
prodn_entry = tk.Entry(root)
prodn_entry.grid(row=0, column=1, padx=10, pady=5)
tk.Button(root, text="Start Simulation", command=start_simulation).grid(row=1, column=0, columnspan=2, padx=10, pady=5)

# Run the main loop
root.mainloop()
