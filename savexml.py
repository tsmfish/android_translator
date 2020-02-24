from __future__ import print_function

import argparse
import os
import os.path
import pickle
import re

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# SCOPES = ['https://www.googleapis.com/auth/drive']

FILE_HEADER = '<resources>\n'
FILE_FOOTER = '</resources>'
FILE_STRING_FORMAT = '    <string name="%s">%s</string>\n'
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
                        type=argparse.FileType('w'),
                        default="strings.xml",
                        help="XML files wheel write into language/<file name/string.xml as default>")
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

    sheet = service.spreadsheets()
    args = get_args()

    languages = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                   range=RANGE_LANGUAGES,
                                   majorDimension="COLUMNS").execute().get('values', [])
    keys = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_KEYS, majorDimension="ROWS") \
        .execute().get('values', [])
    # print('keys: [%s]' % keys)
    dictionary = {}
    current_value_column = 'B'
    if len(languages) > 0 and len(keys) > 0:
        for language in languages:
            # print('language: [%s]' % language)
            values_range = RANGE_VALUES % (current_value_column, current_value_column)
            print(values_range)
            dictionary[language[0]] = {}
            values = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=values_range, majorDimension="ROWS") \
                .execute().get('values', [])
            for pointer in range(min(len(keys), len(values))):
                # print('%d: {[%s]:[%s]}' % (pointer, keys[pointer][0], values[pointer][0]))
                dictionary[language[0]][keys[pointer][0]] = values[pointer][0]
            current_value_column = chr(ord(current_value_column) + 1)

    if len(dictionary) > 0:
        for language in dictionary.keys():
            file_text = FILE_HEADER
            for key in sorted(dictionary[language].keys()):
                file_text += FILE_STRING_FORMAT % (key, dictionary[language][key])
            file_text += FILE_FOOTER
            # print(file_text)
            # try:
            os.makedirs(language.lower(), exist_ok=True)
            # except FileExistsError:
            #     print()

            try:
                output = open('%s/%s' % (language.lower(), args.xml.name), 'w')
                output.write(file_text)
                output.close()
            except IOError:
                print("Can't open file %s/%s" % (language.lower(), args.xml.name))
                pass


if __name__ == '__main__':
    main()
