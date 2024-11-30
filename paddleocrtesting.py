import os
import ast
import requests
import json

#Constants
OCR_OUTPUT_FILE = "ocr_return.json"
EXCHANGE_RATE_API_URL = "https://v6.exchangerate-api.com/v6/df71466400a9e7db30b617b1/latest/USD"

def remove_return_file():
    """Remove the OCR output file if it exists."""
    if os.path.exists(OCR_OUTPUT_FILE):
        os.remove(OCR_OUTPUT_FILE)


def is_valid_input(value):
    """Check if a value is valid (not None or empty)."""
    return bool(value and value != "0")


def normalize_price(price, exchange_rate):
    """Normalize the price based on exchange rate."""
    if not price:
        return "0"
    price = price.replace("O", "0").replace("$", "").strip()
    try:
        value = float(price)
        if value < 10000:  #Assume it's in USD if < 10000
            value *= exchange_rate
        return str(int(value))
    except ValueError:
        return "0"


def parse_items(items_text, exchange_rate):
    """Parse items into structured format."""
    items = ast.literal_eval(items_text)
    total = 0
    parsed_items = []
    for item in items:
        quantity, name, price = item
        normalized_price = normalize_price(price, exchange_rate)
        parsed_items.append({"quantity": quantity, "name": name, "price": normalized_price})
        total += int(normalized_price)
    return parsed_items, total


def parse_ocr_result(ocr_result):
    """Parse OCR result into structured format."""
    result_processed = {}
    for line in ocr_result:
        try:
            y_coord = str(line[0][0][1])  #Ensure y_coord is a string
            text = line[-1][1]
            result_processed[y_coord] = result_processed.get(y_coord, "") + " " + text
        except (IndexError, TypeError):
            continue
    return result_processed


def get_invoice_details(chat, ocr_text, data):
    """Get invoice details via chat."""
    details = ["business_name", "category", "date", "check_id"]
    prompts = [
        "Give me the business name of this invoice: ",
        "Give me the category of this invoice (e.g., Restaurant): ",
        "Give me the date of this invoice (YYYY/MM/DD): ",
        "Give me the check ID of this invoice (numeric or '-'): ",
    ]
    for detail, prompt in zip(details, prompts):
        response = chat.send_message(prompt + ocr_text)
        if not is_valid_input(response.text):
            remove_return_file()
            return {}
        data[detail] = response.text
    return data

def process_bill(img_path, chat, ocr):
    """Process the bill from the given image."""
    #Fetch exchange rate
    try:
        response = requests.get(EXCHANGE_RATE_API_URL)
        response.raise_for_status()
        exchange_rate = response.json().get("conversion_rates", {}).get("LBP", 1)
    except requests.RequestException:
        remove_return_file()
        return {}

    #Perform OCR
    result = ocr.ocr(img_path, cls=True)
    if not result:
        remove_return_file()
        return {}

    #Parse OCR result
    ocr_text = str(parse_ocr_result(result))
    data = {}
    data = get_invoice_details(chat, ocr_text, data)
    if not data:
        return {}

    #Get items and calculate total
    response = chat.send_message(
        "Give me all the items displayed in this invoice as a list in the format: "
        "[['quantity', 'name', 'price'], ...]"
    )
    try:
        parsed_items, total = parse_items(response.text, exchange_rate)
    except (SyntaxError, ValueError):
        remove_return_file()
        return {}

    data.update({"items": parsed_items, "total": str(total)})

    #Save to file
    with open(OCR_OUTPUT_FILE, "w") as json_file:
        json.dump(data, json_file, indent=4)

    return data