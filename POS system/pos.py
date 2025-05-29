import sqlite3
from datetime import datetime

# Initialize DB
conn = sqlite3.connect('database.db')
c = conn.cursor()

# Create tables if not exist
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

# Functions
def add_product(name, price, quantity):
    c.execute("INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)", (name, price, quantity))
    conn.commit()
    print("✅ Product added.")

def view_products():
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    for p in products:
        print(p)

def make_sale(product_id, quantity):
    c.execute("SELECT price, quantity FROM products WHERE id = ?", (product_id,))
    result = c.fetchone()
    if not result:
        print("❌ Product not found.")
        return

    price, stock = result
    if stock < quantity:
        print("❌ Not enough stock.")
        return

    total = price * quantity
    new_quantity = stock - quantity

    c.execute("UPDATE products SET quantity = ? WHERE id = ?", (new_quantity, product_id))
    c.execute("INSERT INTO sales (product_id, quantity_sold, total_price, sale_date) VALUES (?, ?, ?, ?)",
              (product_id, quantity, total, datetime.now().isoformat()))
    conn.commit()
    print(f"✅ Sold {quantity} unit(s). Total: ${total:.2f}")

def view_sales():
    c.execute("SELECT sales.id, products.name, quantity_sold, total_price, sale_date FROM sales JOIN products ON sales.product_id = products.id")
    for sale in c.fetchall():
        print(sale)

# Example CLI menu
def menu():
    while True:
        print("\n=== POS SYSTEM ===")
        print("1. Add Product")
        print("2. View Products")
        print("3. Make Sale")
        print("4. View Sales History")
        print("5. Exit")

        choice = input("Select option: ")

        if choice == '1':
            name = input("Product name: ")
            price = float(input("Product price: "))
            quantity = int(input("Product quantity: "))
            add_product(name, price, quantity)
        elif choice == '2':
            view_products()
        elif choice == '3':
            product_id = int(input("Product ID to sell: "))
            quantity = int(input("Quantity: "))
            make_sale(product_id, quantity)
        elif choice == '4':
            view_sales()
        elif choice == '5':
            print("👋 Exiting...")
            break
        else:
            print("❌ Invalid choice.")

# Start the menu
if __name__ == '__main__':
    menu()
