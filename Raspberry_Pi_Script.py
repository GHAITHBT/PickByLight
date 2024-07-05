import RPi.GPIO as GPIO
import time
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# GPIO setup
button_pins = [17, 27, 22, 5, 6, 13]  # Define your button GPIO pins
led_pins = [18, 23, 24, 12, 16, 20]   # Define your LED GPIO pins
materials = ["MAT1", "MAT2", "MAT3", "MAT4", "MAT5", "MAT6"]  # Define your materials

GPIO.setmode(GPIO.BCM)
for pin in button_pins:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
for pin in led_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

current_bom_materials = []

def update_bom(materials):
    global current_bom_materials
    current_bom_materials = materials
    print("Updated BOM materials:", current_bom_materials)

@app.route('/update_bom', methods=['POST'])
def update_bom_endpoint():
    data = request.get_json()
    materials = data.get('materials', [])
    update_bom(materials)
    return jsonify({'status': 'success'})

def check_materials():
    for i, material in enumerate(materials):
        if material in current_bom_materials:
            GPIO.output(led_pins[i], GPIO.HIGH)
        else:
            GPIO.output(led_pins[i], GPIO.LOW)

try:
    while True:
        check_materials()
        for i, pin in enumerate(button_pins):
            if GPIO.input(pin) == GPIO.LOW:
                print(f"Button {i+1} pressed, material: {materials[i]}")
                time.sleep(0.3)
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
