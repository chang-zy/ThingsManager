from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)


def init_db():
    with sqlite3.connect("price_manager.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                bought_date DATE,
                price REAL
            )
        ''')
        conn.commit()


@app.route('/')
def index():
    with sqlite3.connect("price_manager.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, bought_date, price FROM items")
        items = cursor.fetchall()

    today = datetime.now().date()
    total_price = sum(item[3] for item in items)

    # Build a new list of items that includes the mean price per day
    items_with_mean = []
    for item in items:
        item_id, name, bought_date, price = item
        # Convert the bought_date string to a date object
        date_obj = datetime.strptime(bought_date, '%Y-%m-%d').date()
        # Calculate the number of days since the item was bought
        days_diff = (today - date_obj).days
        # Avoid division by zero: if no days have passed, set mean to 0.
        mean_price_per_day = price / days_diff if days_diff > 0 else 0
        items_with_mean.append((item_id, name, bought_date, price, mean_price_per_day))

    # Optionally, you can also calculate a total mean across all items:
    total_mean = sum(item[4] for item in items_with_mean)

    return render_template("index.html", items=items_with_mean, total_price=total_price, total_mean=total_mean)


@app.route('/add', methods=['POST'])
def add_item():
    name = request.form.get("name").strip()
    price = request.form.get("price").strip()
    bought_date = request.form.get("bought_date").strip()

    try:
        price = float(price)
        with sqlite3.connect("price_manager.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO items (name, bought_date, price) VALUES (?, ?, ?)", (name, bought_date, price))
            conn.commit()
    except ValueError:
        return "Invalid price", 400

    return redirect(url_for("index"))


@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    with sqlite3.connect("price_manager.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
    return redirect(url_for("index"))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)