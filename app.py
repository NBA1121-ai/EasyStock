from flask import Flask, request, redirect, url_for, render_template_string, jsonify
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
<title>EasyStock</title>
<style>
:root {
  --bg: #0e1117;
  --bg2: #161b27;
  --bg3: #1e2535;
  --bg4: #252d3f;
  --border: #2a3347;
  --border2: #374056;
  --text: #e8ecf4;
  --text2: #8b95b0;
  --text3: #5a6480;
  --accent: #4f8ef7;
  --accent2: #3b6fd4;
  --green: #2ecc8a;
  --green2: #1a7a52;
  --red: #f74f4f;
  --red2: #8a1a1a;
  --yellow: #f7c44f;
  --purple: #9b6dff;
  --radius: 10px;
  --radius2: 6px;
  --shadow: 0 4px 24px rgba(0,0,0,0.4);
  --mono: 'Segoe UI', monospace;
}

* { margin:0; padding:0; box-sizing:border-box; }

body {
  font-family: 'Segoe UI', sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  display: flex;
  font-size: 14px;
}

/* SIDEBAR */
.sidebar {
  width: 220px;
  min-height: 100vh;
  background: var(--bg2);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0; left: 0; bottom: 0;
  z-index: 100;
}
.logo {
  padding: 20px 18px 16px;
  border-bottom: 1px solid var(--border);
}
.logo-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--accent);
  letter-spacing: 0.05em;
}
.logo-sub {
  font-size: 10px;
  color: var(--text3);
  margin-top: 2px;
}
.nav { padding: 12px 0; flex: 1; overflow-y: auto; }
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 18px;
  cursor: pointer;
  color: var(--text2);
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s;
  border-left: 2px solid transparent;
  text-decoration: none;
}
.nav-item:hover { background: var(--bg3); color: var(--text); }
.nav-item.active { background: var(--bg3); color: var(--accent); border-left-color: var(--accent); }
.nav-item .icon { font-size: 15px; width: 18px; text-align: center; }

/* MAIN */
.main {
  margin-left: 220px;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
.topbar {
  height: 56px;
  background: var(--bg2);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 24px;
  position: sticky; top: 0; z-index: 50;
}
.topbar-title { font-size: 16px; font-weight: 700; }

.page { padding: 24px; display: none; }
.page.active { display: block; }

/* STAT CARDS */
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px;
  position: relative;
  overflow: hidden;
}
.stat-card::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 2px;
}
.stat-card.accent::before { background: var(--accent); }
.stat-card.green::before { background: var(--green); }
.stat-card.red::before { background: var(--red); }
.stat-card.yellow::before { background: var(--yellow); }
.stat-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text3); }
.stat-value { font-size: 26px; font-weight: 700; margin-top: 6px; font-family: var(--mono); }
.stat-sub { font-size: 11px; color: var(--text3); margin-top: 4px; }
.stat-icon { position: absolute; right: 16px; top: 16px; font-size: 28px; opacity: 0.15; }

/* CARD */
.card {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 20px;
}
.card-header {
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
}
.card-title { font-size: 13px; font-weight: 700; }
.card-body { padding: 18px; }

/* TABLE */
.tbl { width: 100%; border-collapse: collapse; }
.tbl th {
  text-align: left; padding: 10px 14px;
  font-size: 10px; font-weight: 700; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--text3);
  background: var(--bg3);
  border-bottom: 1px solid var(--border);
}
.tbl td {
  padding: 11px 14px; font-size: 12px;
  border-bottom: 1px solid var(--border);
  color: var(--text);
}
.tbl tr:last-child td { border-bottom: none; }
.tbl tr:hover td { background: var(--bg3); }
.tbl .num { text-align: right; font-family: var(--mono); }

/* BADGE */
.badge {
  display: inline-flex; align-items: center;
  padding: 2px 8px; border-radius: 20px;
  font-size: 10px; font-weight: 700;
}
.badge-in { background: rgba(46,204,138,0.15); color: var(--green); }
.badge-out { background: rgba(247,79,79,0.15); color: var(--red); }

/* BUTTONS */
.btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 14px; border-radius: var(--radius2);
  font-size: 12px; font-weight: 600; cursor: pointer;
  border: none; font-family: inherit; transition: all 0.15s;
  color: #fff;
}
.btn-primary { background: var(--accent); }
.btn-primary:hover { background: var(--accent2); }
.btn-success { background: var(--green2); color: var(--green); border: 1px solid var(--green2); }
.btn-success:hover { background: var(--green); color: #0e1117; }
.btn-danger { background: var(--red2); color: var(--red); border: 1px solid var(--red2); }
.btn-danger:hover { background: var(--red); color: #fff; }
.btn-secondary { background: var(--bg3); color: var(--text); border: 1px solid var(--border2); }
.btn-secondary:hover { background: var(--bg4); }
.btn-sm { padding: 5px 10px; font-size: 11px; }

/* FORM */
.form-group { margin-bottom: 14px; }
.form-label { display: block; font-size: 11px; font-weight: 600; color: var(--text2); margin-bottom: 5px; }
.form-control {
  width: 100%; padding: 8px 12px;
  background: var(--bg3); border: 1px solid var(--border2);
  border-radius: var(--radius2); color: var(--text);
  font-family: inherit; font-size: 13px;
  transition: border-color 0.15s;
  outline: none;
}
.form-control:focus { border-color: var(--accent); }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-row3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }

/* MODAL */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.7);
  z-index: 1000; display: none;
  align-items: center; justify-content: center;
}
.modal-overlay.open { display: flex; }
.modal {
  background: var(--bg2); border: 1px solid var(--border2);
  border-radius: var(--radius); width: 500px; max-width: 95vw;
  max-height: 90vh; overflow-y: auto;
  box-shadow: var(--shadow);
}
.modal-header {
  padding: 18px 22px; border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
}
.modal-title { font-size: 15px; font-weight: 700; }
.modal-close { cursor: pointer; color: var(--text3); font-size: 18px; }
.modal-close:hover { color: var(--text); }
.modal-body { padding: 22px; }
.modal-footer {
  padding: 14px 22px; border-top: 1px solid var(--border);
  display: flex; justify-content: flex-end; gap: 8px;
}

/* NOTIFICATION */
.notif {
  position: fixed; top: 20px; right: 20px; z-index: 9999;
  background: var(--bg2); border: 1px solid var(--border2);
  border-radius: var(--radius); padding: 12px 18px;
  box-shadow: var(--shadow); font-size: 13px;
  transform: translateX(120%); transition: transform 0.3s;
  display: flex; align-items: center; gap: 10px;
}
.notif.show { transform: translateX(0); }
.notif.success { border-left: 3px solid var(--green); }
.notif.error { border-left: 3px solid var(--red); }

.profit-pos { color: var(--green); font-weight: 600; }
.profit-neg { color: var(--red); font-weight: 600; }

/* SCROLLBAR */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }

@media (max-width: 768px) {
  .sidebar { width: 60px; }
  .sidebar .logo-title, .sidebar .logo-sub, .sidebar .nav-item span:not(.icon) { display: none; }
  .main { margin-left: 60px; }
  .stats-grid { grid-template-columns: 1fr 1fr; }
  .nav-item { padding: 11px 0; justify-content: center; }
}
</style>
</head>
<body>

<!-- SIDEBAR -->
<aside class="sidebar">
  <div class="logo">
    <div class="logo-title">EasyStock</div>
    <div class="logo-sub">Учёт товаров</div>
  </div>
  <nav class="nav">
    <a class="nav-item active" data-page="dashboard" onclick="showPage('dashboard')">
      <span class="icon">📊</span> <span>Дашборд</span>
    </a>
    <a class="nav-item" data-page="income" onclick="showPage('income')">
      <span class="icon">📥</span> <span>Приход</span>
    </a>
    <a class="nav-item" data-page="expense" onclick="showPage('expense')">
      <span class="icon">📤</span> <span>Расход</span>
    </a>
    <a class="nav-item" data-page="stock" onclick="showPage('stock')">
      <span class="icon">📦</span> <span>Остатки</span>
    </a>
    <a class="nav-item" data-page="history" onclick="showPage('history')">
      <span class="icon">📋</span> <span>История</span>
    </a>
    <a class="nav-item" data-page="products" onclick="showPage('products')">
      <span class="icon">📁</span> <span>Товары</span>
    </a>
  </nav>
</aside>

<!-- MAIN -->
<main class="main">
  <div class="topbar">
    <div class="topbar-title" id="pageTitle">Дашборд</div>
  </div>

  <!-- DASHBOARD -->
  <div class="page active" id="page-dashboard">
    <div class="stats-grid">
      <div class="stat-card accent">
        <div class="stat-icon">📦</div>
        <div class="stat-label">Товаров</div>
        <div class="stat-value">{{ summary.total_products }}</div>
        <div class="stat-sub">наименований</div>
      </div>
      <div class="stat-card green">
        <div class="stat-icon">📥</div>
        <div class="stat-label">Сумма прихода</div>
        <div class="stat-value">{{ "{:,.0f}".format(summary.total_in).replace(",", " ") }}</div>
        <div class="stat-sub">сом</div>
      </div>
      <div class="stat-card red">
        <div class="stat-icon">📤</div>
        <div class="stat-label">Сумма расхода</div>
        <div class="stat-value">{{ "{:,.0f}".format(summary.total_out).replace(",", " ") }}</div>
        <div class="stat-sub">сом</div>
      </div>
      <div class="stat-card yellow">
        <div class="stat-icon">💰</div>
        <div class="stat-label">Прибыль</div>
        <div class="stat-value {{ 'profit-pos' if summary.profit >= 0 else 'profit-neg' }}">{{ "{:,.0f}".format(summary.profit).replace(",", " ") }}</div>
        <div class="stat-sub">сом</div>
      </div>
    </div>

    <!-- Quick stock table -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">📦 Остатки товаров</div>
      </div>
      <table class="tbl">
        <thead><tr>
          <th>Товар</th><th class="num">Остаток</th>
          <th class="num">Ср. цена прихода</th><th class="num">Ср. цена расхода</th>
          <th class="num">Прибыль</th>
        </tr></thead>
        <tbody>
          {% for item in inventory %}
          <tr>
            <td>{{ item.name }}</td>
            <td class="num">{{ "%.2f"|format(item.stock) }}</td>
            <td class="num">{{ "%.2f"|format(item.avg_in_price) if item.avg_in_price else "—" }}</td>
            <td class="num">{{ "%.2f"|format(item.avg_out_price) if item.avg_out_price else "—" }}</td>
            <td class="num {{ 'profit-pos' if item.profit >= 0 else 'profit-neg' }}">{{ "%.2f"|format(item.profit) }}</td>
          </tr>
          {% endfor %}
          {% if not inventory %}
          <tr><td colspan="5" style="text-align:center;color:var(--text3);padding:32px;">Нет товаров</td></tr>
          {% endif %}
        </tbody>
      </table>
    </div>
  </div>

  <!-- INCOME PAGE -->
  <div class="page" id="page-income">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
      <div style="font-size:12px;color:var(--text3);">Приход товаров</div>
      <button class="btn btn-primary" onclick="openModal('incomeModal')">+ Новый приход</button>
    </div>
    <div class="card">
      <table class="tbl">
        <thead><tr>
          <th>Дата</th><th>Товар</th><th class="num">Кол-во</th>
          <th class="num">Цена</th><th class="num">Сумма</th><th></th>
        </tr></thead>
        <tbody>
          {% for t in transactions if t.type == 'in' %}
          <tr>
            <td>{{ t.date }}</td>
            <td>{{ t.product_name }}</td>
            <td class="num">{{ "%.2f"|format(t.quantity) }}</td>
            <td class="num">{{ "%.2f"|format(t.price) }}</td>
            <td class="num">{{ "%.2f"|format(t.quantity * t.price) }}</td>
            <td>
              <form method="POST" action="/delete_transaction/{{ t.id }}" onsubmit="return confirm('Удалить?')">
                <button type="submit" class="btn btn-danger btn-sm">✕</button>
              </form>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>

  <!-- EXPENSE PAGE -->
  <div class="page" id="page-expense">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
      <div style="font-size:12px;color:var(--text3);">Расход товаров</div>
      <button class="btn btn-primary" onclick="openModal('expenseModal')">+ Новый расход</button>
    </div>
    <div class="card">
      <table class="tbl">
        <thead><tr>
          <th>Дата</th><th>Товар</th><th class="num">Кол-во</th>
          <th class="num">Цена</th><th class="num">Сумма</th><th></th>
        </tr></thead>
        <tbody>
          {% for t in transactions if t.type == 'out' %}
          <tr>
            <td>{{ t.date }}</td>
            <td>{{ t.product_name }}</td>
            <td class="num">{{ "%.2f"|format(t.quantity) }}</td>
            <td class="num">{{ "%.2f"|format(t.price) }}</td>
            <td class="num">{{ "%.2f"|format(t.quantity * t.price) }}</td>
            <td>
              <form method="POST" action="/delete_transaction/{{ t.id }}" onsubmit="return confirm('Удалить?')">
                <button type="submit" class="btn btn-danger btn-sm">✕</button>
              </form>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>

  <!-- STOCK PAGE -->
  <div class="page" id="page-stock">
    <div style="margin-bottom:20px;">
      <div style="font-size:12px;color:var(--text3);">Текущие остатки на складе</div>
    </div>
    <div class="card">
      <table class="tbl">
        <thead><tr>
          <th>Товар</th><th class="num">Остаток</th>
          <th class="num">Ср. цена прихода</th><th class="num">Ср. цена расхода</th>
          <th class="num">Сумма прихода</th><th class="num">Сумма расхода</th>
          <th class="num">Прибыль</th>
        </tr></thead>
        <tbody>
          {% for item in inventory %}
          <tr>
            <td>{{ item.name }}</td>
            <td class="num">{{ "%.2f"|format(item.stock) }}</td>
            <td class="num">{{ "%.2f"|format(item.avg_in_price) if item.avg_in_price else "—" }}</td>
            <td class="num">{{ "%.2f"|format(item.avg_out_price) if item.avg_out_price else "—" }}</td>
            <td class="num">{{ "%.2f"|format(item.total_in) }}</td>
            <td class="num">{{ "%.2f"|format(item.total_out) }}</td>
            <td class="num {{ 'profit-pos' if item.profit >= 0 else 'profit-neg' }}">{{ "%.2f"|format(item.profit) }}</td>
          </tr>
          {% endfor %}
          {% if not inventory %}
          <tr><td colspan="7" style="text-align:center;color:var(--text3);padding:32px;">Нет данных</td></tr>
          {% endif %}
        </tbody>
      </table>
    </div>
  </div>

  <!-- HISTORY PAGE -->
  <div class="page" id="page-history">
    <div style="margin-bottom:20px;">
      <div style="font-size:12px;color:var(--text3);">Все операции (последние 100)</div>
    </div>
    <div class="card">
      <table class="tbl">
        <thead><tr>
          <th>Дата</th><th>Товар</th><th>Тип</th>
          <th class="num">Кол-во</th><th class="num">Цена</th><th class="num">Сумма</th><th></th>
        </tr></thead>
        <tbody>
          {% for t in transactions %}
          <tr>
            <td>{{ t.date }}</td>
            <td>{{ t.product_name }}</td>
            <td><span class="badge {{ 'badge-in' if t.type == 'in' else 'badge-out' }}">{{ 'Приход' if t.type == 'in' else 'Расход' }}</span></td>
            <td class="num">{{ "%.2f"|format(t.quantity) }}</td>
            <td class="num">{{ "%.2f"|format(t.price) }}</td>
            <td class="num">{{ "%.2f"|format(t.quantity * t.price) }}</td>
            <td>
              <form method="POST" action="/delete_transaction/{{ t.id }}" onsubmit="return confirm('Удалить?')">
                <button type="submit" class="btn btn-danger btn-sm">✕</button>
              </form>
            </td>
          </tr>
          {% endfor %}
          {% if not transactions %}
          <tr><td colspan="7" style="text-align:center;color:var(--text3);padding:32px;">Нет операций</td></tr>
          {% endif %}
        </tbody>
      </table>
    </div>
  </div>

  <!-- PRODUCTS PAGE -->
  <div class="page" id="page-products">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
      <div style="font-size:12px;color:var(--text3);">Справочник товаров</div>
      <button class="btn btn-primary" onclick="openModal('productModal')">+ Добавить товар</button>
    </div>
    <div class="card">
      <table class="tbl">
        <thead><tr><th>Название</th><th>Действия</th></tr></thead>
        <tbody>
          {% for p in products %}
          <tr>
            <td>{{ p.name }}</td>
            <td>
              <form method="POST" action="/delete_product/{{ p.id }}" onsubmit="return confirm('Удалить товар и все его операции?')">
                <button type="submit" class="btn btn-danger btn-sm">✕ Удалить</button>
              </form>
            </td>
          </tr>
          {% endfor %}
          {% if not products %}
          <tr><td colspan="2" style="text-align:center;color:var(--text3);padding:32px;">Нет товаров</td></tr>
          {% endif %}
        </tbody>
      </table>
    </div>
  </div>
</main>

<!-- INCOME MODAL -->
<div class="modal-overlay" id="incomeModal">
  <div class="modal">
    <div class="modal-header">
      <div class="modal-title">📥 Новый приход</div>
      <span class="modal-close" onclick="closeModal('incomeModal')">✕</span>
    </div>
    <form method="POST" action="/add_transaction">
      <input type="hidden" name="type" value="in">
      <div class="modal-body">
        <div class="form-group">
          <label class="form-label">Товар</label>
          <select class="form-control" name="product_id" required>
            <option value="">Выберите...</option>
            {% for p in products %}
            <option value="{{ p.id }}">{{ p.name }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Количество</label>
            <input class="form-control" type="number" name="quantity" step="0.01" min="0.01" required>
          </div>
          <div class="form-group">
            <label class="form-label">Цена (за ед.)</label>
            <input class="form-control" type="number" name="price" step="0.01" min="0" required>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Дата</label>
          <input class="form-control" type="date" name="date" value="{{ today }}">
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" onclick="closeModal('incomeModal')">Отмена</button>
        <button type="submit" class="btn btn-success">✔ Записать приход</button>
      </div>
    </form>
  </div>
</div>

<!-- EXPENSE MODAL -->
<div class="modal-overlay" id="expenseModal">
  <div class="modal">
    <div class="modal-header">
      <div class="modal-title">📤 Новый расход</div>
      <span class="modal-close" onclick="closeModal('expenseModal')">✕</span>
    </div>
    <form method="POST" action="/add_transaction">
      <input type="hidden" name="type" value="out">
      <div class="modal-body">
        <div class="form-group">
          <label class="form-label">Товар</label>
          <select class="form-control" name="product_id" required>
            <option value="">Выберите...</option>
            {% for p in products %}
            <option value="{{ p.id }}">{{ p.name }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Количество</label>
            <input class="form-control" type="number" name="quantity" step="0.01" min="0.01" required>
          </div>
          <div class="form-group">
            <label class="form-label">Цена (за ед.)</label>
            <input class="form-control" type="number" name="price" step="0.01" min="0" required>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Дата</label>
          <input class="form-control" type="date" name="date" value="{{ today }}">
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" onclick="closeModal('expenseModal')">Отмена</button>
        <button type="submit" class="btn btn-success">✔ Записать расход</button>
      </div>
    </form>
  </div>
</div>

<!-- PRODUCT MODAL -->
<div class="modal-overlay" id="productModal">
  <div class="modal" style="width:400px;">
    <div class="modal-header">
      <div class="modal-title">📁 Новый товар</div>
      <span class="modal-close" onclick="closeModal('productModal')">✕</span>
    </div>
    <form method="POST" action="/add_product">
      <div class="modal-body">
        <div class="form-group">
          <label class="form-label">Название товара</label>
          <input class="form-control" type="text" name="name" placeholder="Введите название" required>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" onclick="closeModal('productModal')">Отмена</button>
        <button type="submit" class="btn btn-primary">+ Добавить</button>
      </div>
    </form>
  </div>
</div>

<!-- NOTIFICATION -->
<div class="notif" id="notif"></div>

<script>
const pageTitles = {
  dashboard: 'Дашборд',
  income: 'Приход',
  expense: 'Расход',
  stock: 'Остатки',
  history: 'История операций',
  products: 'Товары'
};

function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');
  document.querySelector('[data-page="' + name + '"]').classList.add('active');
  document.getElementById('pageTitle').textContent = pageTitles[name] || name;
}

function openModal(id) {
  document.getElementById(id).classList.add('open');
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}

// Close modal on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', function(e) {
    if (e.target === this) this.classList.remove('open');
  });
});

// Close modal on Escape
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
  }
});
</script>
</body>
</html>
'''

@app.route('/')
def index():
    conn = get_db()
    products = conn.execute('SELECT * FROM products ORDER BY name').fetchall()

    from datetime import date
    today = date.today().isoformat()

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
            COALESCE(SUM(CASE WHEN t.type='in' THEN t.quantity * t.price ELSE 0 END), 0) AS total_in,
            COALESCE(SUM(CASE WHEN t.type='out' THEN t.quantity * t.price ELSE 0 END), 0) AS total_out,
            COALESCE(SUM(CASE WHEN t.type='out' THEN t.quantity * t.price ELSE 0 END), 0)
              - COALESCE(SUM(CASE WHEN t.type='in' THEN t.quantity * t.price ELSE 0 END), 0) AS profit
        FROM products p
        LEFT JOIN transactions t ON p.id = t.product_id
        GROUP BY p.id
        ORDER BY p.name
    ''').fetchall()

    row = conn.execute('''
        SELECT
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

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    conn = get_db()
    conn.execute('DELETE FROM transactions WHERE product_id = ?', (product_id,))
    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
