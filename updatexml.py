from __future__ import print_function

import argparse
import os.path
import pickle
import re

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.pickle.
# SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
#           'https://www.googleapis.com/auth/drive.file',
#           'https://www.googleapis.com/auth/drive']
SCOPES = ['https://www.googleapis.com/auth/drive']

FILE_STRING_FORMAT = '    <string name="%s">%s</string>'
# SPREADSHEET_ID = '1DqZh4PzfZ89L1J3QY99zYB0d54hv_QDGAFLiVvVOIow'
SPREADSHEET_ID = '1-RsjRGU0U551-xneX_Mom4AnQw5PDILigXHd2kIoQzg'
RANGE_KEYS = 'Data!A2:A'
RANGE_VALUES = 'Data!%s2:%s'
RANGE_LANGUAGES = 'Data!B1:1'
XML_FILE_NAME = 'strings.xml'
RE_KEY_PAIR_STRING = re.compile(r'<string\s+name="([^"]+)(?!translatable\s*=\s*"false")">(.{1,}?)</string>',
                                flags=re.IGNORECASE | re.MULTILINE)
RE_REPLACE_STRING = r'<string\s+name="%s"([^>]*)>(.{1,}?)</string>'
RE_TRANSLATABLE = re.compile(r'\btranslatable\s*=\s*"false"\b', flags=re.IGNORECASE)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--xml',
                        type=argparse.FileType('r'),
                        default="strings.xml",
                        help="XML files wheel write into language/<file name/string.xml as default>")
    parser.add_argument('-d', '--documents',
                        type=str,
                        default="1DqZh4PzfZ89L1J3QY99zYB0d54hv_QDGAFLiVvVOIow",
                        help="document id")

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

            try:
                updated_file = open('%s/%s' % (language.lower(), args.xml.name), 'w')
                updated_text = updated_file.read()

                for key in dictionary[language[0]].keys():
                    re.sub(RE_REPLACE_STRING % key,
                           FILE_STRING_FORMAT % (key, dictionary[language[0]][key]),
                           updated_text,
                           flags=re.IGNORECASE | re.MULTILINE)
                print(updated_text)

                updated_file.write(updated_text)
                updated_file.close()
            except IOError:
                print("Can't open file %s/%s" % (language.lower(), args.xml.name))
                pass
            finally:
                if updated_file:
                    updated_file.close()


if __name__ == '__main__':
    main()
