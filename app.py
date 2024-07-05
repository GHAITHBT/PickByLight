from flask import Flask, render_template, request, flash
from pyrfc import Connection
import pandas as pd
import logging
import traceback
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    return render_template('index.html')

def connect_to_sap(conn_params):
    try:
        conn = Connection(**conn_params)
        logging.info("Connected to SAP")
        return conn
    except Exception as e:
        logging.error(f"Error connecting to SAP: {e}")
        flash(f"Error connecting to SAP: {e}", 'error')
        return None

def read_bom_data(conn, material, plant, bom_usage):
    try:
        logging.info(f"Reading BOM data for Material: {material}, Plant: {plant}, BOM Usage: {bom_usage}")
        
        # Convert string date to SAP date format
        datuv = datetime.strptime('2024.07.02', '%Y.%m.%d').date()
        
        # Log parameter values for debugging
        logging.debug(f"Parameters - MTNRV: {material}, WERKS: {plant}, STLAN: {bom_usage}, DATUV: {datuv}")
        
        # Call the SAP function module with corrected parameters
        bom_data = conn.call("CS_BOM_EXPL_MAT_V2_RFC", 
                             DATUV=datuv,
                             MTNRV=material,
                             WERKS=plant.upper(),  # Convert plant to uppercase
                             STLAN=bom_usage,
                             CAPID="",
                             AUMNG="0",
                            
                             EMENG="0",
                             MKTLS="x",
                             STPST="0",
                             SVWVO="x",
                             VRSVO="x",
                             STLAL="1")
        logging.info("BOM data retrieved")
        return bom_data
    except Exception as e:
        logging.error(f"Error retrieving BOM data: {e}")
        logging.error(traceback.format_exc())
        flash(f"Error retrieving BOM data: {e}", 'error')
        return None

def process_bom_data(bom_data):
    try:
        items = bom_data.get("STB", [])
        bom_list = []
        for item in items:
            component = {
                "Material": item.get("IDNRK", ""),
                "Description":item.get("OJTXP",""),
                "Quantity": item.get("MNGLG", ""),
              
                # Add more fields as needed
            }
            bom_list.append(component)
        return bom_list
    except Exception as e:
        logging.error(f"Error processing BOM data: {e}")
        logging.error(traceback.format_exc())
        flash(f"Error processing BOM data: {e}", 'error')
        return []

@app.route('/retrieve_bom', methods=['POST'])
def retrieve_bom():
    # Static SAP connection parameters
    conn_params = {
        "user": "touatigb",
        "passwd": "NEver@winfcd100",
        "ashost": "137.121.21.13",
        "sysnr": "13",
        "client": "100",
        "lang": "en",
    }

    material_full = request.form.get('material')
    material = material_full.lstrip('0')  # Remove leading zeros

    plant = request.form.get('plant')
    bom_usage = request.form.get('bomUsage')

    conn = connect_to_sap(conn_params)
    if conn:
        bom_data = read_bom_data(conn, material, plant, bom_usage)
        if bom_data:
            bom_list = process_bom_data(bom_data)
            if bom_list:
                return render_template('bom.html', bom_list=bom_list)
            else:
                flash("No BOM data found.", 'error')
        else:
            flash("Failed to retrieve BOM data.", 'error')
    else:
        flash("Failed to connect to SAP.", 'error')
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
