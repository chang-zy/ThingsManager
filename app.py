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
    total_mean = sum((item[3] / (today - datetime.strptime(item[2], '%Y-%m-%d').date()).days) if (
                                                                                                             today - datetime.strptime(
                                                                                                         item[2],
                                                                                                         '%Y-%m-%d').date()).days > 0 else 0
                     for item in items)

    return render_template("index.html", items=items, total_price=total_price, total_mean=total_mean)


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