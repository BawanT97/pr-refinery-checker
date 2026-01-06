import os
from box_sdk_gen import BoxClient, BoxCCGAuth, CCGConfig

# 1. Setup Connection to Box
config = CCGConfig(
    client_id=os.getenv('BOX_CLIENT_ID'),
    client_secret=os.getenv('BOX_CLIENT_SECRET'),
    enterprise_id=os.getenv('BOX_ENTERPRISE_ID')
)
auth = BoxCCGAuth(config)
client = BoxClient(auth)

def check_refinery_docs(search_term):
    # 2. Search Box for the file
    results = client.search.search_for_content(query=search_term, limit=1)
    
    if results.entries:
        file = results.entries[0]
        # 3. Get a link to the doc
        return f"✅ Found refinery doc: [{file.name}](https://app.box.com/file/{file.id})"
    else:
        return "❌ Warning: No matching refinery documentation found on Box."

if __name__ == "__main__":
    # For a simple test, we just look for "Project-Nihat"
    # You can expand this to read filenames from your git diff!
    status = check_refinery_docs("Project-Nihat")
    print(status)
