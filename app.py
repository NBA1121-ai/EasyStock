from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inventory.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('in', 'out')),
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            date TEXT NOT NULL DEFAULT (date('now')),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
    ''')
    conn.commit()
    conn.close()

TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Учёт товаров</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f0f2f5; color: #333; padding: 20px; }
        h1 { text-align: center; margin-bottom: 20px; color: #1a1a2e; }
        h2 { margin: 20px 0 10px; color: #1a1a2e; }
        .container { max-width: 900px; margin: 0 auto; }
        .card { background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .form-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: end; }
        .form-group { display: flex; flex-direction: column; flex: 1; min-width: 120px; }
        .form-group label { font-size: 13px; margin-bottom: 4px; color: #555; }
        input, select { padding: 8px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
        input:focus, select:focus { outline: none; border-color: #4a90d9; }
        button { padding: 8px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; color: #fff; }
        .btn-in { background: #27ae60; }
        .btn-in:hover { background: #219a52; }
        .btn-out { background: #e74c3c; }
        .btn-out:hover { background: #c0392b; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; font-weight: 600; font-size: 13px; color: #555; }
        td { font-size: 14px; }
        .profit-pos { color: #27ae60; font-weight: 600; }
        .profit-neg { color: #e74c3c; font-weight: 600; }
        .badge-in { background: #d4edda; color: #155724; padding: 2px 8px; border-radius: 10px; font-size: 12px; }
        .badge-out { background: #f8d7da; color: #721c24; padding: 2px 8px; border-radius: 10px; font-size: 12px; }
        .summary { display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 10px; }
        .summary-item { background: #f8f9fa; padding: 12px 20px; border-radius: 6px; text-align: center; flex: 1; min-width: 150px; }
        .summary-item .num { font-size: 24px; font-weight: 700; color: #1a1a2e; }
        .summary-item .label { font-size: 12px; color: #777; margin-top: 4px; }
        .delete-btn { background: #aaa; padding: 4px 10px; font-size: 12px; }
        .delete-btn:hover { background: #888; }
        @media (max-width: 600px) {
            .form-row { flex-direction: column; }
            .form-group { min-width: 100%; }
        }
    </style>
</head>
<body>
<div class="container">
    <h1>Учёт товаров</h1>

    <div class="card">
        <h2>Добавить товар</h2>
        <form method="POST" action="/add_product" style="display:flex;gap:10px;margin-top:10px;">
            <input type="text" name="name" placeholder="Название товара" required style="flex:1;">
            <button type="submit" class="btn-in">Добавить</button>
        </form>
    </div>

    <div class="card">
        <h2>Приход / Расход</h2>
        <form method="POST" action="/add_transaction">
            <div class="form-row" style="margin-top:10px;">
                <div class="form-group">
                    <label>Товар</label>
                    <select name="product_id" required>
                        <option value="">Выберите...</option>
                        {% for p in products %}
                        <option value="{{ p.id }}">{{ p.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group">
                    <label>Тип</label>
                    <select name="type" required>
                        <option value="in">Приход</option>
                        <option value="out">Расход</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Кол-во</label>
                    <input type="number" name="quantity" step="0.01" min="0.01" required>
                </div>
                <div class="form-group">
                    <label>Цена (за ед.)</label>
                    <input type="number" name="price" step="0.01" min="0" required>
                </div>
                <div class="form-group">
                    <label>Дата</label>
                    <input type="date" name="date" value="{{ today }}">
                </div>
                <button type="submit" class="btn-in" style="align-self:end;">Записать</button>
            </div>
        </form>
    </div>

    {% if summary %}
    <div class="card">
        <h2>Сводка</h2>
        <div class="summary">
            <div class="summary-item">
                <div class="num">{{ summary.total_products }}</div>
                <div class="label">Товаров</div>
            </div>
            <div class="summary-item">
                <div class="num">{{ "%.2f"|format(summary.total_in) }}</div>
                <div class="label">Сумма прихода</div>
            </div>
            <div class="summary-item">
                <div class="num">{{ "%.2f"|format(summary.total_out) }}</div>
                <div class="label">Сумма расхода</div>
            </div>
            <div class="summary-item">
                <div class="num {{ 'profit-pos' if summary.profit >= 0 else 'profit-neg' }}">{{ "%.2f"|format(summary.profit) }}</div>
                <div class="label">Прибыль</div>
            </div>
        </div>
    </div>
    {% endif %}

    {% if inventory %}
    <div class="card">
        <h2>Остатки</h2>
        <table>
            <tr><th>Товар</th><th>Остаток</th><th>Сред. цена прихода</th><th>Сред. цена расхода</th><th>Прибыль</th></tr>
            {% for item in inventory %}
            <tr>
                <td>{{ item.name }}</td>
                <td>{{ "%.2f"|format(item.stock) }}</td>
                <td>{{ "%.2f"|format(item.avg_in_price) if item.avg_in_price else "—" }}</td>
                <td>{{ "%.2f"|format(item.avg_out_price) if item.avg_out_price else "—" }}</td>
                <td class="{{ 'profit-pos' if item.profit >= 0 else 'profit-neg' }}">{{ "%.2f"|format(item.profit) }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endif %}

    {% if transactions %}
    <div class="card">
        <h2>История операций</h2>
        <table>
            <tr><th>Дата</th><th>Товар</th><th>Тип</th><th>Кол-во</th><th>Цена</th><th>Сумма</th><th></th></tr>
            {% for t in transactions %}
            <tr>
                <td>{{ t.date }}</td>
                <td>{{ t.product_name }}</td>
                <td><span class="{{ 'badge-in' if t.type == 'in' else 'badge-out' }}">{{ 'Приход' if t.type == 'in' else 'Расход' }}</span></td>
                <td>{{ "%.2f"|format(t.quantity) }}</td>
                <td>{{ "%.2f"|format(t.price) }}</td>
                <td>{{ "%.2f"|format(t.quantity * t.price) }}</td>
                <td><form method="POST" action="/delete_transaction/{{ t.id }}" style="margin:0;" onsubmit="return confirm('Удалить?')"><button type="submit" class="delete-btn">X</button></form></td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endif %}
</div>
</body>
</html>
'''

@app.route('/')
def index():
    conn = get_db()
    products = conn.execute('SELECT * FROM products ORDER BY name').fetchall()

    from datetime import date
    today = date.today().isoformat()

    # Inventory with profit
    inventory = conn.execute('''
        SELECT
            p.name,
            COALESCE(SUM(CASE WHEN t.type='in' THEN t.quantity ELSE 0 END), 0)
              - COALESCE(SUM(CASE WHEN t.type='out' THEN t.quantity ELSE 0 END), 0) AS stock,
            CASE WHEN SUM(CASE WHEN t.type='in' THEN t.quantity ELSE 0 END) > 0
                 THEN SUM(CASE WHEN t.type='in' THEN t.quantity * t.price ELSE 0 END)
                      / SUM(CASE WHEN t.type='in' THEN t.quantity ELSE 0 END)
                 ELSE NULL END AS avg_in_price,
            CASE WHEN SUM(CASE WHEN t.type='out' THEN t.quantity ELSE 0 END) > 0
                 THEN SUM(CASE WHEN t.type='out' THEN t.quantity * t.price ELSE 0 END)
                      / SUM(CASE WHEN t.type='out' THEN t.quantity ELSE 0 END)
                 ELSE NULL END AS avg_out_price,
            COALESCE(SUM(CASE WHEN t.type='out' THEN t.quantity * t.price ELSE 0 END), 0)
              - COALESCE(SUM(CASE WHEN t.type='in' THEN t.quantity * t.price ELSE 0 END), 0) AS profit
        FROM products p
        LEFT JOIN transactions t ON p.id = t.product_id
        GROUP BY p.id
        ORDER BY p.name
    ''').fetchall()

    # Summary
    row = conn.execute('''
        SELECT
            COUNT(DISTINCT product_id) AS total_products,
            COALESCE(SUM(CASE WHEN type='in' THEN quantity * price ELSE 0 END), 0) AS total_in,
            COALESCE(SUM(CASE WHEN type='out' THEN quantity * price ELSE 0 END), 0) AS total_out
        FROM transactions
    ''').fetchone()
    summary = {
        'total_products': len(products),
        'total_in': row['total_in'],
        'total_out': row['total_out'],
        'profit': row['total_out'] - row['total_in']
    }

    # Recent transactions
    transactions = conn.execute('''
        SELECT t.*, p.name AS product_name
        FROM transactions t
        JOIN products p ON t.product_id = p.id
        ORDER BY t.date DESC, t.id DESC
        LIMIT 100
    ''').fetchall()

    conn.close()
    return render_template_string(TEMPLATE, products=products, inventory=inventory,
                                  transactions=transactions, summary=summary, today=today)

@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form['name'].strip()
    if name:
        conn = get_db()
        try:
            conn.execute('INSERT INTO products (name) VALUES (?)', (name,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        conn.close()
    return redirect(url_for('index'))

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    product_id = request.form['product_id']
    tx_type = request.form['type']
    quantity = float(request.form['quantity'])
    price = float(request.form['price'])
    date = request.form.get('date', '')
    conn = get_db()
    if date:
        conn.execute('INSERT INTO transactions (product_id, type, quantity, price, date) VALUES (?, ?, ?, ?, ?)',
                     (product_id, tx_type, quantity, price, date))
    else:
        conn.execute('INSERT INTO transactions (product_id, type, quantity, price) VALUES (?, ?, ?, ?)',
                     (product_id, tx_type, quantity, price))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_transaction/<int:tx_id>', methods=['POST'])
def delete_transaction(tx_id):
    conn = get_db()
    conn.execute('DELETE FROM transactions WHERE id = ?', (tx_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
