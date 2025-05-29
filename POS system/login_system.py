import sqlite3
import hashlib
import tkinter as tk
from tkinter import messagebox

# Connect to SQLite database
conn = sqlite3.connect('pos_system.db')
c = conn.cursor()

# ------------------------------
# Database setup
# ------------------------------
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'cashier'))
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL
)
''')

conn.commit()

# ------------------------------
# Utility functions
# ------------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password, role):
    try:
        password_hash = hash_password(password)
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                  (username, password_hash, role))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"User '{username}' already exists.")

def check_login(username, password):
    password_hash = hash_password(password)
    c.execute("SELECT role FROM users WHERE username = ? AND password_hash = ?", (username, password_hash))
    result = c.fetchone()
    return result[0] if result else None

# ------------------------------
# Login Screen
# ------------------------------
class LoginApp:
    def __init__(self, master):
        self.master = master
        master.title("POS System - Login")
        master.geometry("300x180")

        self.label1 = tk.Label(master, text="Username:")
        self.label1.pack(pady=5)
        self.entry_username = tk.Entry(master)
        self.entry_username.pack()

        self.label2 = tk.Label(master, text="Password:")
        self.label2.pack(pady=5)
        self.entry_password = tk.Entry(master, show="*")
        self.entry_password.pack()

        self.btn_login = tk.Button(master, text="Login", command=self.login)
        self.btn_login.pack(pady=10)

        # Create default admin on first run
        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            add_user("admin", "admin123", "admin")
            messagebox.showinfo("Setup", "Default admin created:\nUsername: admin\nPassword: admin123")

    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        role = check_login(username, password)

        if role:
            messagebox.showinfo("Success", f"Logged in as {role}")
            self.master.destroy()
            UserManagementWindow(role)
        else:
            messagebox.showerror("Error", "Invalid username or password")

# ------------------------------
# User Management Screen (Admin)
# ------------------------------
class UserManagementWindow:
    def __init__(self, role):
        self.window = tk.Tk()
        self.window.title("User Management" if role == "admin" else "POS System")
        self.window.geometry("400x350")

        if role == "admin":
            tk.Label(self.window, text="Add New User").pack(pady=5)

            self.username_entry = tk.Entry(self.window)
            self.username_entry.insert(0, "username")
            self.username_entry.pack()

            self.password_entry = tk.Entry(self.window, show="*")
            self.password_entry.insert(0, "password")
            self.password_entry.pack()

            self.role_entry = tk.Entry(self.window)
            self.role_entry.insert(0, "cashier or admin")
            self.role_entry.pack()

            self.add_btn = tk.Button(self.window, text="Add User", command=self.add_user)
            self.add_btn.pack(pady=5)

            tk.Label(self.window, text="All Users:").pack()
            self.user_list = tk.Listbox(self.window)
            self.user_list.pack(fill=tk.BOTH, expand=True)

            self.delete_btn = tk.Button(self.window, text="Delete Selected User", command=self.delete_user)
            self.delete_btn.pack(pady=5)

            # ✅ Add inventory button
            self.inventory_btn = tk.Button(self.window, text="Open Inventory", command=self.open_inventory)
            self.inventory_btn.pack(pady=5)

            self.load_users()
        else:
            tk.Label(self.window, text="Welcome to the POS System!").pack(pady=50)

    def add_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        role = self.role_entry.get()

        if role not in ['admin', 'cashier']:
            messagebox.showerror("Invalid Role", "Role must be 'admin' or 'cashier'")
            return

        try:
            add_user(username, password, role)
            messagebox.showinfo("Success", f"User '{username}' added")
            self.load_users()
        except:
            messagebox.showerror("Error", "Could not add user")

    def load_users(self):
        self.user_list.delete(0, tk.END)
        c.execute("SELECT username, role FROM users")
        for user in c.fetchall():
            self.user_list.insert(tk.END, f"{user[0]} - {user[1]}")

    def delete_user(self):
        selected = self.user_list.curselection()
        if selected:
            item = self.user_list.get(selected[0])
            username = item.split(" - ")[0]
            if username == "admin":
                messagebox.showerror("Error", "Cannot delete default admin")
                return
            confirm = messagebox.askyesno("Confirm", f"Delete user '{username}'?")
            if confirm:
                c.execute("DELETE FROM users WHERE username = ?", (username,))
                conn.commit()
                self.load_users()

    def open_inventory(self):
        self.window.destroy()
        InventoryWindow()

# ------------------------------
# Inventory Management
# ------------------------------
class InventoryWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Inventory Management")
        self.window.geometry("500x400")

        self.name_entry = tk.Entry(self.window)
        self.name_entry.insert(0, "Product Name")
        self.name_entry.pack()

        self.price_entry = tk.Entry(self.window)
        self.price_entry.insert(0, "Price")
        self.price_entry.pack()

        self.quantity_entry = tk.Entry(self.window)
        self.quantity_entry.insert(0, "Quantity")
        self.quantity_entry.pack()

        self.add_btn = tk.Button(self.window, text="Add / Update Product", command=self.add_product)
        self.add_btn.pack(pady=5)

        self.products_list = tk.Listbox(self.window)
        self.products_list.pack(fill=tk.BOTH, expand=True)
        self.products_list.bind('<Double-Button-1>', self.load_product)

        self.delete_btn = tk.Button(self.window, text="Delete Selected Product", command=self.delete_product)
        self.delete_btn.pack(pady=5)

        self.load_products()

    def add_product(self):
        name = self.name_entry.get()
        try:
            price = float(self.price_entry.get())
            quantity = int(self.quantity_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Price must be a number, Quantity must be an integer.")
            return

        c.execute("SELECT id FROM products WHERE name = ?", (name,))
        result = c.fetchone()
        if result:
            c.execute("UPDATE products SET price = ?, quantity = ? WHERE id = ?", (price, quantity, result[0]))
        else:
            c.execute("INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)", (name, price, quantity))
        conn.commit()
        self.load_products()

    def load_products(self):
        self.products_list.delete(0, tk.END)
        c.execute("SELECT name, price, quantity FROM products")
        for product in c.fetchall():
            self.products_list.insert(tk.END, f"{product[0]} | ${product[1]:.2f} | Qty: {product[2]}")

    def load_product(self, event):
        selected = self.products_list.curselection()
        if selected:
            item = self.products_list.get(selected[0])
            parts = item.split(" | ")
            name = parts[0]
            price = parts[1].replace("$", "")
            qty = parts[2].replace("Qty: ", "")
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, name)
            self.price_entry.delete(0, tk.END)
            self.price_entry.insert(0, price)
            self.quantity_entry.delete(0, tk.END)
            self.quantity_entry.insert(0, qty)

    def delete_product(self):
        selected = self.products_list.curselection()
        if selected:
            item = self.products_list.get(selected[0])
            name = item.split(" | ")[0]
            confirm = messagebox.askyesno("Confirm", f"Delete product '{name}'?")
            if confirm:
                c.execute("DELETE FROM products WHERE name = ?", (name,))
                conn.commit()
                self.load_products()

# ------------------------------
# Main App Entry
# ------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()
