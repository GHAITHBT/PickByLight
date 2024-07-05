from flask import Flask, render_template, request, jsonify
from pyrfc import Connection
from mysql.connector import pooling, Error as MySQLError
from datetime import datetime
import concurrent.futures
import logging
import traceback
import time
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure key

# SAP and MySQL connection parameters
SAP_CONN_PARAMS = {
    "user": "touatigb",
    "passwd": "NEver@winfcd100",
    "ashost": "137.121.21.13",
    "sysnr": "13",
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

RPI_ADDRESS = "http://<raspberry_pi_ip>:<port>/update_bom"  # Replace with your Raspberry Pi's IP and port

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

def fetch_jinum_from_mysql(prodn):
    try:
        conn_mysql = mysql_pool.get_connection()
        cursor = conn_mysql.cursor()

        sql = "SELECT JINUM FROM Jithead WHERE PRODN = %s"
        cursor.execute(sql, (prodn,))
        result = cursor.fetchone()
        cursor.fetchall()  # Clear any unread results

        cursor.close()
        conn_mysql.close()

        if result:
            return result[0]
        else:
            return None

    except MySQLError as err:
        logging.error(f"Failed to fetch JINUM from MySQL: {err}")
        return None

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

def fetch_bom_data(material):
    try:
        conn_sap = Connection(**SAP_CONN_PARAMS)
        datuv = datetime.now().date()
        werks = "TN10"
        stlan = "3"

        bom_data = conn_sap.call("CS_BOM_EXPL_MAT_V2_RFC", 
                             DATUV=datuv,
                             MTNRV=material,
                             WERKS=werks,
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

        processed_bom_data = process_bom_data(bom_data)

        last_bom_data = None
        for item in processed_bom_data:
            if item["Material"].startswith("B") or item["Material"].startswith("P"):
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
            material = item.get("IDNRK", "").lstrip('0')
            component = {
                "Material": material,
                "Description": item.get("OJTXP", ""),
                "Quantity": item.get("MNGLG", ""),
            }
            bom_list.append(component)
        return bom_list
    except Exception as e:
        logging.error(f"Error processing BOM data: {e}")
        logging.error(traceback.format_exc())
        return []

@app.route('/')
def index():
    sap_system = identify_sap_system()
    return render_template('index1.html', sap_system=sap_system)

@app.route('/fetch_jit_components', methods=['POST'])
def fetch_jit_components():
    start_time = time.time()

    prodn = request.form['prodn'].strip()
    if not prodn:
        return jsonify({'error': 'Please enter a PRODN value.'})

    jinum = fetch_jinum_from_mysql(prodn)
    if not jinum:
        return jsonify({'error': f'Could not find JINUM for PRODN: {prodn}'})

    jitcalcomponents = call_bapi_get_details(jinum)
    if not jitcalcomponents:
        return jsonify({'error': f'No JIT Call Components found for JINUM: {jinum}'})

    results = [None] * len(jitcalcomponents)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_index = {executor.submit(fetch_bom_data, component['MATERIAL']): i for i, component in enumerate(jitcalcomponents)}
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                results[index] = future.result()
            except Exception as exc:
                logging.error(f"Error in concurrent execution: {exc}")

    response = []
    filtered_materials = []
    for i, component in enumerate(jitcalcomponents):
        response.append({'component': component, 'bom_data': results[i]})
        if results[i]:
            for bom_item in results[i]:
                if (prodn.startswith('P') and bom_item['Material'].startswith('P')) or (not prodn.startswith('P') and bom_item['Material'].startswith('B')):
                    filtered_materials.append(bom_item['Material'])

    execution_time = time.time() - start_time

    try:
        requests.post(RPI_ADDRESS, json={'materials': filtered_materials})
    except Exception as e:
        logging.error(f"Failed to send materials to Raspberry Pi: {e}")

    return jsonify({'results': response, 'execution_time': execution_time})

if __name__ == '__main__':
    app.run(debug=True)
