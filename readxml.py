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

FILE_STRING_FORMAT = '    <string name="%s">%s</string>'
SPREADSHEET_ID = '1DqZh4PzfZ89L1J3QY99zYB0d54hv_QDGAFLiVvVOIow'
# SPREADSHEET_ID = '1-RsjRGU0U551-xneX_Mom4AnQw5PDILigXHd2kIoQzg'
RANGE_VALUES = 'Data!%s:%s'
RE_KEY_PAIR_STRING = re.compile(r'<string\s+name="([^"]+)(?!translatable\s*=\s*"false")">(.+?)</string>',
                                flags=re.IGNORECASE | re.MULTILINE)
RE_TRANSLATABLE = re.compile(r'\btranslatable\s*=\s*"false"\b', flags=re.IGNORECASE)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--files',
                        type=argparse.FileType('r'),
                        nargs='+',
                        default="strings_ru.xml",
                        help="Input file, <strings.xml> as default")
    parser.add_argument('-d', '--documents',
                        type=str,
                        default=SPREADSHEET_ID,
                        help="document id")
    parser.add_argument('-c', '--clear',
                        default=False,
                        action="store_true",
                        help="clear other lang")

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

    # keys, values = [], []
    dictionary, result, keys = {}, {}, {}
    for file in args.files:
        try:
            # print('file [%s]' % file.name)
            input_text = open(file.name, 'r').read()
            dictionary[file.name] = {}
            for (key, value) in sorted(re.findall(RE_KEY_PAIR_STRING, input_text)):
                # print("parsed: {[%s]:[%s]}" % (key, value))
                dictionary[file.name][key] = value
                keys[key] = ""
        except IOError:
            pass

    for key in sorted(keys.keys()):
        result.setdefault('.name', []).append(key)
        for file in dictionary.keys():
            if key in dictionary[file].keys():
                result.setdefault(file, []).append(dictionary[file][key])
            else:
                result.setdefault(file, []).append("")
    # print(result)

    if len(dictionary) > 0:
        current_value_column = 'A'
        for key in result.keys():
            # clean values in languages column
            values_range = RANGE_VALUES % (current_value_column, current_value_column)
            # print(values_range)
            sheet.values().clear(spreadsheetId=SPREADSHEET_ID, range=values_range).execute()

            update_list = [key]
            update_list.extend(result[key])
            # print(update_list)
            update_body = {'valueInputOption': 'RAW',
                           'data': [{
                               'range': values_range,
                               'majorDimension': 'COLUMNS',
                               'values': [update_list]
                           }]
                           }
            # print(json.dumps(update_body))
            print(sheet.values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=update_body).execute())
            current_value_column = chr(ord(current_value_column) + 1)


if __name__ == '__main__':
    main()
