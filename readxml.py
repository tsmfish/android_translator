from __future__ import print_function

import argparse
import os.path
import pickle
import re

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive.file',
          'https://www.googleapis.com/auth/drive']
# SCOPES = ['https://www.googleapis.com/auth/drive']

FILE_HEADER = '<resources>'
FILE_FOOTER = '</resources>'
FILE_STRING_FORMAT = '    <string name="%s">%s</string>'
SPREADSHEET_ID = '1DqZh4PzfZ89L1J3QY99zYB0d54hv_QDGAFLiVvVOIow'
RANGE_KEYS = 'Data!A2:A'
RANGE_VALUES = 'Data!%s2:%s'
RANGE_LANGUAGES = 'Data!B1:1'
XML_FILE_NAME = 'strings.xml'
RE_KEY_PAIR_STRING = re.compile(r'<string\s+name="([^"]+)(?!translatable\s*=\s*"false")">(.{1,}?)</string>',
                                flags=re.IGNORECASE | re.MULTILINE)
RE_TRANSLATABLE = re.compile(r'\btranslatable\s*=\s*"false"\b', flags=re.IGNORECASE)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--xml',
                        type=argparse.FileType('r'),
                        default="strings.xml",
                        help="Input file, <strings.xml> as default")

    return parser.parse_args()


def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    credentials = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    service = build('sheets', 'v4', credentials=credentials)

    # Call the Sheets API
    sheet = service.spreadsheets()
    args = get_args()
    input_text = open(args.xml.name, 'r').read()
    languages = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                   range=RANGE_LANGUAGES,
                                   majorDimension="COLUMNS").execute().get('values', [])
    keys, values = [], []
    for (key, value) in sorted(re.findall(RE_KEY_PAIR_STRING, input_text)):
        # print("parsed: {[%s]:[%s]}" % (key, value))
        keys.append(key)
        values.append(value)

    if len(keys) > 0:
        # clean values in languages column
        current_value_column = 'B'
        if len(languages) > 0:
            for __ in languages:
                values_range = RANGE_VALUES % (current_value_column, current_value_column)
                # print(values_range)
                sheet.values().clear(spreadsheetId=SPREADSHEET_ID, range=values_range).execute()
                current_value_column = chr(ord(current_value_column) + 1)

        # clear key values
        sheet.values().clear(spreadsheetId=SPREADSHEET_ID, range=RANGE_KEYS).execute()

        # english column
        values_range = RANGE_VALUES % ('B', 'B')
        update_body = {'valueInputOption': 'RAW',
                       'data': [{
                           'range': RANGE_KEYS,
                           'majorDimension': 'COLUMNS',
                           'values': [keys]
                       }, {
                           'range': values_range,
                           'majorDimension': 'COLUMNS',
                           'values': [values]
                       }]
                       }
        # print(json.dumps(update_body))
        print(sheet.values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=update_body)
              .execute())


if __name__ == '__main__':
    main()
