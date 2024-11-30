import unittest
from unittest.mock import patch, Mock, mock_open, MagicMock
from paddleocrtesting import (
    remove_return_file,
    is_valid_input,
    normalize_price,
    parse_items,
    parse_ocr_result,
    get_invoice_details,
    process_bill,
    OCR_OUTPUT_FILE,
)


class TestUtilityFunctions(unittest.TestCase):
    @patch("os.path.exists", return_value=True)
    @patch("os.remove")
    def test_remove_return_file(self, mock_remove, mock_exists):
        """Test removing the OCR output file."""
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
        self.assertEqual(normalize_price("15000", 1500), "15000")


class TestItemParsing(unittest.TestCase):
    def test_parse_items(self):
        """Test parsing items into structured format."""
        items_text = "[['1', 'Burger', '$10'], ['2', 'Fries', '15000']]"
        parsed_items, total = parse_items(items_text, 1500)
        self.assertEqual(parsed_items[0]["price"], "15000")
        self.assertEqual(parsed_items[1]["price"], "15000")
        self.assertEqual(total, 30000)


class TestOCRParsing(unittest.TestCase):
    def test_parse_ocr_result(self):
        """Test parsing OCR result."""
        ocr_result = [
            [[[0, 1], [1, 2]], [0.9, "Sample Item"]],
            [[[0, 1], [1, 2]], [0.7, "Low Precision"]],
        ]
        parsed_result = parse_ocr_result(ocr_result)
        self.assertIn("1", parsed_result)
        self.assertNotIn("2", parsed_result)


class TestChatHandling(unittest.TestCase):
    def test_get_invoice_details(self):
        """Test getting invoice details from the user."""
        mock_chat = MagicMock()
        mock_chat.send_message.side_effect = [
            Mock(text="Business Name"),
            Mock(text="Restaurant"),
            Mock(text="2024/01/01"),
            Mock(text="12345"),
        ]
        data = {}
        res = "Test OCR Content"
        result = get_invoice_details(mock_chat, res, data)
        self.assertEqual(result["business_name"], "Business Name")
        self.assertEqual(result["category"], "Restaurant")


if __name__ == "__main__":
    unittest.main()