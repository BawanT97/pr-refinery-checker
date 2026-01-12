import os
import json
import io
from boxsdk import JWTAuth, Client
from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser

# --- OPTIONAL IMPORTS FOR FILE READING ---
# We wrap these in try/except so the script doesn't crash if you don't have them.
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from pypdf import PdfReader
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# ==========================================
# 1. GLOBAL CONFIGURATION
# ==========================================

# MODE: 'SEARCH_DOCS' (Manuals) or 'FETCH_REPORTS' (Deep dive for data)
OPERATION_MODE = os.environ.get('BOX_OPERATION_MODE', 'FETCH_REPORTS') 

# --- CONFIG FOR 'SEARCH_DOCS' ---
SEARCH_QUERY = os.environ.get('EQUIPMENT_TAG', 'P-201') 

# --- CONFIG FOR 'FETCH_REPORTS' ---
TARGET_FOLDER_ID = '353555683050' 
REPORT_FILTER_MODE = 'LAST_X_DAYS' 
DAYS_BACK = 7 

# SEARCH STRING for finding reports (The script looks for this in the filename)
# We can leave this broad ('Daily Analysis') or specific ('Daily Analysis - Unit 1')
REPORT_NAME_KEYWORD = "Daily Analysis"

# ==========================================
# 2. AUTHENTICATION
# ==========================================
def get_box_client():
    try:
        if 'BOX_CONFIG_JSON' in os.environ:
            config_json = json.loads(os.environ['BOX_CONFIG_JSON'])
            auth = JWTAuth.from_settings_dictionary(config_json)
        else:
            auth = JWTAuth.from_settings_file('config.json') # Local fallback
        return Client(auth)
    except Exception as e:
        print(f"Authentication Failed: {e}")
        return None

# ==========================================
# 3. HELPER: SMART FILE READER
# ==========================================
def read_file_content(client, file_obj):
    """
    Downloads file bytes and converts to text based on extension.
    """
    file_name = file_obj.name.lower()
    file_id = file_obj.id
    
    print(f"   Downloading content for: {file_obj.name}...")
    
    # Download raw bytes into memory
    file_stream = io.BytesIO()
    client.file(file_id).download_to(file_stream)
    file_stream.seek(0)

    try:
        # A. CSV Handling
        if file_name.endswith('.csv'):
            return file_stream.read().decode('utf-8', errors='ignore')

        # B. EXCEL Handling (Requires pandas & openpyxl)
        elif file_name.endswith(('.xlsx', '.xls')):
            if HAS_PANDAS:
                # Read all sheets, convert to string
                df_dict = pd.read_excel(file_stream, sheet_name=None)
                output = ""
                for sheet, df in df_dict.items():
                    output += f"\n--- Sheet: {sheet} ---\n"
                    output += df.to_csv(index=False)
                return output
            else:
                return "[ERROR] Found Excel file but 'pandas' library is missing. Please pip install pandas openpyxl."

        # C. PDF Handling (Requires pypdf)
        elif file_name.endswith('.pdf'):
            if HAS_PDF:
                reader = PdfReader(file_stream)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            else:
                return "[ERROR] Found PDF file but 'pypdf' library is missing. Please pip install pypdf."

        # D. Text/Other
        else:
            return file_stream.read().decode('utf-8', errors='ignore')

    except Exception as e:
        return f"[ERROR READING FILE] {e}"

# ==========================================
# 4. LOGIC: FETCH LAB REPORTS (DEEP SEARCH)
# ==========================================
def run_report_logic(client, folder_id):
    print(f"--> 📊 Deep Scanning for '{REPORT_NAME_KEYWORD}' in folder {folder_id}...")

    # WE USE SEARCH INSTEAD OF FOLDER.GET_ITEMS
    # This automatically looks inside subfolders!
    results = client.search().query(
        query=REPORT_NAME_KEYWORD,
        limit=50000,
        ancestor_folder_ids=[folder_id],
        file_extensions=['csv', 'pdf', 'xlsx', 'xls']
    )

    matches = []
    now = datetime.now(timezone.utc)

    # 1. Filter results by Date
    for file in results:
        # Box returns items, we check modified date
        if file.modified_at:
            file_date = date_parser.parse(file.modified_at)
            
            # Apply 'LAST_X_DAYS' logic (Simplify for brevity, add others if needed)
            if REPORT_FILTER_MODE == 'LAST_X_DAYS':
                cutoff = now - timedelta(days=DAYS_BACK)
                if file_date >= cutoff:
                    matches.append(file)
            else:
                # If no date filter, take all found
                matches.append(file)

    if not matches:
        return "❌ No recent report files found in this folder or its subfolders."

    # 2. Sort Newest First
    sorted_files = sorted(matches, key=lambda x: x.modified_at, reverse=True)
    print(f"✅ Found {len(sorted_files)} matching files.")

    full_output = ""

    # 3. Process Content
    for f in sorted_files:
        content = read_file_content(client, f)
        
        full_output += f"\n=== REPORT: {f.name} (ID: {f.id} | Date: {f.modified_at}) ===\n"
        full_output += content[:50000] # Safety limit to prevent token overflow
        full_output += f"\n=== END REPORT ===\n"
        full_output += "-" * 40

    return full_output

# ==========================================
# 5. LOGIC: SEARCH MANUALS
# ==========================================
def run_search_logic(client, query):
    print(f"--> 🔍 Searching Box for Manuals/Docs: {query}")
    results = client.search().query(query, limit=5, type='file')
    context_block = ""
    for item in results:
        context_block += f"Filename: {item.name} | Link: {item.get_url()}\n"
    
    return context_block if context_block else "No manuals found."

# ==========================================
# 6. EXECUTION
# ==========================================
if __name__ == "__main__":
    client = get_box_client()
    
    if client:
        if OPERATION_MODE == 'FETCH_REPORTS':
            output = run_report_logic(client, TARGET_FOLDER_ID)
        else:
            output = run_search_logic(client, SEARCH_QUERY)

        print("\nCONTEXT_BLOCK_START")
        print(output)
        print("CONTEXT_BLOCK_END")
