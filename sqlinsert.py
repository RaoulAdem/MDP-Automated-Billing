import json
import mysql.connector
import os
from base64 import b64encode, b64decode
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "database": os.getenv("DB_NAME"),
}

def is_present(user_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    if not os.path.exists('ocr_return.json'):
        return False
    with open('ocr_return.json', 'r') as file:
        data = json.load(file)

    try:
        cursor.execute("""
            SELECT businessname, date, checkid FROM billinfo WHERE userid = %s AND businessname = %s AND date = %s AND checkid = %s;
            """, (user_id, data["business_name"], data["date"], data["check_id"]))
        row = cursor.fetchone()
        if not row:
            return False
        else:
            if os.path.exists('ocr_return.json'):
                os.remove('ocr_return.json')
            return True
    except mysql.connector.Error as err:
        print(f"Erreur MySQL: {err}")
    except Exception as e:
        print(f"Erreur: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def insert_data(image, user_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    with open('ocr_return.json', 'r') as file:
        data = json.load(file)
    with open(image, 'rb') as f:
        image_data = f.read()
        encoded_image = b64encode(image_data)
        cursor.execute("INSERT INTO `billmanag`.`billinfo` (userid, total, category, businessname, date, image, checkid) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (user_id, data["total"], data["category"], data["business_name"], data["date"], encoded_image, data["check_id"]))
    for i in range(1, len(data)):
        item_key = "item" + str(i)
        if item_key in data:
            item = data[item_key]
            cursor.execute("INSERT INTO `billmanag`.`billitems`(userid, name, price, quantity, checkid) VALUES (%s, %s, %s, %s, %s)",
                        (user_id, item["name"], item["price"], item["quantity"], data["check_id"]))
    conn.commit()
    cursor.close()
    conn.close()

def get_bill_data(user_id, category, date):
    """
    Retrieve bill data based on user ID, category, and date.
    Returns tuple of (rows, total) where rows contains bill details and total is the sum
    """
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        if category == "All":
            cursor.execute("""
                SELECT date, total, businessname
                FROM billinfo
                WHERE userid = %s AND date >= %s
            """, (user_id, date))
            rows = cursor.fetchall()
            
            cursor.execute("""
                SELECT SUM(total)
                FROM billinfo
                WHERE userid = %s AND date >= %s
            """, (user_id, date))
            total = cursor.fetchall()
        else:
            cursor.execute("""
                SELECT date, total, businessname
                FROM billinfo
                WHERE userid = %s 
                AND category = %s 
                AND date >= %s
            """, (user_id, category, date))
            rows = cursor.fetchall()
            
            cursor.execute("""
                SELECT SUM(total)
                FROM billinfo
                WHERE userid = %s 
                AND category = %s 
                AND date >= %s
            """, (user_id, category, date))
            total = cursor.fetchall()
            
        return rows, total
    
    finally:
        cursor.close()
        conn.close()

def get_bill_image(query):
    """Execute query to retrieve bill image"""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        row = cursor.fetchone()
        return row
    finally:
        cursor.close()
        conn.close()