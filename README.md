# MDP-Automated-Billing
Automated Billing Bot (@Automated_billing_bot)
Automated Billing Bot is a Telegram chatbot designed to help users track and manage their expenses seamlessly. Users can submit photos of their bills, and the bot will perform Optical Character Recognition (OCR) to extract relevant expense details, which it then stores in a database. With this bot, users can easily monitor their spending patterns and receive detailed summaries or answers to queries about their spending history.

Features
Expense Tracking via Image Recognition: Submit a picture of a bill, and the bot will extract and store the expense details.
Database Storage: Stores extracted data in a database for easy retrieval and analysis.
Spendings Inquiry: Users can ask the bot about their past spendings, and it will generate detailed responses based on the data in the database.
Detailed Reports: Provides summaries and insights on user spending, including total expenses over time, spending patterns, and breakdowns by category.
Technologies Used
Python: Core language for the bot functionality.
Telegram Bot API: Integrates with Telegram to provide an accessible chatbot interface.
OCR Library: Used to process images and extract text from bills (e.g., Tesseract OCR).
Database: Stores user data, expense records, and other relevant information (e.g., SQLite, PostgreSQL).
