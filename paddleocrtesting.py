import ast
import json
import os
import requests
import re

#Constants
EXCHANGE_RATE_API_URL = 'https://v6.exchangerate-api.com/v6/df71466400a9e7db30b617b1/latest/USD'
OCR_OUTPUT_FILE = 'ocr_return.json'

def process_bill(img_path, chat, ocr):
    response = requests.get(EXCHANGE_RATE_API_URL)
    tmp = response.json()
    exchange_rate = tmp['conversion_rates']['LBP']
    data = {}
    result = ocr.ocr(img_path, cls=True)
    if not result: #check if empty -> reset return file
        removeReturn()
        
    print(result)
    result_processed1 = {}
    for idx in range(len(result)):
        res = result[idx]
        for line in res:
            precision = line[-1][1] #precision score
            if(precision < 0.75):
                continue
            tmpc = line[0][0][1] #y
            text = line[-1][0]
            if(tmpc in result_processed1):
                result_processed1[tmpc] += " " + text
            else:
                result_processed1[tmpc] = text

    print(result_processed1)
    res = str(result_processed1)
    response=chat.send_message("Give me the business name of this invoice:" + res + "\ngeneraly at the top.")
    var = check(response.text)
    data['business_name'] = response.text
    response=chat.send_message("Give me the category of this invoice:" + res + "\nin 1 word; you have the choice between 'Restaurant', 'Household', 'Drugs', 'Electronics', or 'Groceries'.")
    var = check(response.text)
    data['category'] = response.text
    response=chat.send_message("Give me the date of this invoice:" + res + "\nin format year/month/day.")
    var = var and check(response.text)
    data['date'] = response.text
    response=chat.send_message("Give me the check id of this invoice:" + res + "\nin numeric.\nIf not available, say '-'.")
    var = var and check(response.text)
    if(not var):
        removeReturn()
    data['check_id'] = response.text
    data['total'] = 0

    with open(OCR_OUTPUT_FILE, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    response=chat.send_message("Give me all the items displayed in this invoice in form of a dictionary:" + res + "\nin a python list in a format ['quantity','name','price'], for example: [['Quantity1','Name1','Price1'],['Quantity2','Name2','Price2']].")
    items = ast.literal_eval(response.text)
    i = 1
    total = 0
    for item in items:
        dict = {}
        if item[0] is None or item[1] is None or item[2] is None:
            removeReturn()
        q = item[0]
        if any(char.isdigit() for char in q):
            dict['quantity'] = q
        else:
            dict['quantity'] = '0'
        dict['name'] = item[1]
        p = item[2]
        if 'O' in p:
            p = p.replace('O','0')
        p = re.sub(r'^[^0-9.]*([0-9]+\.?[0-9]*)[^0-9.]*$', r'\1', p)
        if p:
            if '$' in p:
                p = p.replace('$', '')
                p = str(int(float(p) * exchange_rate))  # actual rate
            elif '.' in p:
                if float(p) < 10000:  # == in $
                    p = str(int(float(p) * exchange_rate))
        else:
            p = '0'
        dict['price'] = p
        total += float(p)
        data['item' + str(i)] = dict
        i += 1
    data['total'] = str(int(total))

    with open(OCR_OUTPUT_FILE, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    return data

def removeReturn():
    if os.path.exists(OCR_OUTPUT_FILE):
        os.remove(OCR_OUTPUT_FILE)
    return {}

def check(var):
    if var is None or var == '0':
        return False
    return True