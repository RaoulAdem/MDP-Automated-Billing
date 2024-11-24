import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import mysql.connector
from base64 import b64encode
import os
from datetime import datetime

# Import the modules to test
from langchain1 import get_response, is_query, handle_conv
from sqlinsert import is_present, insert_data, get_bill_data, get_bill_image
from main2 import handle_photos, bot_reply, start_command, help_command, pdf_command

class TestLangChain(unittest.TestCase):
    def setUp(self):
        self.mock_db = Mock()
        self.mock_db.get_table_info.return_value = "mock_schema"
        
    @patch('langchain1.ChatGroq')
    def test_is_query(self, mock_llm):
        # Setup
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = "0"
        mock_llm.return_value = mock_llm_instance
        
        # Test database query
        result = is_query("how much have i spent?")
        self.assertEqual(result, "0")
        
        # Test conversation query
        mock_llm_instance.invoke.return_value = "1"
        result = is_query("hello")
        self.assertEqual(result, "1")
        
    @patch('langchain1.ChatGroq')
    def test_handle_conv(self, mock_llm):
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = "Hello! How can I help you?"
        mock_llm.return_value = mock_llm_instance
        
        response, flag = handle_conv("hi")
        self.assertEqual(flag, 1)
        self.assertIsInstance(response, str)

class TestSQLInsert(unittest.TestCase):
    def setUp(self):
        self.test_data = {
            "total": 100,
            "category": "Restaurant",
            "business_name": "Test Restaurant",
            "date": "2024-03-25",
            "check_id": "12345",
            "item1": {
                "name": "Test Item",
                "price": 50,
                "quantity": 2
            }
        }
        
    @patch('mysql.connector.connect')
    def test_is_present(self, mock_connect):
        # Setup mock
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Write test data to temporary JSON file
        with open('ocr_return.json', 'w') as f:
            json.dump(self.test_data, f)
            
        # Test when bill is not present
        result = is_present(1)
        self.assertFalse(result)
        
        # Test when bill is present
        mock_cursor.fetchone.return_value = ("Test Restaurant", "2024-03-25", "12345")
        result = is_present(1)
        self.assertTrue(result)
        
        # Cleanup
        if os.path.exists('ocr_return.json'):
            os.remove('ocr_return.json')
            
    @patch('mysql.connector.connect')
    def test_get_bill_data(self, mock_connect):
        # Setup mock
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("2024-03-25", 100, "Test Restaurant")
        ]
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Test get_bill_data
        rows, total = get_bill_data(1, "Restaurant", "2024-03-25")
        self.assertIsNotNone(rows)
        self.assertIsNotNone(total)

class TestTelegramBot(unittest.TestCase):
    def setUp(self):
        self.update = Mock()
        self.context = Mock()
        
    async def test_start_command(self):
        self.update.message.reply_text = AsyncMock()
        await start_command(self.update, self.context)
        self.update.message.reply_text.assert_called_once()
        
    async def test_help_command(self):
        self.update.message.reply_text = AsyncMock()
        await help_command(self.update, self.context)
        self.update.message.reply_text.assert_called_once()
        
    @patch('main2.process_bill')
    async def test_handle_photos(self, mock_process_bill):
        # Setup
        self.update.message.photo = [Mock(file_id="test_id", file_unique_id="test_unique_id")]
        self.update.message.from_user.id = 1
        self.context.bot.get_file = AsyncMock()
        self.context.bot.send_message = AsyncMock()
        
        # Mock process_bill return
        mock_process_bill.return_value = self.test_data
        
        # Test
        await handle_photos(self.update, self.context)
        self.context.bot.send_message.assert_called()

# Helper class for async mocks
class AsyncMock(Mock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)

if __name__ == '__main__':
    unittest.main()