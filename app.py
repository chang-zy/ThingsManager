from flask import Flask, render_template, request, redirect, url_for, Response
import sqlite3
from datetime import datetime, timedelta
import io
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

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

    # 计算每个物品今天的均价（若购买当天则为 0）
    items_with_mean = []
    for item in items:
        item_id, name, bought_date, price = item
        try:
            date_obj = datetime.strptime(bought_date, '%Y-%m-%d').date()
        except ValueError:
            continue
        days_diff = (today - date_obj).days
        mean_price_per_day = price / days_diff if days_diff > 0 else 0
        items_with_mean.append((item_id, name, bought_date, price, mean_price_per_day))

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
            cursor.execute("INSERT INTO items (name, bought_date, price) VALUES (?, ?, ?)",
                           (name, bought_date, price))
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


@app.route('/plot')
def plot():
    """
    绘制历史均价曲线和未来6个月预测均价曲线。
    对于每一天 d：
      - 对于每个物品，若 d > bought_date，则贡献 price/((d - bought_date).days)
      - 否则贡献为 0
    历史部分：从最早购买日期（若无物品，则默认为今天前30天）到今天；
    预测部分：从明天到未来6个月结束。
    """
    with sqlite3.connect("price_manager.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT bought_date, price FROM items")
        rows = cursor.fetchall()

    # 转换数据格式
    items = []
    for row in rows:
        try:
            bd = datetime.strptime(row[0], '%Y-%m-%d').date()
            items.append((bd, row[1]))
        except Exception:
            continue

    today = datetime.now().date()
    # 确定历史部分起始日期
    if items:
        start_date = min(bd for (bd, _) in items)
    else:
        start_date = today - timedelta(days=30)
    end_date = today + timedelta(days=180)  # 未来6个月

    # 构造历史日期列表：从 start_date 到今天（包括今天）
    past_dates = []
    past_means = []
    d = start_date
    while d <= today:
        daily_total = 0.0
        for (bought_date, price) in items:
            delta = (d - bought_date).days
            if delta > 0:
                daily_total += price / delta
        past_dates.append(d)
        past_means.append(daily_total)
        d += timedelta(days=1)

    # 构造未来日期列表：从明天到 end_date
    future_dates = []
    future_means = []
    d = today + timedelta(days=1)
    while d <= end_date:
        daily_total = 0.0
        for (bought_date, price) in items:
            delta = (d - bought_date).days
            if delta > 0:
                daily_total += price / delta
        future_dates.append(d)
        future_means.append(daily_total)
        d += timedelta(days=1)

    # 设置y轴的对数刻度，以增强低值的可视化效果
    fig, ax = plt.subplots(figsize=(10, 5))
    if past_dates:
        ax.plot(past_dates, past_means, color='blue', label='Historical Mean Price/Day')
    if future_dates:
        ax.plot(future_dates, future_means, color='red', label='Predicted Future Mean Price/Day')

    # 画今天的虚线
    ax.axvline(today, color='green', linestyle='--', label='Today')

    # 设置标题和标签
    ax.set_title("Historical & Future Predicted Mean Price/Day")
    ax.set_xlabel("Date")
    ax.set_ylabel("Total Mean Price/Day")

    # 使用对数刻度
    ax.set_yscale('log')

    ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    ax.legend()

    # 保存图形到内存并返回 PNG 图片
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return Response(buf.getvalue(), mimetype='image/png')



if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=80, debug=True)
