from flask import Flask, render_template, request, jsonify
from pyrfc import Connection
from mysql.connector import pooling, Error as MySQLError
from datetime import datetime
import threading
import logging
import traceback
import time
import redis

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure key

# SAP and MySQL connection parameters
SAP_CONN_PARAMS = {
      "user": "MIGRATION",
    "passwd": "migSEBN99#",
    "ashost": "137.121.21.6",
    "sysnr": "06",
    "client": "100",
    "lang": "en",
}

MYSQL_CONN_PARAMS = {
    "host": "localhost",
    "user": "root",
    "password": "Passw0rd123",
    "database": "PickByLight",
    "pool_name": "mysql_pool",
    "pool_size": 10
}

# MySQL connection pool
mysql_pool = pooling.MySQLConnectionPool(**MYSQL_CONN_PARAMS)

# Redis connection
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# Function to identify the SAP system
def identify_sap_system():
    if SAP_CONN_PARAMS["ashost"].endswith("15"):
        system = "FCK"
    elif SAP_CONN_PARAMS["ashost"].endswith("13"):
        system = "FCD"
    elif SAP_CONN_PARAMS["ashost"].endswith("6"):
        system = "FCP"
    else:
        system = "Unknown"
    
    client = SAP_CONN_PARAMS["client"]
    return f"{system} {client}"

# Function to connect to MySQL and fetch JINUM for a given PRODN
def fetch_jinum_from_mysql(prodn):
    try:
        # Check cache first
        cached_jinum = redis_client.get(prodn)
        if cached_jinum:
            return cached_jinum.decode('utf-8')
        
        conn_mysql = mysql_pool.get_connection()
        cursor = conn_mysql.cursor()

        sql = "SELECT JINUM FROM Jithead WHERE PRODN = %s"
        cursor.execute(sql, (prodn,))
        result = cursor.fetchone()
        cursor.fetchall()  # Clear any unread results

        cursor.close()
        conn_mysql.close()

        if result:
            jinum = result[0]
            # Cache the result
            redis_client.set(prodn, jinum)
            return jinum
        else:
            return None

    except MySQLError as err:
        logging.error(f"Failed to fetch JINUM from MySQL: {err}")
        return None

# Function to call BAPI_JITCALLIN_GETDETAILS in SAP and fetch jitcalcomponents
def call_bapi_get_details(jinum):
    try:
        conn_sap = Connection(**SAP_CONN_PARAMS)

        jitcalls = [{'JITCALLNUMBER': jinum}]

        result = conn_sap.call('BAPI_JITCALLIN_GETDETAILS', JITCALLS=jitcalls)

        conn_sap.close()

        jitcalcomponents = result['JITCALLCOMPONENTS']

        return jitcalcomponents

    except Exception as e:
        logging.error(f"Failed to call BAPI_JITCALLIN_GETDETAILS: {e}")
        return None

# Function to fetch BOM data from SAP and process it
def fetch_bom_data(material):
    try:
        conn_sap = Connection(**SAP_CONN_PARAMS)
        datuv = datetime.strptime('2024.07.02', '%Y.%m.%d').date()
        # Set default values for WERKS and STLAN
        werks = "TN10"
        stlan = "3"

        # Call the SAP function module to retrieve BOM data
        bom_data = conn_sap.call("CS_BOM_EXPL_MAT_V2_RFC", 
                             DATUV=datuv,
                             MTNRV=material,
                             WERKS=werks,  # Convert plant to uppercase
                             STLAN=stlan,
                             CAPID="",
                             AUMNG="0",
                             EMENG="0",
                             MKTLS="x",
                             STPST="0",
                             SVWVO="x",
                             VRSVO="x",
                             STLAL="1")

        conn_sap.close()

        # Process bom_data using the provided method
        processed_bom_data = process_bom_data(bom_data)

        # Filter and recursively fetch BOM data for materials starting with "B"
        last_bom_data = None
        for item in processed_bom_data:
            if item["Material"].startswith("B"):
                last_bom_data = fetch_bom_data(item["Material"])

        return last_bom_data if last_bom_data else processed_bom_data

    except Exception as e:
        logging.error(f"Failed to fetch BOM data for Material {material}: {e}")
        logging.error(traceback.format_exc())
        return None

def process_bom_data(bom_data):
    try:
        items = bom_data.get("STB", [])
        bom_list = []
        for item in items:
            material = item.get("IDNRK", "").lstrip('0')  # Strip leading zeros
            component = {
                "Material": material,
                "Description": item.get("OJTXP", ""),
                "Quantity": item.get("MNGLG", ""),
                # Add more fields as needed
            }
            bom_list.append(component)
        return bom_list
    except Exception as e:
        logging.error(f"Error processing BOM data: {e}")
        logging.error(traceback.format_exc())
        return []

# Helper function to fetch BOM data concurrently
def fetch_bom_data_concurrently(material, results, index):
    bom_data = fetch_bom_data(material)
    results[index] = bom_data

# Flask routes
@app.route('/')
def index():
    sap_system = identify_sap_system()
    return render_template('index1.html', sap_system=sap_system)

@app.route('/fetch_jit_components', methods=['POST'])
def fetch_jit_components():
    start_time = time.time()  # Start the timer

    prodn = request.form['prodn'].strip()
    if not prodn:
        return jsonify({'error': 'Please enter a PRODN value.'}), 400

    jinum = fetch_jinum_from_mysql(prodn)
    if not jinum:
        return jsonify({'error': f'Could not find JINUM for PRODN: {prodn}'}), 404

    jitcalcomponents = call_bapi_get_details(jinum)
    if not jitcalcomponents:
        return jsonify({'error': f'No JIT Call Components found for JINUM: {jinum}'}), 404

    # Fetch BOM data for each material in jitcalcomponents concurrently
    threads = []
    results = [None] * len(jitcalcomponents)
    for i, component in enumerate(jitcalcomponents):
        material = component['MATERIAL']  # Assuming 'MATERIAL' is the key for material number
        thread = threading.Thread(target=fetch_bom_data_concurrently, args=(material, results, i))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Prepare the response
    response = []
    for i, component in enumerate(jitcalcomponents):
        response.append({'component': component, 'bom_data': results[i]})

    execution_time = time.time() - start_time  # Calculate the execution time
    return jsonify({'results': response, 'execution_time': execution_time}), 200

@app.route('/fetch_jit_components_api', methods=['GET'])
def fetch_jit_components_api():
    start_time = time.time()  # Define start_time here

    prodn = request.args.get('PRODN', '').strip()
    if not prodn:
        return jsonify({'error': 'Please provide a PRODN parameter.'}), 400

    jinum = fetch_jinum_from_mysql(prodn)
    if not jinum:
        return jsonify({'error': f'Could not find JINUM for PRODN: {prodn}'}), 404

    jitcalcomponents = call_bapi_get_details(jinum)
    if not jitcalcomponents:
        return jsonify({'error': f'No JIT Call Components found for JINUM: {jinum}'}), 404

    # Fetch BOM data for each material in jitcalcomponents concurrently
    threads = []
    results = [None] * len(jitcalcomponents)
    for i, component in enumerate(jitcalcomponents):
        material = component['MATERIAL']  # Assuming 'MATERIAL' is the key for material number
        thread = threading.Thread(target=fetch_bom_data_concurrently, args=(material, results, i))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Prepare the response with CUST_MAT and its BOM data
    response = []
    for i, component in enumerate(jitcalcomponents):
        cust_mat = component.get('CUST_MAT', '')
        bom_data = results[i] if results[i] else []
        response.append({'CUST_MAT': cust_mat, 'BOM': bom_data})

    execution_time = time.time() - start_time  # Calculate the execution time
    return jsonify({'results': response, 'execution_time': execution_time}), 200


if __name__ == '__main__':
    app.run(debug=True)
# http://localhost:5000/fetch_jit_components_api?PRODN=240825036001