from pyrfc import Connection
from pprint import pprint

# Create a connection to the SAP system
conn = Connection(
    user='touatigb',
    passwd='NEver@winfcd100',
    ashost='137.121.21.13',
    sysnr='13',
    client='100',
    lang='EN'
)

# Define the parameters
params = {
    'CALLCONTROLID': 'YOUR_CALLCONTROLID',  # Replace with your actual CALLCONTROLID
    'EXTCALLNUMBER': '220975001207',        # External JIT call number
    'DETAILLEVEL': '3'                      # Detail level to get full details including components
}

# Call the BAPI
result = conn.call('BAPI_JITCALLIN_GETDETAIL', **params)

# Extract and print the required tables
jitcalls = result.get('JITCALLS', [])
jitcallheaders = result.get('JITCALLHEADERS', [])
jitcallcomponentgroups = result.get('JITCALLCOMPONENTGROUPS', [])
jitcallcomponents = result.get('JITCALLCOMPONENTS', [])
return_messages = result.get('RETURN', [])

# Print the results
pprint(jitcalls)
pprint(jitcallheaders)
pprint(jitcallcomponentgroups)
pprint(jitcallcomponents)
pprint(return_messages)
