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

# Function to connect to SAP and read table data
def read_table_from_sap():
    try:
        # Connect to SAP
        conn_sap = Connection(**SAP_CONN_PARAMS)

        # Table and field parameters
        table = 'JITHD'
        fields = [{'FIELDNAME': 'JINUM'}, {'FIELDNAME': 'PRODN'}]

        # Read table data using RFC_READ_TABLE
        result = conn_sap.call('RFC_READ_TABLE',
                               QUERY_TABLE=table,
                               DELIMITER='|',
                               NO_DATA='',
                               ROWSKIPS=0,
                               ROWCOUNT=0,
                               FIELDS=fields)

        # Disconnect from SAP
        conn_sap.close()

        # Format and return data
        data = []
        for row in result['DATA']:
            wa = row['WA']
            # Split the concatenated string into individual fields
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
        # Connect to MySQL
        conn_mysql = mysql.connector.connect(**MYSQL_CONN_PARAMS)
        cursor = conn_mysql.cursor()

        # Prepare SQL statement for insertion
        sql = "INSERT INTO Jithead (PRODN, JINUM) VALUES (%s, %s)"

        # Insert each row into the table
        cursor.executemany(sql, data)
        conn_mysql.commit()

        # Disconnect from MySQL
        cursor.close()
        conn_mysql.close()

        print("Data inserted into MySQL successfully.")

    except mysql.connector.Error as err:
        print(f"Failed to insert data into MySQL: {err}")

# Main function to execute the script
def main():
    # Retrieve data from SAP
    data = read_table_from_sap()
    if not data:
        return

    # Insert data into MySQL
    insert_into_mysql(data)

# Execute the main function when the script is run
if __name__ == "__main__":
    main()
