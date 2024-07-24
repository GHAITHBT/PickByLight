from pyrfc import Connection
import mysql.connector
import time

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
    "database": "PickByLight"
}

# Function to connect to SAP and read table data
def read_table_from_sap():
    try:
        conn_sap = Connection(**SAP_CONN_PARAMS)
        table = 'JITHD'
        fields = [{'FIELDNAME': 'JINUM'}, {'FIELDNAME': 'PRODN'}]

        result = conn_sap.call('RFC_READ_TABLE',
                               QUERY_TABLE=table,
                               DELIMITER='|',
                               NO_DATA='',
                               ROWSKIPS=0,
                               ROWCOUNT=0,
                               FIELDS=fields)

        conn_sap.close()

        data = []
        for row in result['DATA']:
            wa = row['WA']
            prodn = wa[11:23].strip()  # Adjust length based on actual field width
            jinum = wa[0:10].strip()  # Adjust length based on actual field width
            data.append((prodn, jinum))

        return data

    except Exception as e:
        print(f"Failed to retrieve data from SAP: {e}")
        return None

# Function to insert data into MySQL database
def insert_into_mysql(data):
    try:
        conn_mysql = mysql.connector.connect(**MYSQL_CONN_PARAMS)
        cursor = conn_mysql.cursor()

        sql = "INSERT INTO Jithead (PRODN, JINUM) VALUES (%s, %s)"

        chunk_size = 1000  # Adjust based on your needs

        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            cursor.executemany(sql, chunk)
            conn_mysql.commit()

        cursor.close()
        conn_mysql.close()

        print("Data inserted into MySQL successfully.")

    except mysql.connector.Error as err:
        print(f"Failed to insert data into MySQL: {err}")

# Main function to execute the script
def main():
    start_time = time.time()  # Start time measurement

    data = read_table_from_sap()
    if not data:
        return

    insert_into_mysql(data)

    end_time = time.time()  # End time measurement
    elapsed_time = end_time - start_time
    print(f"Execution time: {elapsed_time:.2f} seconds")

# Execute the main function when the script is run
if __name__ == "__main__":
    main()
