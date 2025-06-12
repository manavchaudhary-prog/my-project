from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    expiry_date TEXT,
                    unit TEXT
                )''')
    # Try adding unit column if it doesn't exist
    try:
        c.execute("ALTER TABLE items ADD COLUMN unit TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

init_db()

# --- Routes ---
@app.route('/', methods=['GET', 'POST'])
def index():
    search_query = request.args.get('search', '').strip()

    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()

    if search_query:
        c.execute("SELECT * FROM items WHERE name LIKE ?", ('%' + search_query + '%',))
    else:
        c.execute("SELECT * FROM items")
        
    items = c.fetchall()

    total_value = sum(item[2] * item[3] for item in items)

    low_stock_threshold = 5
    low_stock_items = [item for item in items if item[2] < low_stock_threshold]

    today = datetime.today().date()
    expiring_soon = [item for item in items if item[4] and datetime.strptime(item[4], '%Y-%m-%d').date() <= today + timedelta(days=7)]

    conn.close()
    
    return render_template('index.html', items=items, total_value=total_value, low_stock_items=low_stock_items, expiring_soon=expiring_soon)

@app.route('/add', methods=['POST'])
def add_item():
    name = request.form['name']
    quantity = int(request.form['quantity'])
    price = float(request.form['price'])
    expiry_date = request.form['expiry_date']
    unit = request.form['unit']
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("INSERT INTO items (name, quantity, price, expiry_date, unit) VALUES (?, ?, ?, ?, ?)",
              (name, quantity, price, expiry_date, unit))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:item_id>')
def delete_item(item_id):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:item_id>')
def edit_item(item_id):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM items WHERE id=?", (item_id,))
    item = c.fetchone()
    conn.close()
    return render_template('edit.html', item=item)

@app.route('/update/<int:item_id>', methods=['POST'])
def update_item(item_id):
    name = request.form['name']
    quantity = int(request.form['quantity'])
    price = float(request.form['price'])
    expiry_date = request.form['expiry_date']
    unit = request.form['unit']
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("UPDATE items SET name=?, quantity=?, price=?, expiry_date=?, unit=? WHERE id=?",
              (name, quantity, price, expiry_date, unit, item_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/sell/<int:item_id>')
def sell_item(item_id):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT quantity FROM items WHERE id=?", (item_id,))
    result = c.fetchone()
    if result and result[0] > 0:
        c.execute("UPDATE items SET quantity = quantity - 1 WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/report')
def report():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM items WHERE quantity < 5")
    low_stock = c.fetchall()
    c.execute("SELECT * FROM items")
    all_items = c.fetchall()
    conn.close()
    today = datetime.today().date()
    expiring_soon = [item for item in all_items if item[4] and datetime.strptime(item[4], '%Y-%m-%d').date() <= today]
    return render_template('report.html', low_stock=low_stock, expiring_soon=expiring_soon)

if __name__ == '__main__':
    app.run(debug=True)

