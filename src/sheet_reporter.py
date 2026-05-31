import gspread
import os
import json
from google.oauth2.service_account import Credentials
from gspread_formatting import (
    format_cell_range, CellFormat, Color, TextFormat,
    set_frozen, set_column_width
)
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

COLOR_POSTULER = Color(0.714, 0.843, 0.659)
COLOR_PEUT_ETRE = Color(1.0, 0.949, 0.667)
COLOR_HEADER = Color(0.157, 0.306, 0.475)

def get_sheet():
    credentials_json = os.getenv("GOOGLE_CREDENTIALS")
    credentials_dict = json.loads(credentials_json)
    credentials = Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)
    client = gspread.authorize(credentials)
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    return client.open_by_key(sheet_id).sheet1

def add_filters(spreadsheet, sheet):
    sheet_id = sheet._properties['sheetId']
    spreadsheet.batch_update({
        "requests": [{
            "setBasicFilter": {
                "filter": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "startColumnIndex": 0,
                        "endColumnIndex": 12
                    }
                }
            }
        }]
    })

def add_banding(spreadsheet, sheet):
    sheet_id = sheet._properties['sheetId']
    spreadsheet.batch_update({
        "requests": [{
            "addBanding": {
                "bandedRange": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": 12
                    },
                    "rowProperties": {
                        "headerColor": {"red": 0.157, "green": 0.306, "blue": 0.475},
                        "firstBandColor": {"red": 1, "green": 1, "blue": 1},
                        "secondBandColor": {"red": 0.949, "green": 0.949, "blue": 0.949}
                    }
                }
            }
        }]
    })

def add_statut_validation(spreadsheet, sheet):
    sheet_id = sheet._properties['sheetId']
    spreadsheet.batch_update({
        "requests": [{
            "setDataValidation": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 1,
                    "startColumnIndex": 9,
                    "endColumnIndex": 10
                },
                "rule": {
                    "condition": {
                        "type": "ONE_OF_LIST",
                        "values": [
                            {"userEnteredValue": "À postuler"},
                            {"userEnteredValue": "Postulé"},
                            {"userEnteredValue": "Entretien"},
                            {"userEnteredValue": "Refus"},
                            {"userEnteredValue": "Offre"},
                            {"userEnteredValue": "Abandonné"}
                        ]
                    },
                    "showCustomUi": True,
                    "strict": True
                }
            }
        }]
    })

def init_sheet(spreadsheet, sheet):
    if sheet.row_values(1) == []:
        sheet.append_row([
            "Date", "Titre", "Entreprise", "Score", "Verdict",
            "Localisation", "Contrat", "Télétravail", "URL", "Statut", "Prochaine action", "Notes"
        ], value_input_option="RAW")

        format_cell_range(sheet, "1:1", CellFormat(
            backgroundColor=COLOR_HEADER,
            textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1)),
        ))
        set_frozen(sheet, rows=1)

        set_column_width(sheet, "A", 90)
        set_column_width(sheet, "B", 220)
        set_column_width(sheet, "C", 150)
        set_column_width(sheet, "D", 60)
        set_column_width(sheet, "E", 100)
        set_column_width(sheet, "F", 130)
        set_column_width(sheet, "G", 100)
        set_column_width(sheet, "H", 110)
        set_column_width(sheet, "I", 60)
        set_column_width(sheet, "J", 110)
        set_column_width(sheet, "K", 150)
        set_column_width(sheet, "L", 200)

        add_filters(spreadsheet, sheet)
        add_banding(spreadsheet, sheet)
        add_statut_validation(spreadsheet, sheet)

def format_job_rows(sheet, start_row: int, rows: list):
    for i, row in enumerate(rows):
        verdict = row[4]
        color = COLOR_POSTULER if verdict == "POSTULER" else COLOR_PEUT_ETRE
        row_num = start_row + i
        format_cell_range(sheet, f"{row_num}:{row_num}", CellFormat(
            backgroundColor=color
        ))

def append_jobs(results: list[tuple]) -> None:
    try:
        credentials_json = os.getenv("GOOGLE_CREDENTIALS")
        credentials_dict = json.loads(credentials_json)
        credentials = Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)
        client = gspread.authorize(credentials)
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        spreadsheet = client.open_by_key(sheet_id)
        sheet = spreadsheet.sheet1

        init_sheet(spreadsheet, sheet)

        date_str = datetime.now().strftime("%d/%m/%Y")
        rows = []

        for job, result in results:
            if result['verdict'] in ["POSTULER", "PEUT-ÊTRE"]:
                rows.append([
                    date_str,
                    job['title'],
                    job['company'],
                    result['score'],
                    result['verdict'],
                    job['location'],
                    job['contract'],
                    job['remote'],
                    f'=HYPERLINK("{job["url"]}","Voir offre")',
                    "À postuler" if result['verdict'] == "POSTULER" else "À évaluer",
                    "",
                    ""
                ])

        if rows:
            start_row = len(sheet.get_all_values()) + 1
            sheet.append_rows(rows, value_input_option="USER_ENTERED")
            format_job_rows(sheet, start_row, rows)
            print(f"Google Sheet updated with {len(rows)} new jobs.")
        else:
            print("No jobs to add to Google Sheet.")

    except Exception as e:
        print(f"Google Sheet error: {e}")