import sqlite3
import csv
from datetime import datetime, timedelta
from collections import defaultdict
from PIL import Image, ImageTk

import matplotlib
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
matplotlib.use('TkAgg')

import tkinter as tk
from tkinter import ttk, messagebox, StringVar, filedialog

import seaborn as sns
sns.set_theme(style="whitegrid", palette="deep")



# Initialize database
conn = sqlite3.connect('finance.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                type TEXT,
                amount REAL,
                category TEXT,
                date TEXT,
                note TEXT,
                user_id INTEGER
            )''')
conn.commit()

class LoginWindow:
    def __init__(self, root, on_success):
        self.root = root
        self.root.title("Student Finance Manager - Login / Sign Up")
        self.root.geometry("400x400")
        self.root.resizable(False, False)
        self.on_success = on_success
        
        # --- Logo & Title Section ---
        # Load the logo image
        logo_image = Image.open("SafeSpend_Logo.png")  # Make sure this matches the actual file name
        logo_image = logo_image.resize((120, 120), Image.ANTIALIAS)  # Resize as needed
        logo_photo = ImageTk.PhotoImage(logo_image)

        # Create a container frame for branding
        branding_frame = tk.Frame(self.root, bg="white")
        branding_frame.pack(pady=15)

        # Display the logo
        logo_label = tk.Label(branding_frame, image=logo_photo, bg="white")
        logo_label.image = logo_photo  # Keep reference
        logo_label.pack()

        style = ttk.Style()
        style.configure("TButton", font=('Segoe UI', 13))
        style.configure("TLabel", font=('Segoe UI', 13))
        style.configure("TEntry", font=('Segoe UI', 13))

        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both', padx=20, pady=20)

        login_frame = ttk.Frame(notebook)
        notebook.add(login_frame, text="Login")

        ttk.Label(login_frame, text="Username:").grid(row=0, column=0, padx=10, pady=(20, 5), sticky="e")
        self.login_username = ttk.Entry(login_frame, width=23)
        self.login_username.grid(row=0, column=1, pady=(20, 5))

        ttk.Label(login_frame, text="Password:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.login_password = ttk.Entry(login_frame, width=23, show="*")
        self.login_password.grid(row=1, column=1, pady=5)

        ttk.Button(login_frame, text="Login", command=self.login).grid(row=2, column=1, padx=10, pady=20, sticky="w")

        signup_frame = ttk.Frame(notebook)
        notebook.add(signup_frame, text="Sign Up")

        ttk.Label(signup_frame, text="Username:").grid(row=0, column=0, padx=10, pady=(20, 5), sticky="e")
        self.signup_username = ttk.Entry(signup_frame, width=23)
        self.signup_username.grid(row=0, column=1, pady=(20, 5))

        ttk.Label(signup_frame, text="Password:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.signup_password = ttk.Entry(signup_frame, width=23, show="*")
        self.signup_password.grid(row=1, column=1, pady=5)

        ttk.Button(signup_frame, text="Sign Up", command=self.signup).grid(row=2, column=1, padx=10, pady=20, sticky="w")

        for frame in [login_frame, signup_frame]:
            frame.columnconfigure(0, weight=1)
            frame.columnconfigure(1, weight=2)

    def login(self):
        with sqlite3.connect('finance.db') as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE username=? AND password=?", (self.login_username.get(), self.login_password.get()))
            result = c.fetchone()
        if result:
            self.root.withdraw()
            self.launch_finance_app(result[0])
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def signup(self):
        with sqlite3.connect('finance.db') as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (self.signup_username.get(), self.signup_password.get()))
                conn.commit()
                messagebox.showinfo("Success", "Account created! You can now log in.")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists.")
    
    def launch_finance_app(self, user_id):
        finance_window = tk.Toplevel(self.root)
        finance_window.protocol("WM_DELETE_WINDOW", lambda: self.logout(finance_window))  # Optional: handle X button
        FinanceApp(finance_window, user_id, logout_callback=lambda: self.logout(finance_window))
        self.root.withdraw()  # Hide login window

    def logout(self, finance_window):
        finance_window.destroy()
        self.root.deiconify()  # Show login window again

class FinanceApp:
    def __init__(self, root, user_id, logout_callback=None):
        self.root = root
        self.user_id = user_id
        self.logout_callback = logout_callback
        self.root.title("Student Finance Manager")
        self.create_widgets()
        self.refresh_data()

    def create_widgets(self):
        # Top Entry Frame
        entry_frame = ttk.LabelFrame(self.root, text="Add Transaction")
        entry_frame.pack(fill="x", padx=10, pady=5)
        
        self.type_var = tk.StringVar(value="Income")
        self.amount_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.note_var = tk.StringVar()

        income_categories = ["Salary", "Scholarship", "Gift", "Other"]
        expense_categories = ["Food", "Transport", "Rent", "Utilities", "Entertainment", "Other"]

        self.category_options = {
            "Income": income_categories,
            "Expense": expense_categories
        }

        ttk.Radiobutton(entry_frame, text="Income", variable=self.type_var, value="Income", command=self.update_category_menu).grid(row=0, column=0)
        ttk.Radiobutton(entry_frame, text="Expense", variable=self.type_var, value="Expense", command=self.update_category_menu).grid(row=0, column=1)

        ttk.Label(entry_frame, text="Amount:").grid(row=1, column=0, padx=5, pady=2)
        ttk.Entry(entry_frame, textvariable=self.amount_var, width=10).grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(entry_frame, text="Category:").grid(row=1, column=2, padx=5, pady=2)
        self.category_menu = ttk.Combobox(entry_frame, textvariable=self.category_var, values=self.category_options[self.type_var.get()], width=15)
        self.category_menu.grid(row=1, column=3, padx=5, pady=2)

        ttk.Label(entry_frame, text="Date (YYYY-MM-DD):", font=(13)).grid(row=1, column=4, padx=5, pady=2)
        ttk.Entry(entry_frame, textvariable=self.date_var, width=12).grid(row=1, column=5, padx=5, pady=2)

        ttk.Label(entry_frame, text="Note:").grid(row=1, column=6, padx=5, pady=2)
        ttk.Entry(entry_frame, textvariable=self.note_var, width=20).grid(row=1, column=7, padx=5, pady=2)

        ttk.Button(entry_frame, text="Add", command=self.add_transaction).grid(row=1, column=8, padx=5)

        # Search and Filter Frame
        filter_frame = ttk.LabelFrame(self.root, text="Search/Filter")
        filter_frame.pack(fill="x", padx=10, pady=5)

        self.search_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.search_var, width=20).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Search", command=self.search_transaction).pack(side="left")
        ttk.Button(filter_frame, text="Reset", command=self.refresh_data).pack(side="left")

        # Treeview for transactions
        self.tree = ttk.Treeview(self.root, columns=("Type", "Amount", "Category", "Date", "Note"), show="headings")
        for col in self.tree['columns']:
            self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        # Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(button_frame, text="Delete Selected", command=self.delete_transaction).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Update Selected", command=self.load_selected_transaction).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Log Out", command=self.logout).grid(row=0, column=2, padx=175)
        ttk.Button(button_frame, text="Export to CSV", command=self.export_to_csv).grid(row=0, column=3, padx=5)
        
        # Dropdown Menu for Charts
        chart_menu_btn = ttk.Menubutton(button_frame, text="Show Charts")
        chart_menu = tk.Menu(chart_menu_btn, tearoff=0)
        chart_menu.add_command(label="Balance History", command=self.show_balance_chart)
        chart_menu.add_command(label="Expense Categories", command=self.show_expense_chart)
        chart_menu.add_command(label="Income Categories", command=self.show_income_chart)
        chart_menu_btn["menu"] = chart_menu

        # Grid layout to simulate right alignment
        chart_menu_btn.grid(row=0, column=4, sticky="e", padx=5)
        button_frame.columnconfigure(4, weight=1)
        ttk.Button(button_frame, text="Summary", command=self.show_summary).grid(row=0, column=5, padx=5)
       



    def update_category_menu(self):
        current_type = self.type_var.get()
        self.category_menu["values"] = self.category_options[current_type]
        if self.category_options[current_type]:
            self.category_menu.current(0)

    def load_selected_transaction(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a transaction to update.")
            return
        item_id = selected[0]
        values = self.tree.item(item_id, "values")
        
        self.type_var.set(values[0])
        self.amount_var.set(values[1])
        self.category_var.set(values[2])
        self.date_var.set(values[3])
        self.note_var.set(values[4])
        self.update_category_menu()

        # Change Add button to Update mode
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.LabelFrame) and "Add Transaction" in widget.cget("text"):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button) and child.cget("text") == "Add":
                        child.config(text="Update", command=lambda: self.update_transaction(item_id))
                        
    def update_transaction(self, item_id):
        try:
            amount = float(self.amount_var.get())
            with sqlite3.connect("finance.db") as conn:
                c = conn.cursor()
                c.execute("""
                    UPDATE transactions 
                    SET type=?, amount=?, category=?, date=?, note=?
                    WHERE id=?
                """, (
                    self.type_var.get(), amount, self.category_var.get(),
                    self.date_var.get(), self.note_var.get(), item_id
                ))
                conn.commit()
            self.refresh_data()

            # Reset the Add button
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.LabelFrame) and "Add Transaction" in widget.cget("text"):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Button) and child.cget("text") == "Update":
                            child.config(text="Add", command=self.add_transaction)

            # Clear fields
            self.amount_var.set("")
            self.category_var.set("")
            self.note_var.set("")
            self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
            self.update_category_menu()

        except ValueError:
            messagebox.showerror("Invalid Input", "Amount must be a number.")


    def add_transaction(self):
        try:
            amount = float(self.amount_var.get())
            with sqlite3.connect("finance.db") as conn:
                c = conn.cursor()
                c.execute("INSERT INTO transactions (type, amount, category, date, note, user_id) VALUES (?, ?, ?, ?, ?, ?)",
                          (self.type_var.get(), amount, self.category_var.get(), self.date_var.get(), self.note_var.get(), self.user_id))
                conn.commit()
            self.refresh_data()
        except ValueError:
            messagebox.showerror("Invalid Input", "Amount must be a number.")

    def refresh_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        with sqlite3.connect("finance.db") as conn:
            c = conn.cursor()
            for row in c.execute("SELECT * FROM transactions WHERE user_id = ?", (self.user_id,)):
                self.tree.insert("", "end", iid=row[0], values=row[1:-1])

    def delete_transaction(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a transaction to delete.")
            return
        with sqlite3.connect("finance.db") as conn:
            c = conn.cursor()
            for item_id in selected:
                c.execute("DELETE FROM transactions WHERE id = ?", (item_id,))
            conn.commit()
        self.refresh_data()

    def search_transaction(self):
        query = self.search_var.get().lower()
        for row in self.tree.get_children():
            self.tree.delete(row)
        with sqlite3.connect("finance.db") as conn:
            c = conn.cursor()
            for row in c.execute("SELECT * FROM transactions WHERE user_id = ?", (self.user_id,)):
                if query in str(row).lower():
                    self.tree.insert("", "end", iid=row[0], values=row[1:-1])

    def show_summary(self):
        with sqlite3.connect("finance.db") as conn:
            c = conn.cursor()
            c.execute("SELECT type, SUM(amount) FROM transactions WHERE user_id = ? GROUP BY type", (self.user_id,))
            results = c.fetchall()
        summary = ""
        total_balance = 0
        for t_type, total in results:
            summary += f"{t_type}: ${total:.2f}\n"
            if t_type == "Income":
                total_balance += total
            else:
                total_balance -= total
        summary += f"\nCurrent Balance: ${total_balance:.2f}"
        messagebox.showinfo("Summary", summary)

    def show_expense_chart(self):

        with sqlite3.connect("finance.db") as conn:
            c = conn.cursor()
            c.execute("SELECT category, SUM(amount) FROM transactions WHERE type = 'Expense' AND user_id = ? GROUP BY category", (self.user_id,))
            data = c.fetchall()
        if not data:
            messagebox.showinfo("No Data", "No expense data available to display chart.")
            return
        
        chart_window = tk.Toplevel(self.root)
        chart_window.title("Expenses by Category")
        
        categories = [row[0] for row in data]
        amounts = [row[1] for row in data]

        fig, ax = plt.subplots(figsize=(6, 5), facecolor='#f5f5f5')
        wedges, texts, autotexts = ax.pie(amounts, labels=categories, autopct='%1.1f%%',
                                          startangle=140, shadow=True)
        for text in texts + autotexts:
            text.set_fontsize(10)

        ax.set_title("Expenses by Category", fontsize=14, fontweight='bold')
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chart_window)
        canvas.draw()
        canvas.get_tk_widget().pack()
        plt.close(fig)

    def show_income_chart(self):
        
        with sqlite3.connect("finance.db") as conn:
            c = conn.cursor()
            c.execute("SELECT category, SUM(amount) FROM transactions WHERE type = 'Income' AND user_id = ? GROUP BY category", (self.user_id,))
            data = c.fetchall()
        if not data:
            messagebox.showinfo("No Data", "No income data available to display chart.")
            return
        
        chart_window = tk.Toplevel(self.root)
        chart_window.title("Income by Category")

        categories = [row[0] for row in data]
        amounts = [row[1] for row in data]

        fig, ax = plt.subplots(figsize=(6, 5), facecolor='#f5f5f5')
        wedges, texts, autotexts = ax.pie(amounts, labels=categories, autopct='%1.1f%%',
                                          startangle=140, shadow=True)
        for text in texts + autotexts:
            text.set_fontsize(10)

        ax.set_title("Income by Category", fontsize=14, fontweight='bold')
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chart_window)
        canvas.draw()
        canvas.get_tk_widget().pack()
        plt.close(fig)

    def show_balance_chart(self):
        chart_window = tk.Toplevel(self.root)
        chart_window.title("Balance History")
        chart_window.resizable(True, True)
        self.current_chart_canvas = None

        # Time range selection
        period_var = StringVar(value="Month")
        ttk.Label(chart_window, text="Group by:").pack()
        period_menu = ttk.Combobox(chart_window, textvariable=period_var, values=["Week", "Month", "Year"], state="readonly")
        period_menu.pack()

        def update_chart():
            # Remove previous chart if it exists
            if self.current_chart_canvas is not None:
                self.current_chart_canvas.get_tk_widget().destroy()
                self.current_chart_canvas = None

            with sqlite3.connect("finance.db") as conn:
                c = conn.cursor()
                c.execute("SELECT date, type, amount FROM transactions WHERE user_id = ? ORDER BY date", (self.user_id,))
                rows = c.fetchall()

            period = period_var.get()
            today = datetime.today()

            if period == "Week":
                cutoff_date = today - timedelta(weeks=13)
            elif period == "Month":
                cutoff_date = today - timedelta(days=365)
            else:
                cutoff_date = None

            if cutoff_date:
                rows = [row for row in rows if datetime.strptime(row[0], "%Y-%m-%d") >= cutoff_date]

            grouped = defaultdict(float)

            for date_str, t_type, amount in rows:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                if period_var.get() == "Week":
                    key = f"{dt.year}-W{dt.isocalendar()[1]}"
                elif period_var.get() == "Month":
                    key = dt.strftime("%Y-%m")
                elif period_var.get() == "Year":
                    key = dt.strftime("%Y")

                if t_type == "Income":
                    grouped[key] += amount
                else:
                    grouped[key] -= amount

            # Sort keys chronologically
            def parse_key(k):
                if "-W" in k:
                    year, week = k.split("-W")
                    return datetime.strptime(f"{year} {week} 1", "%Y %W %w")  # Monday of that ISO week
                elif "-" in k:
                    return datetime.strptime(k, "%Y-%m")  # Monthly
                else:
                    return datetime.strptime(k, "%Y")     # Yearly

            sorted_keys = sorted(grouped.keys(), key=parse_key)


            balances = []
            dates = []
            running_total = 0
            for key in sorted_keys:
                running_total += grouped[key]
                dates.append(key)
                balances.append(running_total)

            fig, ax = plt.subplots(figsize=(7, 5), facecolor='#f5f5f5')
            ax.plot(dates, balances, marker='o', color='teal', linestyle='-', linewidth=2)
            
            if period_var.get()=="Week":
                ax.set_title(f"Balance History - Last 3 Months", fontsize=14, fontweight='bold')
            elif period_var.get()=="Month":
                ax.set_title(f"Balance History - Past Year", fontsize=14, fontweight='bold')
            else:
                ax.set_title(f"Balance History - All Time", fontsize=14, fontweight='bold')
                
            ax.set_xlabel("Date", fontsize=12)
            ax.set_ylabel("Balance ($)", fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.6)
            
            # Format the x-axis labels for weekly and monthly views
            if period in ["Week", "Month"]:
                # Convert string keys to datetime objects for formatting
                date_labels = [datetime.strptime(k + "-1", "%Y-W%W-%w") if "W" in k else datetime.strptime(k + "-01", "%Y-%m-%d") for k in sorted_keys]

                # Apply new labels in "Jan 08" format
                ax.set_xticks(range(len(date_labels)))
                ax.set_xticklabels([d.strftime("%b %d") for d in date_labels])
    
            fig.autofmt_xdate()
            fig.tight_layout()
            
            # Create and show the new chart
            self.current_chart_canvas = FigureCanvasTkAgg(fig, master=chart_window)
            self.current_chart_canvas.draw()
            self.current_chart_canvas.get_tk_widget().pack(expand=True, fill='both')

        period_menu.bind("<<ComboboxSelected>>", lambda e: update_chart())
        update_chart()

    def export_to_csv(self):
        if not self.transactions:
            messagebox.showinfo("Export", "No transactions to export.")
            return

        # Prompt user for file location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save Transactions As"
        )

        if file_path:
            try:
                with open(file_path, mode="w", newline="") as file:
                    writer = csv.writer(file)
                    # Write headers
                    writer.writerow(["Date", "Category", "Amount", "Description"])
                    # Write each transaction
                    for txn in self.transactions:
                        writer.writerow([
                            txn["date"],
                            txn["category"],
                            txn["amount"],
                            txn["description"]
                        ])
                messagebox.showinfo("Export", f"Transactions exported successfully to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {e}")
                
    def export_to_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv")],
                                                 title="Save as")
        if not file_path:
            return

        with sqlite3.connect("finance.db") as conn:
            c = conn.cursor()
            c.execute("SELECT type, amount, category, date, note FROM transactions WHERE user_id = ?", (self.user_id,))
            transactions = c.fetchall()

        try:
            with open(file_path, "w", newline='', encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Type", "Amount", "Category", "Date", "Note"])
                writer.writerows(transactions)
            messagebox.showinfo("Success", f"Data exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV:\n{e}")
            
    def logout(self):
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to log out?"):
            if self.logout_callback:
                self.logout_callback()



if __name__ == "__main__":
    def start_app(user_id):
        app_window = tk.Toplevel()
        FinanceApp(app_window, user_id)

    login_root = tk.Tk()
    login_window = LoginWindow(login_root, start_app)
    login_root.mainloop()

