import datetime
from fpdf import FPDF
import requests

LBP_URL = 'https://v6.exchangerate-api.com/v6/df71466400a9e7db30b617b1/latest/LBP'
USD_URL = 'https://v6.exchangerate-api.com/v6/df71466400a9e7db30b617b1/latest/USD'
PDF_FILENAME = "AutomatedPDF.pdf"

def fetch_exchange_rate(url):
    """Fetch exchange rate from the given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['conversion_rates']
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None


async def to_pdf(total,rows,dict_responses):
    lbp_rates = fetch_exchange_rate(LBP_URL)
    usd_rates = fetch_exchange_rate(USD_URL)
    pdf = FPDF()
    pdf.add_page()
    pdf.image("logo.png", x=10, y=10, w=50)
    pdf.set_font("Times", size=20, style='B')
    pdf.cell(200, 10, txt = "Automated Billing Archive & Recognition", ln = 1, align = 'R')
    pdf.set_font("Times", size=12)
    pdf.cell(200, 5, txt = "Date: " + str(datetime.datetime.now().date()), ln = 1, align = 'R')
    pdf.cell(200, 5, txt = "Category: " + str(dict_responses["category"]), ln = 1, align = 'R')
    pdf.cell(200, 5, txt = "Currency: " + str(dict_responses["currency"]), ln = 1, align = 'R')
    pdf.ln()
    pdf.set_font("Times", size=15, style='B')
    pdf.cell(200, 8, txt = "Report", ln = 1, align = 'C')
    pdf.set_font("Times", size=12)
    pdf.cell(200, 5, txt = "Exchange rate: " + str(int(lbp_rates)) + " LL", ln = 1, align = 'C')
    pdf.set_font("Times", size=10)
    pdf.set_fill_color(169, 169, 169)
    pdf.ln()
    pdf.cell(30, 8, border=0)
    pdf.cell(50, 8, txt="Date", border=1, fill=True, align="C")
    pdf.cell(50, 8, txt="Business", border=1, fill=True, align="C")
    pdf.cell(35, 8, txt="Total", border=1, fill=True, align="C")
    pdf.ln()
    pair = 0
    currency = dict_responses["currency"]
        
    for row in rows:
        pdf.cell(30, 7, border=0)
        if(pair%2==0):
            pdf.set_fill_color(255, 255, 255)
        else:
            pdf.set_fill_color(192, 192, 192)

        pdf.cell(50, 7, txt=f"{row[0]}", border=1, fill=True)
        pdf.cell(50, 7, txt=row[2], border=1, fill=True)

        if(currency == "LL - Lebanese pound"):
            pdf.cell(35, 7, txt=f"{row[1]} LL", border=1, fill=True)
        else:
            tmp = row[1]
            tmp*= usd_rates
            pdf.cell(35, 7, txt=f"$ {round(tmp)}", border=1, fill=True)

        pdf.ln()
        pair+=1
    
    pdf.cell(30, 7, border=0)
    pdf.cell(50, 7, txt="", border=1)
    pdf.cell(50, 7, txt="", border=1)
    if(currency == "LL - Lebanese pound"):
        total = int(float(total[0][0]))
        pdf.cell(35, 7, txt=f"{total} LL", border=1)
    else:
        total = float(total[0][0])
        total *= usd_rates
        pdf.cell(35, 7, txt=f"$ {round(total)}", border=1)
    
    pdf.ln()
    pdf.ln()
    pdf.set_font("Times", size=12)
    pdf.cell(200, 5, txt = "Expenses since " + str(dict_responses['date']) + ".", ln = 1, align = 'C')

    pdf.output(PDF_FILENAME)