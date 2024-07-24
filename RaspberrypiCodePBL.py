import RPi.GPIO as GPIO
import time
import requests

# Define GPIO pin mappings
material_gpio_mapping = {
    'Material1': {'led': 17, 'button': 5},
    'Material2': {'led': 18, 'button': 6},
    'Material3': {'led': 27, 'button': 13},
    'Material4': {'led': 22, 'button': 19},
    'Material5': {'led': 23, 'button': 26},
    'Material6': {'led': 24, 'button': 21},
    'Material7': {'led': 25, 'button': 20},
    'Material8': {'led': 12, 'button': 16},
}

# Set up GPIO mode
GPIO.setmode(GPIO.BCM)

# Initialize LEDs and buttons based on mapping
for material, pins in material_gpio_mapping.items():
    GPIO.setup(pins['led'], GPIO.OUT)
    GPIO.output(pins['led'], GPIO.LOW)
    GPIO.setup(pins['button'], GPIO.IN, pull_up_down=GPIO.PUD_UP)

def fetch_json_data(prodn):
    try:
        url = f'http://localhost:5000/fetch_jit_components_api?PRODN={prodn}'
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch JSON data: {e}")
        return None

def control_led_for_material(material, state):
    if material in material_gpio_mapping:
        led_pin = material_gpio_mapping[material]['led']
        GPIO.output(led_pin, GPIO.HIGH if state else GPIO.LOW)

def wait_for_button_press(material):
    if material in material_gpio_mapping:
        button_pin = material_gpio_mapping[material]['button']
        while GPIO.input(button_pin) == GPIO.HIGH:
            # Wait for button press
            pass
        return True
    return False

def process_materials(json_data):
    if not json_data:
        return

    for material in material_gpio_mapping.keys():
        # Check if material is in the fetched data
        if any(component['CUST_MAT'] == material for component in json_data['results']):
            control_led_for_material(material, True)
            if wait_for_button_press(material):
                control_led_for_material(material, False)
        else:
            control_led_for_material(material, False)

if __name__ == '__main__':
    try:
        while True:
            scanned_prodn = input("Scan a product number: ").strip()
            data = fetch_json_data(scanned_prodn)
            process_materials(data)
            time.sleep(1)  # Adjust delay as needed

    except KeyboardInterrupt:
        print("Exiting program.")
    finally:
        GPIO.cleanup()
        print("Cleanup complete.")
