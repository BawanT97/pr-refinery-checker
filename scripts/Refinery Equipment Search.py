import os
from boxsdk import JWTAuth, Client
import json

# 1. Authenticate
config_json = json.loads(os.environ['BOX_CONFIG_JSON'])
auth = JWTAuth.from_settings_dictionary(config_json)
client = Client(auth)

# 2. Search Logic (Input from GitHub Issue/Comment)
query = os.environ.get('EQUIPMENT_TAG', 'P-201')  # Default or input
print(f"Searching Box for: {query}")
results = client.search().query(query, limit=5, type='file')

# 3. Output the "Context Block" for the AI
context_block = ""
found = False

for item in results:
    # In a real scenario, you might extract text via OCR here
    # For now, we grab the file name and metadata
    context_block += f"Filename: {item.name} | ID: {item.id} | Link: {item.get_url()}\n"
    found = True

if not found:
    print("No matching documentation found.")
else:
    print("CONTEXT_BLOCK_START")
    print(context_block)
    print("CONTEXT_BLOCK_END")
