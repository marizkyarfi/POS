import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

# Database setup
conn = sqlite3.connect("database.db")
c = conn.cursor()

# Create tables
c.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        quantity_sold INTEGER,
        total_price REAL,
        sale_date TEXT,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
''')
conn.commit()

# App setup
root = tk.Tk()
root.title("Simple POS System")
root.geometry("600x500")

# Tabs
notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

frame_add = ttk.Frame(notebook)
frame_sale = ttk.Frame(notebook)
frame_history = ttk.Frame(notebook)

notebook.add(frame_add, text="Add Product")
notebook.add(frame_sale, text="Make Sale")
notebook.add(frame_history, text="Sales History")

# === Add Product Tab ===
def add_product():
    name = entry_name.get()
    price = entry_price.get()
    qty = entry_qty.get()

    if not (name and price and qty):
        messagebox.showerror("Input Error", "All fields required")
        return

    try:
        price = float(price)
        qty = int(qty)
        c.execute("INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)", (name, price, qty))
        conn.commit()
        messagebox.showinfo("Success", "Product added")
        entry_name.delete(0, tk.END)
        entry_price.delete(0, tk.END)
        entry_qty.delete(0, tk.END)
        load_products()
    except ValueError:
        messagebox.showerror("Invalid Input", "Price must be number and quantity must be integer")

tk.Label(frame_add, text="Product Name").pack()
entry_name = tk.Entry(frame_add)
entry_name.pack()

tk.Label(frame_add, text="Price").pack()
entry_price = tk.Entry(frame_add)
entry_price.pack()

tk.Label(frame_add, text="Quantity").pack()
entry_qty = tk.Entry(frame_add)
entry_qty.pack()

tk.Button(frame_add, text="Add Product", command=add_product).pack(pady=10)

# === Make Sale Tab ===
tree = ttk.Treeview(frame_sale, columns=("ID", "Name", "Price", "Qty"), show="headings")
tree.heading("ID", text="ID")
tree.heading("Name", text="Name")
tree.heading("Price", text="Price")
tree.heading("Qty", text="Stock")
tree.pack(fill='both', expand=True)

def load_products():
    for row in tree.get_children():
        tree.delete(row)
    for row in c.execute("SELECT * FROM products"):
        tree.insert("", "end", values=row)

def make_sale():
    selected = tree.focus()
    if not selected:
        messagebox.showerror("Error", "No product selected")
        return

    item = tree.item(selected)['values']
    product_id, name, price, stock = item
    qty = entry_sale_qty.get()

    try:
        qty = int(qty)
        if qty <= 0 or qty > stock:
            raise ValueError
        total = price * qty
        c.execute("UPDATE products SET quantity = ? WHERE id = ?", (stock - qty, product_id))
        c.execute("INSERT INTO sales (product_id, quantity_sold, total_price, sale_date) VALUES (?, ?, ?, ?)",
                  (product_id, qty, total, datetime.now().isoformat()))
        conn.commit()
        load_products()
        entry_sale_qty.delete(0, tk.END)
        load_sales()
        messagebox.showinfo("Sale", f"Sold {qty} x {name} = ${total:.2f}")
    except:
        messagebox.showerror("Error", "Invalid quantity")

tk.Label(frame_sale, text="Quantity to Sell").pack()
entry_sale_qty = tk.Entry(frame_sale)
entry_sale_qty.pack()
tk.Button(frame_sale, text="Sell", command=make_sale).pack(pady=10)

# === Sales History Tab ===
sales_tree = ttk.Treeview(frame_history, columns=("ID", "Name", "Qty", "Total", "Date"), show="headings")
for col in ("ID", "Name", "Qty", "Total", "Date"):
    sales_tree.heading(col, text=col)
sales_tree.pack(fill='both', expand=True)

def load_sales():
    for row in sales_tree.get_children():
        sales_tree.delete(row)
    for row in c.execute('''
        SELECT sales.id, products.name, sales.quantity_sold, sales.total_price, sales.sale_date
        FROM sales
        JOIN products ON sales.product_id = products.id
        ORDER BY sales.sale_date DESC
    '''):
        sales_tree.insert("", "end", values=row)

# Initialize
load_products()
load_sales()

# Start App
root.mainloop()
