# Student Finance Manager

**Student Finance Manager** is a desktop application built with Python using `tkinter`, `sqlite3`, and `matplotlib`. It helps students track their income and expenses, visualize their spending habits, and maintain better control of their finances.

---

## Features

- **User Authentication**
  - Login and Sign Up functionality with unique usernames
- **Transaction Management**
  - Add, update, delete, and search financial transactions
  - Categorize transactions as either "Income" or "Expense"
- **Summary**
  - Displays total income, expenses, and current balance
- **Charts and Graphs**
  - View pie charts for income and expense categories
  - View a line graph for balance history (weekly, monthly, yearly)
- **Data Export**
  - Export all transaction data to a CSV file
- **Polished UI**
  - Clean interface using `ttk`, styled with Segoe UI and modern widgets
  - Includes a custom logo image (`SafeSpend_Logo.png`)

---

## Technologies Used

- **Python 3.x**
- **Tkinter**: For the GUI
- **SQLite3**: For local database storage
- **Matplotlib**: For generating financial charts
- **Pillow**: For logo image processing
- **Seaborn**: Theme enhancement for matplotlib charts

---

## Installation

1. Clone this repository or download the source code.
2. Make sure the following Python packages are installed:
   ```bash
   pip3 install matplotlib pillow seaborn
