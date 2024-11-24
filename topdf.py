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

def create_pdf_header(pdf, dict_responses):
    """Create the header for the PDF."""
    pdf.image("logo.png", x=10, y=10, w=50)
    pdf.set_font("Times", size=20, style='B')
    pdf.cell(200, 10, txt="Automated Billing Archive & Recognition", ln=1, align='R')
    pdf.set_font("Times", size=12)
    pdf.cell(200, 5, txt="Date: " + str(datetime.datetime.now().date()), ln=1, align='R')
    pdf.cell(200, 5, txt="Category: " + str(dict_responses.get("category", "N/A")), ln=1, align='R')
    pdf.cell(200, 5, txt="Currency: " + str(dict_responses.get("currency", "N/A")), ln=1, align='R')


async def to_pdf(total,rows,dict_responses):
    #Fetch exchange rates
    lbp_rates = fetch_exchange_rate(LBP_URL)  #returns dictionary
    usd_rates = fetch_exchange_rate(USD_URL)  #returns dictionary
    if not lbp_rates or not usd_rates:
        print("Error fetching exchange rates. Cannot generate PDF.")
        return
    #Extract specific rates
    lbp_to_usd_rate = lbp_rates.get('USD', 1)  #fallback to 1 if not found
    usd_to_lbp_rate = usd_rates.get('LBP', 1)  #fallback to 1 if not found
    #Validate fetched rates
    if not lbp_to_usd_rate or not usd_to_lbp_rate:
        print("Invalid exchange rates retrieved.")
        return
    currency = dict_responses["currency"]

    #Create PDF and add header
    pdf = FPDF()
    pdf.add_page()
    create_pdf_header(pdf, dict_responses)

    #Add report section
    pdf.ln()
    pdf.set_font("Times", size=15, style='B')
    pdf.cell(200, 8, txt="Report", ln=1, align='C')
    pdf.set_font("Times", size=12)
    pdf.cell(200, 5, txt=f"Exchange rate: {int(usd_to_lbp_rate)} LL", ln=1, align='C')

    #Add table headers
    pdf.ln()
    pdf.set_font("Times", size=10)
    pdf.set_fill_color(169, 169, 169)
    pdf.cell(30, 8, border=0)
    pdf.cell(50, 8, txt="Date", border=1, fill=True, align="C")
    pdf.cell(50, 8, txt="Business", border=1, fill=True, align="C")
    pdf.cell(35, 8, txt="Total", border=1, fill=True, align="C")
    pdf.ln()

    #Add table rows
    for i, row in enumerate(rows):
        pdf.cell(30, 7, border=0)
        pdf.set_fill_color(255, 255, 255) if i % 2 == 0 else pdf.set_fill_color(192, 192, 192)
        pdf.cell(50, 7, txt=row[0], border=1, fill=True)
        pdf.cell(50, 7, txt=row[2], border=1, fill=True)
        amount = row[1] * lbp_to_usd_rate if currency != "LL - Lebanese pound" else row[1]
        pdf.cell(35, 7, txt=f"{amount:.2f} {currency}", border=1, fill=True)
        pdf.ln()

    #Add total row
    pdf.cell(30, 7, border=0)
    pdf.cell(50, 7, txt="", border=1)
    pdf.cell(50, 7, txt="", border=1)
    total_amount = total[0][0] * lbp_to_usd_rate if currency != "LL - Lebanese pound" else total[0][0]
    pdf.cell(35, 7, txt=f"{total_amount:.2f} {currency}", border=1)
    
    #Footer
    pdf.ln()
    pdf.ln()
    pdf.set_font("Times", size=12)
    pdf.cell(200, 5, txt=f"Expenses since {dict_responses['date']}.", ln=1, align='C')
    
    #Output PDF
    pdf.output(PDF_FILENAME)