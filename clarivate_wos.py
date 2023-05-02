# -*- coding: utf-8 -*-
"""Clarivate WoS.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1naEcJ94YMeGAYjNqBu86uW0Xrb447T_t
"""

#!pip install rispy

import requests
import json
import time
import re
import csv
import rispy

"""Get the author list"""

authors_url = 'https://gist.githubusercontent.com/ibshelp/1c078ff8692574ba0e5665b7372c973f/raw/c4d04643b246a0802003bde1e22f5df5679c6de8/IBS%2520Researchers'

author_list = requests.get(authors_url).text.split('\n')
print(f'First record: {author_list[0]}\nLast record: {author_list[-1]}')

"""Go get the API definition"""

base_url = 'https://wos-api.clarivate.com/api/woslite'
#base_url = 'https://wos-api.clarivate.com/api/wos'
api_key = '98c6817fc891c194dce9ed0170cddf259d092a87'
api_user = 'b681ff0ecd9c154da0dc8e22f9cae39d6ffb4409'

result = requests.get(f'{base_url}/swagger?forUser={api_user}').json()

with open('swagger_def.txt', 'w') as file:
    file.write(json.dumps(result, indent=2))

"""Do a search using the specification on line 18 in the WOSLite database and dump 
the results to test.txt for debugging.
"""

# Andy Baker
# symbolicTimeSpan= '1week', '2week', '4week'
# TimeSpan

headers = {
    "X-ApiKey": api_key
}

query = {
    "databaseId": "WOS",
    "count": 100,
    "firstRecord": 1,
    "usrQuery": "",
    "sortField": "",
    "symbolicTimeSpan": ""
}

query['usrQuery'] = 'TS=(("latin america" OR "Brazil" OR "Mexico" OR "Chile" OR "Argentina" OR "Uruguay" OR "Peru" OR "Colombia" OR "Bolivia") AND (“labor” OR “labour” OR "welfare" OR "social policy" OR "government expenditure*" OR "health policy" OR "anti-poverty" OR "antipoverty" OR "transfer*" OR "health sector" OR "pension*") NOT ("mental health")) AND LA=("English" OR "Portuguese" OR "Spanish")'
query['symbolicTimeSpan'] = '4week'

result = requests.get(f'{base_url}/', headers=headers, params=query).json()

print(f"Found {result['QueryResult']['RecordsFound']} result(s)")

with open('test.txt', 'w') as file:
    file.write(json.dumps(result, indent=2))

"""Convert the result to RIS format for output and write to test.ris"""

# https://github.com/MrTango/rispy

entries = []
for record in result['Data']:
    cleaned_record = {
        'primary_title': record.get('Title', {}).get('Title')[0],
        'authors': record.get('Author', {}).get('Authors'),
        'publication_year': record.get('Source', {}).get('Published.BiblioYear')[0],
        'keywords': record.get('Keyword', {}).get('Keywords', []),
        'accession_number': record.get('UT'),
        'secondary_title': record.get('Source', {}).get('SourceTitle')[0],
    }

    reference_type = record.get('Doctype', {}).get('Doctype')[0]
    if reference_type == "Article":
        cleaned_record['type_of_reference'] = "EJOUR"
    else:
        ris_type = [k for k, v in rispy.TYPE_OF_REFERENCE_MAPPING.items() if v == reference_type]
        if ris_type == []:
            cleaned_record['type_of_reference'] = "GEN"
        else:
            cleaned_record['type_of_reference'] = ris_type[0]


    doi = record.get('Other', {}).get('Identifier.Doi')
    if doi:
        cleaned_record['doi'] = doi[0]

    issn = record.get('Other', {}).get('Identifier.Issn')
    if issn:
        cleaned_record['issn'] = issn[0]

    pages = record.get('Source', {}).get('Pages')
    if pages and pages[0] != "":
        cleaned_record['start_page'] = pages[0].split('-')[0]
        cleaned_record['end_page'] = pages[-1].split('-')[-1]
    
    issue_number = record.get('Source', {}).get('Issue')
    if issue_number:
        cleaned_record['number'] = issue_number[0]

    volume = record.get('Source', {}).get('Volume')
    if volume:
        cleaned_record['volume'] = volume[0]
    
    date = record.get('Source', {}).get('Published.BiblioDate')
    if date and '-' not in date[0]:
        months = {
            'JAN': '01',
            'FEB': '02',
            'MAR': '03',
            'APR': '04',
            'MAY': '05',
            'JUN': '06',
            'JUL': '07',
            'AUG': '08',
            'SEP': '09',
            'OCT': '10',
            'NOV': '11',
            'DEC': '12'
        }
        year = cleaned_record.get('publication_year')
        date_field = date[0].split(' ')
        month = months.get(date_field[0].upper(), "")
        day = "" if len(date_field) == 1 else date_field[1]
        date_string = f"{year}/{month}/{day}/undefined"
        
        cleaned_record['date'] = date_string

    entries.append(cleaned_record)

with open('test.ris', 'w') as file:
    rispy.dump(entries, file)