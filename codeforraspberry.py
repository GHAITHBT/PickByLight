import RPi.GPIO as GPIO
import time

# Define GPIO pins for buttons and LEDs (adjust pin numbers as per your setup)
GPIO.setmode(GPIO.BCM)

materials = {
    'Material1': {'pin': 17, 'matched': False},
    'Material2': {'pin': 18, 'matched': False},
    'Material3': {'pin': 22, 'matched': False},
    'Material4': {'pin': 23, 'matched': False},
    'Material5': {'pin': 24, 'matched': False},
    'Material6': {'pin': 25, 'matched': False},
}

# Setup GPIO pins for buttons and LEDs
for material, config in materials.items():
    GPIO.setup(config['pin'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Function to light up the LED for matched materials
def light_up(material):
    pin = materials[material]['pin']
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)

try:
    while True:
        # Replace this logic with your SAP integration and material comparison
        # For demonstration purposes, we simulate a match with Material3
        simulated_bom_data = ['Material1', 'Material2', 'Material3', 'Material4', 'Material5', 'Material6']

        for material in materials:
            if material in simulated_bom_data:
                materials[material]['matched'] = True
                light_up(material)

        # Wait for user confirmation by pressing the button
        for material, config in materials.items():
            if config['matched']:
                while GPIO.input(config['pin']) == GPIO.LOW:
                    time.sleep(0.1)

        # Reset LEDs after confirmation
        for material in materials:
            if materials[material]['matched']:
                GPIO.output(materials[material]['pin'], GPIO.LOW)
                materials[material]['matched'] = False

except KeyboardInterrupt:
    GPIO.cleanup()
