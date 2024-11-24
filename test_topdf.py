import unittest
from unittest.mock import patch, Mock
from fpdf import FPDF
import asyncio
import topdf
import requests

class TestPDFGenerator(unittest.TestCase):

    def test_fetch_exchange_rate_valid_url(self):
        """Test fetching exchange rates with a valid URL."""
        with patch('requests.get') as mocked_get:
            mocked_get.return_value = Mock(
                status_code=200,
                json=lambda: {"conversion_rates": {"USD": 1.5, "LBP": 1500}}
            )
            rates = topdf.fetch_exchange_rate("http://valid-url.com")
            self.assertEqual(rates["USD"], 1.5)
            self.assertEqual(rates["LBP"], 1500)

    def test_fetch_exchange_rate_invalid_url(self):
        """Test fetching exchange rates with an invalid URL."""
        with patch('requests.get') as mocked_get:
            mocked_get.side_effect = requests.RequestException("Network error")
            rates = topdf.fetch_exchange_rate("http://invalid-url.com")
            self.assertIsNone(rates)

    def test_create_pdf_header(self):
        """Test PDF header creation."""
        pdf = FPDF()
        dict_responses = {
            "category": "Food",
            "currency": "USD",
            "date": "2024-01-01"
        }
        pdf.add_page()
        topdf.create_pdf_header(pdf, dict_responses)
        self.assertTrue(pdf.page_no() > 0)  #Verify a page was added

    def test_add_pdf_table(self):
        """Test adding a table to the PDF."""
        pdf = FPDF()
        rows = [["2024-01-01", 100, "Groceries"], ["2024-01-02", 200, "Transport"]]
        exchange_rate = 1.5
        currency = "USD"
        total = [[300]]

        pdf.add_page()
        topdf.add_pdf_table(pdf, rows, exchange_rate, currency, total)
        self.assertTrue(pdf.page_no() > 0)

    @patch("topdf.fetch_exchange_rate")
    @patch("topdf.FPDF.output")
    def test_to_pdf(self, mocked_output, mocked_fetch_exchange_rate):
        """Test the full PDF generation process."""
        mocked_fetch_exchange_rate.side_effect = [
            {"USD": 1.5},  #LBP to USD
            {"LBP": 1500}  #USD to LBP
        ]
        total = [[300]]
        rows = [["2024-01-01", 100, "Groceries"], ["2024-01-02", 200, "Transport"]]
        dict_responses = {
            "category": "Food",
            "currency": "USD",
            "date": "2024-01-01"
        }

        #Run the coroutine
        asyncio.run(topdf.to_pdf(total, rows, dict_responses))

        #Verify output was called
        mocked_output.assert_called_once_with(topdf.PDF_FILENAME)

if __name__ == '__main__':
    unittest.main()
