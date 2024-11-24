import unittest
from unittest.mock import patch, mock_open, Mock
import os
import ast
import requests
from paddleocrtesting import remove_return_file, is_valid_input

# Constants
OCR_OUTPUT_FILE = 'ocr_return.json'


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


if __name__ == "__main__":
    unittest.main()