import gspread
import os
import json
from google.oauth2.service_account import Credentials
from gspread_formatting import set_column_width
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_credentials():
    credentials_json = os.getenv("GOOGLE_CREDENTIALS")
    credentials_dict = json.loads(credentials_json)
    return Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)

def get_spreadsheet():
    client = gspread.authorize(get_credentials())
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    return client.open_by_key(sheet_id)

def get_table_id(spreadsheet, sheet_id):
    data = spreadsheet.fetch_sheet_metadata()
    for s in data.get("sheets", []):
        if s["properties"]["sheetId"] == sheet_id:
            for table in s.get("tables", []):
                return table["tableId"]
    return None

def create_table(spreadsheet, sheet, sheet_id, num_rows):
    spreadsheet.batch_update({
        "requests": [{
            "addTable": {
                "table": {
                    "name": "Job Hunt",
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1 + num_rows,
                        "startColumnIndex": 0,
                        "endColumnIndex": 12
                    },
                    "columnProperties": [
                        {"columnIndex": 0, "columnType": "TEXT"},
                        {"columnIndex": 1, "columnType": "TEXT"},
                        {"columnIndex": 2, "columnType": "TEXT"},
                        {"columnIndex": 3, "columnType": "TEXT"},
                        {"columnIndex": 4, "columnType": "DROPDOWN",
                         "dataValidationRule": {"condition": {"type": "ONE_OF_LIST", "values": [
                             {"userEnteredValue": "POSTULER"},
                             {"userEnteredValue": "PEUT-ÊTRE"}
                         ]}}},
                        {"columnIndex": 5, "columnType": "TEXT"},
                        {"columnIndex": 6, "columnType": "TEXT"},
                        {"columnIndex": 7, "columnType": "TEXT"},
                        {"columnIndex": 8, "columnType": "TEXT"},
                        {"columnIndex": 9, "columnType": "DROPDOWN",
                         "dataValidationRule": {"condition": {"type": "ONE_OF_LIST", "values": [
                             {"userEnteredValue": "À postuler"},
                             {"userEnteredValue": "Postulé"},
                             {"userEnteredValue": "Entretien"},
                             {"userEnteredValue": "Refus"},
                             {"userEnteredValue": "Offre"},
                             {"userEnteredValue": "Abandonné"}
                         ]}}},
                        {"columnIndex": 10, "columnType": "TEXT"},
                        {"columnIndex": 11, "columnType": "TEXT"}
                    ]
                }
            }
        }]
    })

    set_column_width(sheet, "A", 90)
    set_column_width(sheet, "B", 220)
    set_column_width(sheet, "C", 150)
    set_column_width(sheet, "D", 60)
    set_column_width(sheet, "E", 110)
    set_column_width(sheet, "F", 130)
    set_column_width(sheet, "G", 100)
    set_column_width(sheet, "H", 130)
    set_column_width(sheet, "I", 90)
    set_column_width(sheet, "J", 120)
    set_column_width(sheet, "K", 150)
    set_column_width(sheet, "L", 200)

def extend_table(spreadsheet, sheet_id, table_id, current_end_row, num_new_rows):
    spreadsheet.batch_update({
        "requests": [{
            "updateTable": {
                "table": {
                    "tableId": str(table_id),
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": current_end_row + num_new_rows,
                        "startColumnIndex": 0,
                        "endColumnIndex": 12
                    }
                },
                "fields": "range"
            }
        }]
    })

def append_to_table(spreadsheet, sheet_id, table_id, rows):
    cell_data = []
    for row in rows:
        row_data = []
        for cell in row:
            if isinstance(cell, str) and cell.startswith("="):
                row_data.append({"userEnteredValue": {"formulaValue": cell}})
            elif isinstance(cell, (int, float)):
                row_data.append({"userEnteredValue": {"numberValue": cell}})
            else:
                row_data.append({"userEnteredValue": {"stringValue": str(cell)}})
        cell_data.append({"values": row_data})

    spreadsheet.batch_update({
        "requests": [{
            "appendCells": {
                "tableId": str(table_id),
                "rows": cell_data,
                "fields": "userEnteredValue"
            }
        }]
    })

def append_jobs(results: list[tuple]) -> None:
    try:
        spreadsheet = get_spreadsheet()
        sheet = spreadsheet.sheet1
        sheet_id = sheet._properties["sheetId"]

        date_str = datetime.now().strftime("%d/%m/%Y")
        rows = []

        for job, result in results:
            if result["verdict"] in ["POSTULER", "PEUT-ÊTRE"]:
                rows.append([
                    date_str,
                    job["title"],
                    job["company"],
                    result["score"],
                    result["verdict"],
                    job["location"],
                    job["contract"],
                    job["remote"],
                    f'=HYPERLINK("{job["url"]}","Voir offre")',
                    "À postuler" if result["verdict"] == "POSTULER" else "À évaluer",
                    "",
                    ""
                ])

        if not rows:
            print("No jobs to add to Google Sheet.")
            return

        table_id = get_table_id(spreadsheet, sheet_id)

        if table_id is None:
            # Write header first so table picks up column names
            sheet.append_row([
                "Date", "Titre", "Entreprise", "Score", "Verdict",
                "Localisation", "Contrat", "Télétravail", "URL",
                "Statut", "Prochaine action", "Notes"
            ], value_input_option="RAW")
            # Write data rows
            sheet.append_rows(rows, value_input_option="USER_ENTERED")
            # Create table on top of existing data
            create_table(spreadsheet, sheet, sheet_id, len(ro