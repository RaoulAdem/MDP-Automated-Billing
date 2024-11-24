import unittest
from unittest.mock import patch, Mock, mock_open
import os
import ast
from paddleocrtesting import (
    remove_return_file,
    is_valid_input,
    normalize_price,
    parse_items,
    process_bill,
    OCR_OUTPUT_FILE
)


class TestUtilityFunctions(unittest.TestCase):
    @patch("os.path.exists", return_value=True)
    @patch("os.remove")
    def test_remove_return_file(self, mock_remove, mock_exists):
        """Test removing the OCR return file."""
        remove_return_file()
        mock_remove.assert_called_once_with(OCR_OUTPUT_FILE)

    def test_is_valid_input(self):
        """Test validating input values."""
        self.assertTrue(is_valid_input("valid_input"))
        self.assertFalse(is_valid_input(None))
        self.assertFalse(is_valid_input("0"))


class TestNormalizePrice(unittest.TestCase):
    def test_normalize_price(self):
        """Test normalizing prices."""
        self.assertEqual(normalize_price("$10", 1500), "15000")
        self.assertEqual(normalize_price("15.5", 1500), "23250")
        self.assertEqual(normalize_price("O20", 1500), "30000")
        self.assertEqual(normalize_price("", 1500), "0")


class TestParseItems(unittest.TestCase):
    def test_parse_items_valid(self):
        """Test parsing valid items."""
        items_text = "[['1', 'Burger', '$10'], ['2', 'Fries', '15000']]"
        parsed, total = parse_items(items_text, 1500)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(total, 18000)

    def test_parse_items_invalid(self):
        """Test parsing invalid items."""
        items_text = "[['1', 'Burger'], ['Fries', '15000']]"
        parsed, total = parse_items(items_text, 1500)
        self.assertEqual(parsed, [])
        self.assertEqual(total, 0)


class TestProcessBill(unittest.TestCase):
    @patch("requests.get")
    @patch("your_module.chat.send_message")
    @patch("your_module.ocr.ocr")
    @patch("builtins.open", new_callable=mock_open)
    def test_process_bill(self, mock_open_file, mock_ocr, mock_chat, mock_get):
        """Test processing the bill."""
        # Mock exchange rate API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"conversion_rates": {"LBP": 1500}}

        # Mock OCR results
        mock_ocr.return_value = [
            [[[0, 0], [0, 1]], [[1, 1], [1, 2]], [0.9, "Sample Item"]]
        ]

        # Mock chat responses
        mock_chat.side_effect = [
            Mock(text="Business Name"),  # Business name
            Mock(text="Restaurant"),    # Category
            Mock(text="2024/01/01"),    # Date
            Mock(text="12345"),         # Check ID
            Mock(
                text=str([["1", "Burger", "$10"], ["2", "Fries", "15000"]])
            ),  # Items
        ]

        # Run the process_bill function
        data = process_bill("test_img_path", mock_chat, mock_ocr)

        # Assertions
        self.assertEqual(data["business_name"], "Business Name")
        self.assertEqual(data["category"], "Restaurant")
        self.assertEqual(data["date"], "2024/01/01")
        self.assertEqual(data["check_id"], "12345")
        self.assertEqual(data["total"], 18000)

        # Ensure file writing
        mock_open_file().write.assert_called()


if __name__ == "__main__":
    unittest.main()